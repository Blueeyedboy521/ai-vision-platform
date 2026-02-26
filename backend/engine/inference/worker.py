# -*- coding: utf-8 -*-
"""
推理 Worker

从请求队列获取帧，执行推理，将结果放入结果队列
"""
import threading
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from loguru import logger

from .model_loader import ModelLoader


@dataclass
class InferenceRequest:
    """推理请求"""
    request_id: str
    camera_id: str
    frame_id: int
    frame: Any  # numpy.ndarray
    timestamp: float


@dataclass
class InferenceResult:
    """推理结果"""
    request_id: str
    camera_id: str
    frame_id: int
    detections: list  # 检测结果列表
    inference_time_ms: float
    timestamp: float


class InferenceWorker:
    """
    推理 Worker
    
    作为线程运行，从请求队列获取帧并执行推理
    """
    
    def __init__(
        self,
        worker_id: str,
        model_id: str,
        model_path: str,
        model_type: str,
        input_size: tuple,
        request_queue: Any,
        result_queues: Dict[str, Any]
    ):
        """
        初始化 Worker
        
        Args:
            worker_id: Worker 标识
            model_id: 模型 ID
            model_path: 模型文件路径
            model_type: 模型类型 (yolo, onnx, tensorrt)
            input_size: 输入尺寸
            request_queue: 请求队列
            result_queues: 结果队列映射 {camera_id: queue}
        """
        self.worker_id = worker_id
        self.model_id = model_id
        self.model_path = model_path
        self.model_type = model_type
        self.input_size = input_size
        self.request_queue = request_queue
        self.result_queues = result_queues
        
        self.model = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # 统计信息
        self.processed_frames = 0
        self.total_time_ms = 0
    
    def start(self):
        """启动 Worker"""
        logger.info(f"Worker {self.worker_id} 启动中...")
        
        # 加载模型
        self._load_model()
        
        # 启动处理线程
        self.is_running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        
        logger.info(f"Worker {self.worker_id} 已启动")
    
    def stop(self):
        """停止 Worker"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Worker {self.worker_id} 已停止")
    
    def _load_model(self):
        """加载模型"""
        logger.info(f"Worker {self.worker_id} 加载模型: {self.model_path}")
        
        try:
            self.model = ModelLoader.load(
                model_path=self.model_path,
                model_type=self.model_type,
                input_size=self.input_size
            )
            logger.info(f"Worker {self.worker_id} 模型加载完成")
        except Exception as e:
            logger.error(f"Worker {self.worker_id} 模型加载失败: {e}")
            # 使用模拟模型
            self.model = None
    
    def _process_loop(self):
        """处理循环"""
        logger.debug(f"Worker {self.worker_id} 进入处理循环")
        
        while self.is_running:
            try:
                # 从队列获取请求 (超时 1 秒)
                request = self.request_queue.get(timeout=1)
                if request is None:
                    continue

                # 兼容 dict / InferenceRequest 两种形式
                if isinstance(request, dict):
                    frame = request.get("frame")
                    request_id = request.get("request_id")
                    camera_id = request.get("camera_id")
                    frame_id = request.get("frame_id")
                else:
                    frame = request.frame
                    request_id = request.request_id
                    camera_id = request.camera_id
                    frame_id = request.frame_id
                
                if frame is None:
                    continue
                
                # 执行推理
                start_time = time.perf_counter()
                detections = self._inference(frame)
                inference_time_ms = (time.perf_counter() - start_time) * 1000
                
                # 构建结果
                result = InferenceResult(
                    request_id=request_id,
                    camera_id=camera_id,
                    frame_id=frame_id,
                    detections=detections,
                    inference_time_ms=inference_time_ms,
                    timestamp=time.time()
                )
                
                # 放入结果队列（根据 camera_id 选择对应的结果队列）
                result_queue = self.result_queues.get(camera_id)
                if result_queue:
                    result_queue.put(result)
                
                # 更新统计
                self.processed_frames += 1
                self.total_time_ms += inference_time_ms
                
            except Exception as e:
                if "Empty" not in str(type(e).__name__):
                    logger.error(f"Worker {self.worker_id} 处理异常: {e}")
    
    def _inference(self, frame) -> list:
        """
        执行推理
        
        Args:
            frame: 输入图像
            
        Returns:
            检测结果列表
        """
        if self.model is None:
            # 模拟推理结果
            return []
        
        try:
            # 执行推理
            results = self.model.predict(frame)
            
            # 解析结果
            detections = []
            for r in results:
                boxes = r.boxes
                if boxes is None:
                    continue
                    
                for box in boxes:
                    detection = {
                        "class_id": int(box.cls[0]),
                        "class_name": self.model.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    }
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"推理失败: {e}")
            return []
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "worker_id": self.worker_id,
            "processed_frames": self.processed_frames,
            "avg_time_ms": self.total_time_ms / max(self.processed_frames, 1),
            "is_running": self.is_running
        }
