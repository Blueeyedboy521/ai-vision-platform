# -*- coding: utf-8 -*-
"""
视频处理管道

负责单路摄像头的完整处理流程：
- StreamReader: 拉流线程
- StreamWriter: 推流线程
- ResultHandler: 结果处理线程

支持在同一进程内按指令动态切换模式（live_only / inference_only / full），
通过 PipelineService/Scheduler 调用 set_mode，在管道内部启停对应线程。
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
from .overlay_state import OverlayState


@dataclass
class PipelineConfig:
    """Pipeline 配置"""
    camera_id: str
    camera_name: str
    rtsp_url: str
    fps: int = 25
    skip_frames: int = 3
    algorithms: list = None
    # 模式：full / live_only / inference_only
    mode: str = "full"
    # 推流绘框用：build_inferencer 参数（仅用于 draw_boxes，不 load）
    draw_model: Optional[dict] = None


class Pipeline:
    """
    视频处理管道
    
    作为 Engine 内部对象运行，管理三个线程：
    - StreamReader: 从 RTSP 拉流
    - StreamWriter: 向 RTMP 推流
    - ResultHandler: 处理检测结果
    """
    
    def __init__(
        self,
        config: PipelineConfig,
        request_queue: Optional[Any] = None,
        result_queue: Optional[Any] = None,
    ):
        """
        初始化 Pipeline。
        
        Args:
            config: Pipeline 配置
            request_queue: 推理请求队列（给 InferenceService 的模型请求队列）
            result_queue: 推理结果队列（InferenceService → Pipeline）
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
        self.frame_queue = Queue(maxsize=3)  # 原始帧队列
        self.draw_queue = Queue(maxsize=30)   # 绘制帧队列
        # ResultHandler -> StreamWriter 最新绘框数据（OverlayState 内深拷贝，result 销毁后仍有效；每路 Pipeline 一个进程一个实例）
        self.overlay_state = OverlayState(camera_id=self.config.camera_id)
        
        # 状态
        self.running = False
        self.start_time: Optional[float] = None
        
        # 统计
        self.processed_frames = 0
        self.dropped_frames = 0
    
    def start(self):
        """启动 Pipeline"""
        logger.info(f"Pipeline 启动中: {self.config.camera_name}, mode={self.config.mode}")
        self.running = True
        self.start_time = time.time()
        
        try:
            from config.settings import settings
            debug_reader_push = bool(getattr(settings, "ENGINE_DEBUG_READER_OPENCV_PUSH", False))
            debug_push_url = self._get_push_url() if debug_reader_push else None

            # 启动 StreamReader（始终存在，仅通过 request_queue 是否为 None 决定是否向推理服务发请求）
            self.stream_reader = StreamReader(
                camera_id=self.config.camera_id,
                rtsp_url=self.config.rtsp_url,
                fps=self.config.fps,
                skip_frames=self.config.skip_frames,
                frame_queue=self.frame_queue,
                # live_only 模式不发推理请求
                request_queue=None if debug_reader_push else (self.request_queue if self.config.mode in ("full", "inference_only") else None),
                result_queue=self.result_queue,
                disable_inference=debug_reader_push,
                direct_push_url=debug_push_url,
                direct_push_ffmpeg=debug_reader_push,
                direct_push_only=debug_reader_push,
            )
            self.stream_reader.start()
            
            # 按初始模式应用线程组合（仅在首次启动时生效，后续通过 set_mode 动态切换）
            self._apply_mode(self.config.mode, initial=True)
            
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

    def _apply_mode(self, mode: str, initial: bool = False) -> None:
        """
        在当前 Pipeline 进程内按目标模式启停线程。
        
        Args:
            mode: 目标模式（"live_only" / "inference_only" / "full"）
            initial: 是否为首次启动时应用（仅影响日志文本）
        """
        old_mode = self.config.mode
        if initial:
            logger.info(f"Pipeline 初始模式: camera_id={self.config.camera_id}, mode={mode}")
            self.config.mode = mode
        else:
            if mode == old_mode:
                return
            logger.info(f"Pipeline 模式切换: camera_id={self.config.camera_id}, {old_mode} -> {mode}")
            self.config.mode = mode

        # 1. 控制 StreamReader 是否向推理服务发送请求
        from config.settings import settings
        debug_reader_push = bool(getattr(settings, "ENGINE_DEBUG_READER_OPENCV_PUSH", False))
        if self.stream_reader:
            if debug_reader_push:
                # 调试：强制关闭推理
                self.stream_reader.disable_inference = True
                self.stream_reader.request_queue = None
            else:
                self.stream_reader.disable_inference = False
                if mode in ("full", "inference_only"):
                    # full / inference_only: 需要往推理服务发送帧
                    self.stream_reader.request_queue = self.request_queue
                else:
                    # live_only: 只推流，不推理
                    self.stream_reader.request_queue = None

        # 2. 控制 StreamWriter 是否存在
        writer_needed = mode in ("full", "live_only")
        if writer_needed:
            push_url = self._get_push_url()
            from config.settings import settings
            debug_reader_push = bool(getattr(settings, "ENGINE_DEBUG_READER_OPENCV_PUSH", False))

            if debug_reader_push:
                # 调试：跳过 StreamWriter，由 StreamReader 直接 FFmpeg 推流到远端，并关闭推理请求
                if self.stream_writer:
                    self.stream_writer.stop()
                    self.stream_writer = None
                if self.stream_reader:
                    self.stream_reader.disable_inference = True
                    self.stream_reader.direct_push_ffmpeg = True
                    self.stream_reader.direct_push_url = push_url
                    self.stream_reader.direct_push_only = True
                logger.info(f"Pipeline {self.config.camera_id} 调试模式已开启：StreamReader 直推 -> {push_url}")
            else:
                # 正常模式：确保关闭 Reader 直推
                if self.stream_reader:
                    self.stream_reader.direct_push_ffmpeg = False
                    self.stream_reader.direct_push_url = None
                    self.stream_reader.direct_push_only = False
                if self.stream_writer is None:
                    draw_inferencer = None
                    draw_boxes = False
                    if self.config.draw_model:
                        draw_boxes = getattr(settings, "ENGINE_STREAM_DRAW_BOXES", False)
                        if draw_boxes:
                            from engine.inference.inferencer import build_inferencer
                            dm = self.config.draw_model
                            # for_draw=True：构造轻量化绘框 inferencer，只用于 draw_boxes，不调用 load()/infer()
                            draw_inferencer = build_inferencer(
                                model_type=dm.get("model_type", "yolo"),
                                model_id=dm.get("model_id", ""),
                                model_path=dm.get("model_path", ""),
                                device=dm.get("device", "cpu"),
                                input_size=tuple(dm.get("input_size") or (640, 640)),
                                for_draw=True,
                            )
                    logger.info(
                        f"Pipeline {self.config.camera_id} 绘框模型: {self.config.draw_model}, "
                        f"draw_boxes: {draw_boxes}, inferencer: {draw_inferencer is not None}"
                    )
                    self.stream_writer = StreamWriter(
                        camera_id=self.config.camera_id,
                        push_url=push_url,
                        frame_queue=self.frame_queue,
                        fps=self.config.fps,
                        overlay_state=self.overlay_state,
                        inferencer=draw_inferencer,
                    )
                    self.stream_writer.start()
        else:
            if self.stream_writer:
                self.stream_writer.stop()
                self.stream_writer = None

        # 3. 控制 ResultHandler 是否存在
        handler_needed = mode in ("full", "inference_only")
        if handler_needed:
            if self.result_handler is None:
                self.result_handler = ResultHandler(
                    camera_id=self.config.camera_id,
                    result_queue=self.result_queue,
                    algorithms=self.config.algorithms or [],
                    overlay_state=self.overlay_state,
                )
                self.result_handler.start()
        else:
            if self.result_handler:
                self.result_handler.stop()
                self.result_handler = None

    def set_mode(self, mode: str) -> None:
        """
        对外暴露的模式切换接口，由子进程内的控制循环调用。
        """
        self._apply_mode(mode, initial=False)
    
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
