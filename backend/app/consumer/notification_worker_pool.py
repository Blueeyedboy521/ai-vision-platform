# -*- coding: utf-8 -*-
"""
推送处理线程池

从 Redis notification_queue 消费推送事件，调用 notification_service.dispatch_event
"""

import json
import threading
from typing import List, Optional

import redis

from common.logging import logger
from config.settings import settings
from common.redis.client import get_redis_client


class NotificationWorkerPool:
    def __init__(self):
        self.workers: List[threading.Thread] = []
        self.running = False
        self.redis_client: Optional[redis.Redis] = None

    def start(self, num_workers: int = 2) -> None:
        if self.running:
            return
        self.running = True

        wrapper = get_redis_client()
        try:
            wrapper.connect_sync()
        except Exception as e:
            logger.error(f"推送线程池初始化 Redis 连接失败: {e}")
            self.running = False
            return
        self.redis_client = wrapper.sync_client

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
        if self.redis_client:
            for _ in range(len(self.workers)):
                try:
                    self.redis_client.rpush(settings.NOTIFICATION_QUEUE_NAME, json.dumps({"__stop__": True}))
                except Exception:
                    pass
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

        while self.running:
            try:
                res = self.redis_client.blpop(settings.NOTIFICATION_QUEUE_NAME, timeout=1)
                if res is None:
                    continue
                _, data = res
                try:
                    payload = json.loads(data)
                except Exception:
                    continue
                if payload.get("__stop__"):
                    break
                dispatch_event(payload)
            except redis.ConnectionError as e:
                logger.error(f"{name} Redis 连接错误: {e}")
                threading.Event().wait(timeout=1.0)
            except Exception as e:
                logger.error(f"{name} 处理推送异常: {e}")

        logger.info(f"{name} 已停止")


notification_worker_pool = NotificationWorkerPool()

