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
from common.redis import get_redis_client, RedisChannels, RedisKeys
import json


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
        
        # 配置监听线程（通过 Redis 接收 FastAPI 的配置变更）
        self._config_thread: Optional[threading.Thread] = None
        self._config_running: bool = False
    
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
            
            # 5. 启动 Redis 配置监听（Engine 订阅 engine:config_update）
            self._start_config_listener()
            
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
        
        # 停止配置监听线程
        self._stop_config_listener()
        
        logger.info("调度器已停止")

    def _start_config_listener(self):
        """启动配置监听线程，从 Redis 订阅配置变更事件"""
        if self._config_thread and self._config_thread.is_alive():
            return
        self._config_running = True
        
        def _worker():
            client = get_redis_client()
            try:
                client.connect_sync()
                pubsub = client.sync_client.pubsub()
                pubsub.subscribe(RedisChannels.ENGINE_CONFIG_UPDATE)
                logger.info(f"Engine 已订阅 Redis 频道: {RedisChannels.ENGINE_CONFIG_UPDATE}" )
                
                while self._config_running:
                    message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if not message:
                        time.sleep(0.1)
                        continue
                    try:
                        data = json.loads(message.get("data") or "{}")
                        action = data.get("action")
                        payload = data.get("data") or {}
                        self._handle_config_event(action, payload)
                    except Exception as e:
                        logger.error(f"解析配置更新消息失败: {e}")
                        time.sleep(0.5)
            except Exception as e:
                logger.error(f"Engine 配置监听线程启动失败: {e}")
        
        self._config_thread = threading.Thread(target=_worker, daemon=True)
        self._config_thread.start()

    def _stop_config_listener(self):
        """停止配置监听线程"""
        self._config_running = False
        if self._config_thread and self._config_thread.is_alive():
            self._config_thread.join(timeout=2)

    def _handle_config_event(self, action: Optional[str], data: dict):
        """
        处理来自 FastAPI 的配置事件。
        当前版本主要负责从 Redis 读取最新配置并打印日志，后续可在此处热更新 self.cameras/self.models。
        """
        if not action:
            return
        
        logger.info(f"Engine 收到配置事件: {action} - {data}")
        
        # 模型相关：从 Redis 读取最新模型配置
        if action in ("model_add", "model_update"):
            model_id = data.get("model_id")
            if not model_id:
                return
            try:
                client = get_redis_client()
                client.connect_sync()
                raw = client.sync_client.get(RedisKeys.model_config(model_id))
                if raw:
                    cfg = json.loads(raw)
                    logger.info(f"Engine 读取模型配置: {cfg}")
            except Exception as e:
                logger.error(f"Engine 读取模型配置失败: {e}")
        
        # 算法相关：从 Redis 读取最新算法配置
        if action in ("algorithm_add", "algorithm_update"):
            algorithm_id = data.get("algorithm_id")
            if not algorithm_id:
                return
            try:
                client = get_redis_client()
                client.connect_sync()
                raw = client.sync_client.get(RedisKeys.algorithm_config(algorithm_id))
                if raw:
                    cfg = json.loads(raw)
                    logger.info(f"Engine 读取算法配置: {cfg}")
            except Exception as e:
                logger.error(f"Engine 读取算法配置失败: {e}")
        
        # 摄像头-算法绑定：从 Redis 读取最新绑定配置
        if action in ("camera_algorithm_add", "camera_algorithm_update"):
            camera_id = data.get("camera_id")
            algorithm_id = data.get("algorithm_id")
            if not camera_id or not algorithm_id:
                return
            try:
                client = get_redis_client()
                client.connect_sync()
                raw = client.sync_client.get(
                    RedisKeys.camera_algorithm_config(camera_id, algorithm_id)
                )
                if raw:
                    cfg = json.loads(raw)
                    logger.info(f"Engine 读取摄像头算法配置: {cfg}")
            except Exception as e:
                logger.error(f"Engine 读取摄像头算法配置失败: {e}")
        
        # 摄像头启动/停止：控制 Pipeline
        if action == "camera_start":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头启动命令: {camera_id}")
            self._start_pipeline(camera_id)
        
        if action == "camera_stop":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头停止命令: {camera_id}")
            process = self.pipeline_processes.get(camera_id)
            if process and process.is_alive():
                logger.info(f"停止 Pipeline 进程: {camera_id}")
                process.terminate()
                process.join(timeout=5)
            self.pipeline_processes.pop(camera_id, None)
    
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
        """从 Redis 加载配置（FastAPI 预先写入的快照）"""
        logger.info("从 Redis 加载引擎配置...")
        
        self.cameras = {}
        self.models = {}
        
        client = get_redis_client()
        try:
            client.connect_sync()
            r = client.sync_client
        except Exception as e:
            logger.error(f"连接 Redis 失败，无法加载配置: {e}")
            return
        
        # 1. 加载模型配置
        try:
            for key in r.scan_iter(f"{RedisKeys.MODEL_CONFIG_PREFIX}*"):
                raw = r.get(key)
                if not raw:
                    continue
                try:
                    cfg = json.loads(raw)
                except Exception:
                    logger.error(f"解析模型配置失败: key={key}")
                    continue
                
                if not cfg.get("is_enabled", True):
                    continue
                
                model_id = cfg.get("id") or str(key).split(":")[-1]
                self.models[model_id] = ModelConfig(
                    id=model_id,
                    name=cfg.get("name", model_id),
                    path=cfg.get("model_path", ""),
                    model_type=cfg.get("model_type", "yolo"),
                    input_size=(
                        int(cfg.get("input_width", 640)),
                        int(cfg.get("input_height", 640)),
                    ),
                    inference_time_ms=float(cfg.get("inference_ms", 30.0)),
                    gpu_memory_mb=int(cfg.get("gpu_memory_mb", 500)),
                )
        except Exception as e:
            logger.error(f"从 Redis 加载模型配置失败: {e}")
        
        # 2. 加载摄像头基础配置
        try:
            for key in r.scan_iter(f"{RedisKeys.CAMERA_CONFIG_PREFIX}*"):
                raw = r.get(key)
                if not raw:
                    continue
                try:
                    cfg = json.loads(raw)
                except Exception:
                    logger.error(f"解析摄像头配置失败: key={key}")
                    continue
                
                if not cfg.get("is_enabled", True):
                    continue
                
                camera_id = cfg.get("id") or str(key).split(":")[-1]
                self.cameras[camera_id] = CameraConfig(
                    id=camera_id,
                    name=cfg.get("name", camera_id),
                    rtsp_url=cfg.get("rtsp_url", ""),
                    fps=int(cfg.get("fps", 25)),
                    skip_frames=int(cfg.get("skip_frames", 3)),
                    algorithms=[],
                )
        except Exception as e:
            logger.error(f"从 Redis 加载摄像头配置失败: {e}")
        
        # 3. 加载摄像头-算法绑定配置
        try:
            for key in r.scan_iter(f"{RedisKeys.CAMERA_ALGORITHM_CONFIG_PREFIX}*"):
                raw = r.get(key)
                if not raw:
                    continue
                try:
                    cfg = json.loads(raw)
                except Exception:
                    logger.error(f"解析摄像头算法配置失败: key={key}")
                    continue
                
                if not cfg.get("is_enabled", True):
                    continue
                
                camera_id = cfg.get("camera_id") or str(key).split(":")[-2]
                algorithm_id = cfg.get("algorithm_id") or str(key).split(":")[-1]
                model_id = cfg.get("model_id")
                if not camera_id or not model_id:
                    continue
                
                # 如果摄像头基础配置还不存在，创建一个占位配置
                if camera_id not in self.cameras:
                    self.cameras[camera_id] = CameraConfig(
                        id=camera_id,
                        name=camera_id,
                        rtsp_url="",
                        fps=int(cfg.get("fps", 25)),
                        skip_frames=int(cfg.get("skip_frames", 3)),
                        algorithms=[],
                    )
                
                algo_entry = {
                    "id": algorithm_id,
                    "model_id": model_id,
                    "config": {
                        "confidence": cfg.get("confidence"),
                        "alert_config": cfg.get("alert_config"),
                        "regions": cfg.get("regions") or [],
                    },
                }
                self.cameras[camera_id].algorithms.append(algo_entry)
        except Exception as e:
            logger.error(f"从 Redis 加载摄像头算法绑定配置失败: {e}")
        
        logger.info(
            f"从 Redis 加载配置完成: {len(self.cameras)} 个摄像头, "
            f"{len(self.models)} 个模型"
        )
    
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
            args=(models_config, self.request_queues, self.result_queues),
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
        # 如果rtsp_url为空，则不启动
        if not camera.rtsp_url:
            logger.warning(f"摄像头{camera_id} RTSP 地址为空，不启动")
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
