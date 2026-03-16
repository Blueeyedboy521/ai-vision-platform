# -*- coding: utf-8 -*-
"""
告警处理线程池

管理多个 Worker 线程从 Redis 队列消费告警消息
"""
import json
import threading
from typing import List, Optional

import redis

from common.logging import logger
from config.settings import settings
from common.redis.channels import RedisKeys

from common.redis.client import RedisClient


class AlarmWorkerPool:
    """
    告警处理线程池
    
    管理 N 个 Worker 线程，从 Redis alarm_queue 消费告警消息
    """
    
    def __init__(self):
        """初始化线程池"""
        self.workers: List[threading.Thread] = []
        self.running = False
        self.redis_client: Optional[redis.Redis] = None
        self._lock = threading.Lock()
    
    def start(self, num_workers: int = 4) -> None:
        """
        启动线程池
        
        Args:
            num_workers: Worker 数量
        """
        if self.running:
            logger.warning("告警线程池已在运行中")
            return
        
        self.running = True
        
        # 创建独立的同步 Redis 客户端（避免与其它线程池共享同一连接后被 close）
        redis_wrapper = RedisClient(
            url=settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )
        try:
            redis_wrapper.connect_sync()
        except Exception as e:
            logger.error(f"告警线程池初始化 Redis 连接失败: {e}")
            self.running = False
            return
        self.redis_client = redis_wrapper.sync_client
        
        # 创建 Worker 线程
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"AlarmWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"告警线程池已启动: {num_workers} 个 Worker")
    
    def stop(self, timeout: float = 5.0) -> None:
        """
        停止线程池
        
        Args:
            timeout: 等待超时时间(秒)
        """
        if not self.running:
            return
        
        logger.info("正在停止告警线程池...")
        self.running = False
        
        # 向队列发送停止信号
        if self.redis_client:
            for _ in range(len(self.workers)):
                try:
                    self.redis_client.rpush(
                        settings.ALARM_QUEUE_NAME,
                        json.dumps({"__stop__": True})
                    )
                except Exception as e:
                    logger.warning(f"发送停止信号失败: {e}")
        
        # 等待所有 Worker 结束
        for worker in self.workers:
            worker.join(timeout=timeout)
            if worker.is_alive():
                logger.warning(f"Worker {worker.name} 未能在超时时间内停止")
        
        self.workers.clear()
        
        # 关闭 Redis 连接
        if self.redis_client:
            self.redis_client.close()
            self.redis_client = None
        
        logger.info("告警线程池已停止")
    
    def _worker_loop(self) -> None:
        """
        Worker 主循环
        
        阻塞式从 Redis 队列消费告警消息
        """
        thread_name = threading.current_thread().name
        logger.info(f"{thread_name} 已启动")
        
        while self.running:
            try:
                # 阻塞式从队列获取消息，超时1秒
                result = self.redis_client.blpop(
                    settings.ALARM_QUEUE_NAME,
                    timeout=1
                )
                
                if result is None:
                    # 超时，继续循环
                    continue
                
                _, data = result
                
                # 解析消息
                try:
                    alarm_data = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.error(f"告警消息解析失败: {e}, 数据: {data[:100]}")
                    continue
                
                # 检查是否是停止信号
                if alarm_data.get("__stop__"):
                    logger.info(f"{thread_name} 收到停止信号")
                    break
                
                # 处理告警
                self._process_alarm(alarm_data)
                
            except redis.ConnectionError as e:
                logger.error(f"Redis 连接错误: {e}")
                if self.running:
                    # 重建连接（Windows 下 socket 失效常见：10038）
                    try:
                        with self._lock:
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
                logger.error(f"{thread_name} 处理异常: {e}")
        
        logger.info(f"{thread_name} 已停止")
    
    def _process_alarm(self, alarm_data: dict) -> None:
        """
        处理告警消息
        
        Args:
            alarm_data: 告警数据
        """
        from .alarm_consumer import process_alarm
        
        try:
            process_alarm(alarm_data)
        except Exception as e:
            logger.error(f"处理告警失败: {e}, 数据: {alarm_data}")
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.running
    
    @property
    def worker_count(self) -> int:
        """Worker 数量"""
        return len(self.workers)


# 全局线程池实例
alarm_worker_pool = AlarmWorkerPool()
