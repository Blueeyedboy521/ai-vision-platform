# -*- coding: utf-8 -*-
"""
推理服务

管理多个 InferenceWorker 线程，处理来自多个摄像头的推理请求
"""
import threading
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from loguru import logger

from .worker import InferenceWorker
from .model_loader import ModelLoader


@dataclass
class WorkerConfig:
    """Worker 配置"""
    model_id: str
    model_path: str
    model_type: str
    input_size: tuple
    gpu_id: int = 0


class InferenceService:
    """
    推理服务
    
    作为独立进程运行，管理多个 Worker 线程
    """
    
    def __init__(self, models_config: Dict[str, dict], request_queues: Dict, result_queues: Dict):
        """
        初始化推理服务
        
        Args:
            models_config: 模型配置字典 {model_id: config}
            request_queues: 请求队列字典 {model_id: queue}
            result_queues: 结果队列字典 {camera_id: queue}
        """
        self.models_config = models_config
        self.request_queues = request_queues
        self.result_queues = result_queues
        
        self.workers: Dict[str, List[InferenceWorker]] = {}  # model_id -> workers
        self.running = False
        
        # 统计信息
        self.total_inferences = 0
        self.total_time_ms = 0
    
    @classmethod
    def run(cls, models_config: Dict[str, dict], request_queues: Dict, result_queues: Dict):
        """进程入口函数"""
        service = cls(models_config, request_queues, result_queues)
        service.start()
        
        # 保持进程运行
        try:
            while service.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            service.stop()
    
    def start(self):
        """启动推理服务"""
        logger.info("推理服务启动中...")
        self.running = True
        
        # 为每个模型创建 Worker
        for model_id, config in self.models_config.items():
            self._create_workers(model_id, config)
        
        logger.info(f"推理服务启动完成: {len(self.workers)} 个模型已加载")
    
    def stop(self):
        """停止推理服务"""
        logger.info("停止推理服务...")
        self.running = False
        
        # 停止所有 Worker
        for model_id, workers in self.workers.items():
            for worker in workers:
                worker.stop()
        
        logger.info("推理服务已停止")
    
    def _create_workers(self, model_id: str, config: dict):
        """为模型创建 Worker"""
        logger.info(f"创建 Worker: {config.get('name', model_id)}")
        
        request_queue = self.request_queues.get(model_id)
        if not request_queue:
            logger.warning(f"模型 {model_id} 没有对应的请求队列")
            return
        
        # 计算需要的 Worker 数量
        # TODO: 根据摄像头数量和帧率动态计算
        worker_count = 1
        
        workers = []
        for i in range(worker_count):
            worker = InferenceWorker(
                worker_id=f"{model_id}_worker_{i}",
                model_id=model_id,
                model_path=config.get("path", ""),
                model_type=config.get("model_type", "yolo"),
                input_size=config.get("input_size", (640, 640)),
                request_queue=request_queue,
                result_queues=self.result_queues,
            )
            worker.start()
            workers.append(worker)
        
        self.workers[model_id] = workers
        logger.info(f"模型 {model_id} 创建了 {worker_count} 个 Worker")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = {
            "total_inferences": self.total_inferences,
            "avg_time_ms": self.total_time_ms / max(self.total_inferences, 1),
            "workers": {}
        }
        
        for model_id, workers in self.workers.items():
            stats["workers"][model_id] = {
                "count": len(workers),
                "running": sum(1 for w in workers if w.is_running)
            }
        
        return stats
