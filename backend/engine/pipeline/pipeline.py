# -*- coding: utf-8 -*-
"""
视频处理管道

负责单路摄像头的完整处理流程：
- StreamReader: 拉流线程
- StreamWriter: 推流线程
- ResultHandler: 结果处理线程
"""
import threading
import time
import uuid
from typing import Any, Dict, Optional
from dataclasses import dataclass

from loguru import logger

from .stream_reader import StreamReader
from .stream_writer import StreamWriter
from .result_handler import ResultHandler


@dataclass
class PipelineConfig:
    """Pipeline 配置"""
    camera_id: str
    camera_name: str
    rtsp_url: str
    fps: int = 25
    skip_frames: int = 3
    algorithms: list = None


class Pipeline:
    """
    视频处理管道
    
    作为独立进程运行，管理三个线程：
    - StreamReader: 从 RTSP 拉流
    - StreamWriter: 向 RTMP 推流
    - ResultHandler: 处理检测结果
    """
    
    def __init__(
        self,
        config: PipelineConfig,
        request_queue: Optional[Any] = None,
        result_queue: Optional[Any] = None
    ):
        """
        初始化 Pipeline
        
        Args:
            config: Pipeline 配置
            request_queue: 推理请求队列
            result_queue: 推理结果队列
        """
        self.config = config
        self.request_queue = request_queue
        self.result_queue = result_queue
        
        # 线程
        self.stream_reader: Optional[StreamReader] = None
        self.stream_writer: Optional[StreamWriter] = None
        self.result_handler: Optional[ResultHandler] = None
        
        # 内部队列
        from queue import Queue
        self.frame_queue = Queue(maxsize=30)  # 原始帧队列
        self.draw_queue = Queue(maxsize=30)   # 绘制帧队列
        
        # 状态
        self.running = False
        self.start_time: Optional[float] = None
        
        # 统计
        self.processed_frames = 0
        self.dropped_frames = 0
    
    @classmethod
    def run(cls, config: dict, request_queue: Any, result_queue: Any):
        """进程入口函数"""
        pipeline_config = PipelineConfig(
            camera_id=config.get("camera_id", ""),
            camera_name=config.get("camera_name", ""),
            rtsp_url=config.get("rtsp_url", ""),
            fps=config.get("fps", 25),
            skip_frames=config.get("skip_frames", 3),
            algorithms=config.get("algorithms", [])
        )
        
        pipeline = cls(pipeline_config, request_queue, result_queue)
        pipeline.start()
        
        # 保持进程运行
        try:
            while pipeline.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            pipeline.stop()
    
    def start(self):
        """启动 Pipeline"""
        logger.info(f"Pipeline 启动中: {self.config.camera_name}")
        self.running = True
        self.start_time = time.time()
        
        try:
            # 启动 StreamReader
            self.stream_reader = StreamReader(
                camera_id=self.config.camera_id,
                rtsp_url=self.config.rtsp_url,
                fps=self.config.fps,
                skip_frames=self.config.skip_frames,
                frame_queue=self.frame_queue,
                request_queue=self.request_queue,
                result_queue=self.result_queue
            )
            self.stream_reader.start()
            
            # 启动 StreamWriter
            push_url = self._get_push_url()
            self.stream_writer = StreamWriter(
                camera_id=self.config.camera_id,
                push_url=push_url,
                frame_queue=self.draw_queue,
                fps=self.config.fps
            )
            self.stream_writer.start()
            
            # 启动 ResultHandler
            self.result_handler = ResultHandler(
                camera_id=self.config.camera_id,
                result_queue=self.result_queue,
                frame_queue=self.frame_queue,
                draw_queue=self.draw_queue,
                algorithms=self.config.algorithms or []
            )
            self.result_handler.start()
            
            logger.info(f"Pipeline 启动完成: {self.config.camera_name}")
            
        except Exception as e:
            logger.exception(f"Pipeline 启动失败: {e}")
            self.stop()
            raise
    
    def stop(self):
        """停止 Pipeline"""
        logger.info(f"Pipeline 停止中: {self.config.camera_name}")
        self.running = False
        
        # 停止各线程
        if self.stream_reader:
            self.stream_reader.stop()
        if self.stream_writer:
            self.stream_writer.stop()
        if self.result_handler:
            self.result_handler.stop()
        
        logger.info(f"Pipeline 已停止: {self.config.camera_name}")
    
    def _get_push_url(self) -> str:
        """获取推流地址"""
        # TODO: 从配置或 ZLMediaKit API 获取
        from config.settings import settings
        
        stream_key = f"camera_{self.config.camera_id}"
        push_url = f"rtmp://{settings.ZLM_HOST}:{settings.ZLM_RTMP_PORT}/live/{stream_key}"
        
        logger.info(f"推流地址: {push_url}")
        return push_url
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "camera_id": self.config.camera_id,
            "camera_name": self.config.camera_name,
            "uptime": uptime,
            "processed_frames": self.processed_frames,
            "dropped_frames": self.dropped_frames,
            "running": self.running,
            "stream_reader": self.stream_reader.get_stats() if self.stream_reader else None,
            "stream_writer": self.stream_writer.get_stats() if self.stream_writer else None,
            "result_handler": self.result_handler.get_stats() if self.result_handler else None
        }
