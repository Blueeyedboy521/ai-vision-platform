# -*- coding: utf-8 -*-
"""
推送处理线程池

通过 Redis Stream 消费通知事件，调用 notification_service.dispatch_event
"""

import json
import threading
import os
import socket
from typing import List, Optional

import redis

from common.logging import logger
from common.redis.client import RedisClient
from common.redis.channels import RedisKeys
from config.settings import settings


class NotificationWorkerPool:
    def __init__(self):
        self.workers: List[threading.Thread] = []
        self.running = False
        self.redis_client: Optional[redis.Redis] = None
        self._consumer_group = "notification_workers"
        self._instance_id = f"{socket.gethostname()}:{os.getpid()}"

    def start(self, num_workers: int = 2) -> None:
        if self.running:
            return
        self.running = True

        # 创建独立的同步 Redis 客户端（避免与其它线程池共享同一连接后被 close）
        wrapper = RedisClient(
            url=settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )
        try:
            wrapper.connect_sync()
        except Exception as e:
            logger.error(f"推送线程池初始化 Redis 连接失败: {e}")
            self.running = False
            return
        self.redis_client = wrapper.sync_client

        # ensure consumer group exists
        try:
            self.redis_client.xgroup_create(
                RedisKeys.NOTIFICATION_EVENTS_STREAM,
                self._consumer_group,
                # 只消费 group 创建后的新消息，避免历史消息干扰
                id="$",
                mkstream=True,
            )
        except Exception as e:
            # BUSYGROUP is ok
            if "BUSYGROUP" not in str(e):
                logger.error(f"创建通知事件消费者组失败: {e}")

        for i in range(num_workers):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"NotifyWorker-{i}",
                daemon=True,
            )
            t.start()
            self.workers.append(t)

        logger.info(f"推送线程池已启动: {num_workers} 个 Worker")

    def stop(self, timeout: float = 5.0) -> None:
        if not self.running:
            return
        self.running = False
        for t in self.workers:
            t.join(timeout=timeout)
        self.workers.clear()
        try:
            if self.redis_client:
                self.redis_client.close()
        finally:
            self.redis_client = None

    def _worker_loop(self) -> None:
        name = threading.current_thread().name
        logger.info(f"{name} 已启动")
        from app.services.notification_service import dispatch_event

        # consumername 需跨进程唯一，避免多实例/多机重名导致消费异常
        consumer_name = f"{self._instance_id}:{name}"
        while self.running:
            try:
                res = self.redis_client.xreadgroup(
                    groupname=self._consumer_group,
                    consumername=consumer_name,
                    streams={RedisKeys.NOTIFICATION_EVENTS_STREAM: ">"},
                    count=1,
                    block=1000,  # 最多阻塞 1000ms 等待新消息；超时后返回空，再进入下一轮循环检查 self.running
                )
                logger.info(f"res: {res}")
                if not res:
                    continue

                # res: [(stream, [(msg_id, {"data": b"..."}), ...])]
                _stream, messages = res[0]
                for msg_id, fields in messages:
                    raw = fields.get("data") if isinstance(fields, dict) else None
                    logger.info(f"msg_id: {msg_id}, raw: {raw}")
                    if raw is None:
                        # ack malformed
                        self.redis_client.xack(
                            RedisKeys.NOTIFICATION_EVENTS_STREAM,
                            self._consumer_group,
                            msg_id,
                        )
                        continue
                    if isinstance(raw, (bytes, bytearray)):
                        raw = raw.decode("utf-8", errors="ignore")
                    payload = json.loads(raw)
                    dispatch_event(payload)
                    self.redis_client.xack(
                        RedisKeys.NOTIFICATION_EVENTS_STREAM,
                        self._consumer_group,
                        msg_id,
                    )
            except redis.ConnectionError as e:
                logger.error(f"{name} Redis 连接错误: {e}")
                # 重建连接（Windows 下 socket 失效常见：10038）
                try:
                    if self.redis_client:
                        try:
                            self.redis_client.close()
                        except Exception:
                            pass
                    wrapper = RedisClient(
                        url=settings.REDIS_URL,
                        max_connections=settings.REDIS_MAX_CONNECTIONS,
                        decode_responses=True,
                    )
                    wrapper.connect_sync()
                    self.redis_client = wrapper.sync_client
                except Exception:
                    pass
                threading.Event().wait(timeout=1.0)
            except Exception as e:
                logger.error(f"{name} 处理推送异常: {e}")
        logger.info(f"{name} 已停止")


notification_worker_pool = NotificationWorkerPool()

