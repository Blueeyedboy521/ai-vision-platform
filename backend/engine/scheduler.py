# -*- coding: utf-8 -*-
"""
主调度器

负责管理整个视频处理引擎的生命周期：
- 读取配置
- 创建和管理子进程
- 健康检查
- 配置热更新
"""
import os
import time
import threading
from typing import Dict, List, Optional
from multiprocessing import Process, Queue
from dataclasses import dataclass, field

from loguru import logger

from engine.inference.service import InferenceService
from engine.pipeline.pipeline import Pipeline
from engine.queue.memory_queue import MemoryQueue


@dataclass
class CameraConfig:
    """摄像头配置"""
    id: str
    name: str
    rtsp_url: str
    fps: int = 25
    skip_frames: int = 3
    algorithms: List[dict] = field(default_factory=list)


@dataclass
class ModelConfig:
    """模型配置"""
    id: str
    name: str
    path: str
    model_type: str  # yolo, onnx, tensorrt
    input_size: tuple = (640, 640)
    inference_time_ms: float = 30.0
    gpu_memory_mb: int = 500


class Scheduler:
    """
    主调度器
    
    负责管理:
    - InferenceService 进程
    - Pipeline 进程
    - 内存队列
    """
    
    def __init__(self):
        self.running = False
        
        # 配置
        self.cameras: Dict[str, CameraConfig] = {}
        self.models: Dict[str, ModelConfig] = {}
        
        # 进程管理
        self.inference_process: Optional[Process] = None
        self.pipeline_processes: Dict[str, Process] = {}
        
        # 队列管理
        self.request_queues: Dict[str, MemoryQueue] = {}  # model_id -> queue
        self.result_queues: Dict[str, MemoryQueue] = {}   # camera_id -> queue
        
        # 统计信息
        self.start_time: Optional[float] = None
        self.processed_frames = 0
        self.generated_alarms = 0
    
    def start(self):
        """启动调度器"""
        logger.info("正在启动调度器...")
        self.running = True
        self.start_time = time.time()
        
        try:
            # 1. 加载配置
            self._load_config()
            
            # 2. 创建队列
            self._create_queues()
            
            # 3. 启动推理服务
            self._start_inference_service()
            
            # 4. 启动所有 Pipeline
            self._start_pipelines()
            
            logger.info(f"引擎启动完成: {len(self.cameras)} 路摄像头, "
                       f"{len(self.models)} 个模型")
            
        except Exception as e:
            logger.exception(f"调度器启动失败: {e}")
            self.stop()
            raise
    
    def stop(self):
        """停止调度器"""
        logger.info("正在停止调度器...")
        self.running = False
        
        # 停止所有 Pipeline
        for camera_id, process in self.pipeline_processes.items():
            if process.is_alive():
                logger.info(f"停止 Pipeline: {camera_id}")
                process.terminate()
                process.join(timeout=5)
        self.pipeline_processes.clear()
        
        # 停止推理服务
        if self.inference_process and self.inference_process.is_alive():
            logger.info("停止推理服务")
            self.inference_process.terminate()
            self.inference_process.join(timeout=10)
        
        logger.info("调度器已停止")
    
    def health_check(self):
        """健康检查"""
        # 检查推理服务
        if self.inference_process and not self.inference_process.is_alive():
            logger.error("推理服务进程已退出，正在重启...")
            self._start_inference_service()
        
        # 检查所有 Pipeline
        for camera_id, process in list(self.pipeline_processes.items()):
            if not process.is_alive():
                logger.warning(f"Pipeline {camera_id} 已退出，正在重启...")
                self._start_pipeline(camera_id)
        
        # 输出统计信息
        if self.start_time:
            uptime = time.time() - self.start_time
            logger.debug(f"运行时间: {uptime:.1f}s, "
                        f"处理帧数: {self.processed_frames}, "
                        f"生成告警: {self.generated_alarms}")
    
    def _load_config(self):
        """从数据库加载配置"""
        logger.info("加载配置...")
        
        # TODO: 从数据库读取实际配置
        # 这里使用示例配置
        
        # 示例摄像头配置
        self.cameras = {
            "camera_001": CameraConfig(
                id="camera_001",
                name="测试摄像头1",
                rtsp_url="rtsp://localhost:554/live/test1",
                fps=25,
                skip_frames=3,
                algorithms=[
                    {"id": "alg_001", "model_id": "model_001", "config": {}}
                ]
            )
        }
        
        # 示例模型配置
        self.models = {
            "model_001": ModelConfig(
                id="model_001",
                name="YOLOv8-安全帽检测",
                path="models/yolov8_safety.pt",
                model_type="yolo",
                input_size=(640, 640),
                inference_time_ms=30.0,
                gpu_memory_mb=500
            )
        }
        
        logger.info(f"加载配置完成: {len(self.cameras)} 个摄像头, "
                   f"{len(self.models)} 个模型")
    
    def _create_queues(self):
        """创建所有队列"""
        logger.info("创建队列...")
        
        # 为每个模型创建请求队列
        for model_id in self.models:
            self.request_queues[model_id] = MemoryQueue(maxsize=100)
            logger.debug(f"创建请求队列: {model_id}")
        
        # 为每个摄像头创建结果队列
        for camera_id in self.cameras:
            self.result_queues[camera_id] = MemoryQueue(maxsize=100)
            logger.debug(f"创建结果队列: {camera_id}")
    
    def _start_inference_service(self):
        """启动推理服务"""
        logger.info("启动推理服务...")
        
        # 准备配置
        models_config = {
            model_id: {
                "id": model.id,
                "name": model.name,
                "path": model.path,
                "model_type": model.model_type,
                "input_size": model.input_size
            }
            for model_id, model in self.models.items()
        }
        
        # 创建并启动进程
        self.inference_process = Process(
            target=InferenceService.run,
            args=(models_config, self.request_queues),
            name="InferenceService"
        )
        self.inference_process.start()
        logger.info(f"推理服务进程已启动: PID={self.inference_process.pid}")
    
    def _start_pipelines(self):
        """启动所有 Pipeline"""
        logger.info("启动所有 Pipeline...")
        
        for camera_id in self.cameras:
            self._start_pipeline(camera_id)
    
    def _start_pipeline(self, camera_id: str):
        """启动单个 Pipeline"""
        camera = self.cameras.get(camera_id)
        if not camera:
            logger.error(f"摄像头配置不存在: {camera_id}")
            return
        
        # 准备配置
        pipeline_config = {
            "camera_id": camera.id,
            "camera_name": camera.name,
            "rtsp_url": camera.rtsp_url,
            "fps": camera.fps,
            "skip_frames": camera.skip_frames,
            "algorithms": camera.algorithms
        }
        
        # 获取相关队列
        request_queue = None
        if camera.algorithms:
            model_id = camera.algorithms[0].get("model_id")
            if model_id:
                request_queue = self.request_queues.get(model_id)
        
        result_queue = self.result_queues.get(camera_id)
        
        # 创建并启动进程
        process = Process(
            target=Pipeline.run,
            args=(pipeline_config, request_queue, result_queue),
            name=f"Pipeline-{camera_id}"
        )
        process.start()
        
        self.pipeline_processes[camera_id] = process
        logger.info(f"Pipeline 已启动: {camera.name} (PID={process.pid})")
    
    def add_camera(self, camera_config: CameraConfig):
        """动态添加摄像头"""
        camera_id = camera_config.id
        if camera_id in self.cameras:
            logger.warning(f"摄像头已存在: {camera_id}")
            return
        
        self.cameras[camera_id] = camera_config
        self.result_queues[camera_id] = MemoryQueue(maxsize=100)
        self._start_pipeline(camera_id)
        logger.info(f"已添加摄像头: {camera_config.name}")
    
    def remove_camera(self, camera_id: str):
        """动态移除摄像头"""
        if camera_id not in self.cameras:
            logger.warning(f"摄像头不存在: {camera_id}")
            return
        
        # 停止 Pipeline
        process = self.pipeline_processes.get(camera_id)
        if process and process.is_alive():
            process.terminate()
            process.join(timeout=5)
        
        # 清理资源
        del self.pipeline_processes[camera_id]
        del self.result_queues[camera_id]
        del self.cameras[camera_id]
        
        logger.info(f"已移除摄像头: {camera_id}")
