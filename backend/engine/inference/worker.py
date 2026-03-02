# -*- coding: utf-8 -*-
"""
推理 Worker

职责：加载推理器、从队列取请求、组 params 字典交给 infer(params)、将返回的 InferenceResult 放入结果队列。
推理实现类在 infer 内完成计时与结果组装，Worker 不再二次组装。
可选：若 config 中 TEST_SAVE_DRAW=True，Worker 会调用推理器的 draw_boxes(result) 并保存绘框图到 TEST_SAVE_DRAW_DIR。
"""
import os
import threading
import time
from dataclasses import replace
from typing import Optional, Dict, Any
from dataclasses import dataclass

from loguru import logger

from .inferencer import build_inferencer, Inferencer, InferenceResult


@dataclass
class InferenceRequest:
    """推理请求"""
    request_id: str
    camera_id: str
    frame_id: int
    frame: Any  # numpy.ndarray
    timestamp: float


class InferenceWorker:
    """
    推理 Worker：仅负责加载推理器、循环取帧、调用 infer、组结果入队。
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
        self.worker_id = worker_id
        self.model_id = model_id
        self.model_path = model_path
        self.model_type = model_type
        self.input_size = input_size
        self.request_queue = request_queue
        self.result_queues = result_queues

        self.inferencer: Optional[Inferencer] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        self.processed_frames = 0
        self.total_time_ms = 0

    def start(self):
        """启动 Worker"""
        logger.info(f"Worker {self.worker_id} 启动中...")
        self._load_model()
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
        """创建推理器并调用 load()，下载与 classes 等由实现类负责"""
        logger.info(f"Worker {self.worker_id} 加载模型: {self.model_path}")
        try:
            device = "cuda:0"
            self.inferencer = build_inferencer(
                model_type=self.model_type,
                model_id=self.model_id,
                model_path=self.model_path,
                device=device,
                input_size=self.input_size,
            )
            self.inferencer.load()
            logger.info(f"Worker {self.worker_id} 模型加载完成")
        except Exception as e:
            logger.error(f"Worker {self.worker_id} 模型加载失败: {e}")
            self.inferencer = None
    def _process_loop(self):
        """处理循环"""
        logger.debug(f"Worker {self.worker_id} 进入处理循环")
        last_alive_log_time = time.time()
        alive_log_interval = 10.0  # 秒
        last_camera_id: Optional[str] = None
        last_frame_id: Optional[int] = None

        while self.is_running:
            try:
                # 打印进程pid
                # logger.info(f"Worker {self.worker_id} 处理循环，队列大小: {self.request_queue.qsize()},进程pid: {os.getpid()}")
                # 从队列获取请求 (超时 1 秒)
                request = self.request_queue.get(timeout=0.4)
                # logger.info(f"Worker {self.worker_id} 处理循环，获取请求{request is None}, 进程pid: {os.getpid()}")
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

                params = {
                    "frame": frame,
                    "request_id": request_id,
                    "camera_id": camera_id,
                    "frame_id": frame_id,
                    "timestamp": time.time(),
                }
                result = self._inference(params)

                result_queue = self.result_queues.get(camera_id)
                if result_queue:
                    result_queue.put(result)

                # 测试验证：若 .env 中 TEST_SAVE_DRAW=True，调用推理器 draw_boxes(result) 并保存绘框图
                try:
                    from config.settings import get_settings
                    settings = get_settings()
                    if settings.TEST_SAVE_DRAW and settings.TEST_SAVE_DRAW_DIR and self.inferencer is not None:
                        result_with_frame = replace(result, frame=params.get("frame"))
                        drawn = self.inferencer.draw_boxes(result_with_frame)
                        if drawn is not None:
                            os.makedirs(settings.TEST_SAVE_DRAW_DIR, exist_ok=True)
                            import cv2
                            path = os.path.join(settings.TEST_SAVE_DRAW_DIR, f"test__{camera_id}_{frame_id}.jpg")
                            cv2.imwrite(path, drawn)
                            logger.info(f"测试绘框图已保存: {path}, 检测数={len(result.detections)}")
                except Exception as e:
                    logger.debug(f"测试保存绘框图跳过或失败: {e}")

                self.processed_frames += 1
                self.total_time_ms += result.inference_time_ms
                last_camera_id = camera_id
                last_frame_id = frame_id

                now_wall = time.time()
                if (
                    now_wall - last_alive_log_time >= alive_log_interval
                    and last_camera_id is not None
                    and last_frame_id is not None
                ):
                    last_alive_log_time = now_wall
                    logger.info(
                        f"InferenceWorker {self.worker_id} 正在推理，model_id={self.model_id}, "
                        f"camera_id={last_camera_id}, frame_id={last_frame_id}, "
                        f"processed_frames={self.processed_frames}, "
                        f"avg_time_ms={self.total_time_ms / max(self.processed_frames, 1):.2f}, 推理结果: {result}"
                    )
            except Exception as e:
                if "Empty" not in str(type(e).__name__):
                    logger.error(f"Worker {self.worker_id} 处理异常，可能空队列: {e}")
                else:
                    logger.info(f"Worker {self.worker_id} 处理异常: {e}")
    
    def _inference(self, params: Dict[str, Any]) -> InferenceResult:
        """调用推理器 infer(params)，由实现类内部计时并组装完整 InferenceResult 返回"""
        if self.inferencer is None:
            logger.warning(f"Worker {self.worker_id} 模型未加载，返回空结果，model_id={self.model_id}")
            return InferenceResult(
                request_id=params.get("request_id", ""),
                camera_id=params.get("camera_id", ""),
                frame_id=int(params.get("frame_id", 0)),
                detections=[],
                inference_time_ms=0.0,
                timestamp=params.get("timestamp", time.time()),
            )
        try:
            return self.inferencer.infer(params)
        except Exception as e:
            logger.error(f"推理失败: {e}")
            return InferenceResult(
                request_id=params.get("request_id", ""),
                camera_id=params.get("camera_id", ""),
                frame_id=int(params.get("frame_id", 0)),
                detections=[],
                inference_time_ms=0.0,
                timestamp=params.get("timestamp", time.time()),
            )
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "worker_id": self.worker_id,
            "processed_frames": self.processed_frames,
            "avg_time_ms": self.total_time_ms / max(self.processed_frames, 1),
            "is_running": self.is_running
        }
