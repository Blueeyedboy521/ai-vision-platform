# -*- coding: utf-8 -*-
"""
主调度器

负责管理整个视频处理引擎的生命周期（单进程 + 多线程）：
- 读取配置
- 创建和管理 InferenceService / Pipeline 对象
- 健康检查
- 配置热更新
"""
import os
import time
import threading
from queue import Queue, Empty
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from loguru import logger

from engine.inference.service import InferenceService
from engine.pipeline.service import PipelineService
from engine.queue.memory_queue import MemoryQueue
import json

from engine.redis import (
    get_sync_client,
    get_live_started_camera_ids,
    get_inference_started_camera_ids,
    is_camera_heartbeat_active,
    scan_model_configs,
    scan_camera_configs,
    scan_camera_algorithm_bindings,
    scan_camera_algorithm_configs,
    get_model_config,
    get_algorithm_config,
    get_camera_algorithm_config,
)
from common.redis import RedisChannels, RedisKeys
from app.core.redis import push_alarm_to_queue_sync


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
    classes: List[str] = field(default_factory=list)
    inference_time_ms: float = 30.0
    gpu_memory_mb: int = 500


class Scheduler:
    """
    主调度器
    
    负责管理:
    - InferenceService 线程池（按模型维度管理 Worker 线程）
    - Pipeline（每路摄像头一个 Pipeline 对象，内部 3 个线程）
    - 内存队列（单进程内线程安全）
    """
    
    def __init__(self):
        self.running = False
        
        # 配置
        self.cameras: Dict[str, CameraConfig] = {}
        self.models: Dict[str, ModelConfig] = {}
        
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
        
        # 点播状态：记录已启动直播的摄像头（Engine 自身视角）
        self.live_started: set[str] = set()
        # 推理状态：记录已启动推理的摄像头（Engine 自身视角）
        self.inference_started: set[str] = set()
        
        # 告警队列与处理线程（Engine 内部：ResultHandler -> Scheduler -> Redis alarm_queue）
        self.alarm_queue: Queue = Queue(maxsize=1000)
        self._alarm_thread: Optional[threading.Thread] = None
        self._alarm_running: bool = False
        
        # 服务层封装
        self.inference_service: Optional[InferenceService] = None
        self.pipeline_service: Optional[PipelineService] = None
    
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
            
            # 3. 初始化服务层
            self._init_services()
            
            # 4. 启动所有 Pipeline（按点播/推理开关决定是否启动）
            self._start_pipelines()
            
            # 5. 按需启动推理服务（仅当存在推理任务时）
            self._reconcile_inference_service()
            
            # 6. 启动告警转发线程（将 Engine 内部告警队列写入 Redis alarm_queue）
            self._start_alarm_dispatcher()
            
            # 7. 启动 Redis 配置监听（Engine 订阅 engine:config_update）
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
        if self.pipeline_service is not None:
            try:
                self.pipeline_service.stop_all()
            except Exception as e:
                logger.error(f"停止 PipelineService 失败: {e}")
        
        # 停止推理服务（仅停 Worker 线程，不再管理独立进程）
        if self.inference_service is not None:
            try:
                logger.info("停止推理服务")
                self.inference_service.stop()
            except Exception as e:
                logger.error(f"停止推理服务失败: {e}")
        
        # 停止配置监听线程
        self._stop_config_listener()
        
        # 停止告警处理线程
        if self._alarm_thread is not None:
            self._alarm_running = False
            self._alarm_thread.join(timeout=5)
            self._alarm_thread = None
        
        logger.info("调度器已停止")

    def _start_config_listener(self):
        """启动配置监听线程，从 Redis 订阅配置变更事件"""
        if self._config_thread and self._config_thread.is_alive():
            return
        self._config_running = True
        
        def _worker():
            try:
                r = get_sync_client()
                pubsub = r.pubsub()
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

    def _start_alarm_dispatcher(self) -> None:
        """启动告警转发线程：从 Engine 内部告警队列读取并写入 Redis alarm_queue。"""
        if self._alarm_thread and self._alarm_thread.is_alive():
            return
        self._alarm_running = True

        def _worker():
            logger.info("告警转发线程启动")
            try:
                while self._alarm_running:
                    try:
                        try:
                            alarm = self.alarm_queue.get(timeout=1.0)
                        except Empty:
                            continue
                        if not alarm:
                            continue

                        # 将本地截图绘制检测框后上传到 Storage 的正式目录，并写回 snapshot_path
                        camera_id = str(alarm.get("camera_id") or "")
                        ts_str = str(alarm.get("timestamp") or "")
                        local_path = alarm.pop("local_snapshot_path", None)
                        if local_path and camera_id:
                            try:
                                import os
                                import cv2
                                from datetime import datetime
                                from common.storage import get_storage
                                from engine.inference.draw_utils import draw_detections_inplace

                                # 读取本地原始截图
                                if not os.path.exists(local_path):
                                    logger.error(f"本地告警截图不存在: {local_path}")
                                else:
                                    img = cv2.imread(local_path)
                                    if img is None:
                                        logger.error(f"读取本地告警截图失败: {local_path}")
                                    else:
                                        # 先在截图上绘制检测框
                                        dets = alarm.get("detections") or []
                                        draw_detections_inplace(img, dets)

                                        storage = get_storage()
                                        try:
                                            dt = datetime.fromisoformat(ts_str)
                                        except Exception:
                                            dt = datetime.now()
                                        date_path = dt.strftime("%Y/%m/%d")
                                        file_id = str(int(dt.timestamp() * 1000))
                                        rel_path = f"alarm/{date_path}/{camera_id}/{file_id}.jpg"

                                        # 直接通过 save_image 将带框图片保存到正式目录
                                        snapshot_path = storage.save_image(img, rel_path)
                                        alarm["snapshot_path"] = snapshot_path or rel_path
                            except Exception as e:
                                logger.error(
                                    f"处理告警截图上传失败: camera_id={camera_id}, path={local_path}, err={e}"
                                )

                        # 将告警消息写入 Redis 列表，由 app 侧 AlarmConsumer 负责入库与推送
                        push_alarm_to_queue_sync(alarm)
                        self.generated_alarms += 1
                    except Exception as e:
                        logger.error(f"告警转发线程循环异常: {e}")
                        time.sleep(0.5)
            finally:
                logger.info("告警转发线程退出")

        self._alarm_thread = threading.Thread(target=_worker, daemon=True)
        self._alarm_thread.start()

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
            if model_id:
                cfg = get_model_config(model_id)
                if cfg:
                    logger.info(f"Engine 读取模型配置: {cfg}")
        
        # 算法相关：从 Redis 读取最新算法配置
        if action in ("algorithm_add", "algorithm_update"):
            algorithm_id = data.get("algorithm_id")
            if algorithm_id:
                cfg = get_algorithm_config(algorithm_id)
                if cfg:
                    logger.info(f"Engine 读取算法配置: {cfg}")
        
        # 摄像头-算法绑定：从 Redis 读取最新绑定配置
        if action in ("camera_algorithm_add", "camera_algorithm_update"):
            camera_id = data.get("camera_id")
            algorithm_id = data.get("algorithm_id")
            if camera_id and algorithm_id:
                cfg = get_camera_algorithm_config(camera_id, algorithm_id)
                if cfg:
                    logger.info(f"Engine 读取摄像头算法配置: {cfg}")
            
            # 重新加载该摄像头的算法列表（简单做法：从 Redis scan 一遍该 camera_id 前缀）
            # 注意：这里仅更新配置与 Pipeline，不直接改变 InferenceService 的调度状态
            self._refresh_camera_algorithms_from_redis(camera_id)
            self._reconcile_camera_pipeline(camera_id)
        
        # 摄像头启动/停止：控制 Pipeline
        if action == "camera_start":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头启动命令: {camera_id}")
            self.live_started.add(camera_id)
            # 点播开始：默认 live_only；若同时启动推理且存在启用算法，则 full
            self._reconcile_camera_pipeline(camera_id)
        
        if action == "camera_stop":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头停止命令: {camera_id}")
            self.live_started.discard(camera_id)
            # 点播结束：不点播则只可能保留 inference_only（需要显式启动推理）
            self._reconcile_camera_pipeline(camera_id)

        if action == "camera_inference_start":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头推理启动命令: {camera_id}")
            self.inference_started.add(camera_id)
            self._refresh_camera_algorithms_from_redis(camera_id)
            self._reconcile_camera_pipeline(camera_id)
            # 通知 InferenceService 某个摄像头开始推理，由服务内部自行计数与扩缩容
            if self.inference_service:
                camera = self.cameras.get(camera_id)
                model_id = None
                if camera and camera.algorithms:
                    first_algo = camera.algorithms[0] or {}
                    model_id = first_algo.get("model_id")
                self.inference_service.on_camera_inference_start(camera_id, model_id or "")
            self._reconcile_inference_service()

        if action == "camera_inference_stop":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头推理停止命令: {camera_id}")
            self.inference_started.discard(camera_id)
            self._reconcile_camera_pipeline(camera_id)
            # 通知 InferenceService 某个摄像头停止推理
            if self.inference_service:
                self.inference_service.on_camera_inference_stop(camera_id)
            self._reconcile_inference_service()
    
    def health_check(self):
        """健康检查"""
        # 检查推理服务（仅当确实需要推理时才保证存在）
        if self._want_inference() and self.inference_service is None:
            logger.error("推理服务未启动，正在启动...")
            self._start_inference_service()
        
        # 检查所有 Pipeline（若线程异常退出，可按状态机重新拉起）
        if self.pipeline_service:
            for camera_id in list(self.cameras.keys()):
                # 简单策略：按状态机重新 reconcile 一遍，由 PipelineService 自己决定是否重建
                self._reconcile_camera_pipeline(camera_id)
        
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
        
        # 0. 读取“直播已启动”“推理已启动”集合
        self.live_started = get_live_started_camera_ids()
        self.inference_started = get_inference_started_camera_ids()
        
        # 1. 加载模型配置
        try:
            for model_id, cfg in scan_model_configs():
                self.models[model_id] = ModelConfig(
                    id=model_id,
                    name=cfg.get("name", model_id),
                    path=cfg.get("model_path", ""),
                    model_type=cfg.get("model_type", "yolo"),
                    # 统一按 (h, w) 存储，供 ONNX letterbox/预处理使用
                    input_size=(
                        int(cfg.get("input_height", 640)),
                        int(cfg.get("input_width", 640)),
                    ),
                    classes=list(cfg.get("classes") or []),
                    inference_time_ms=float(cfg.get("inference_ms", 30.0)),
                    gpu_memory_mb=int(cfg.get("gpu_memory_mb", 500)),
                )
        except Exception as e:
            logger.error(f"从 Redis 加载模型配置失败: {e}")
        
        # 2. 加载摄像头基础配置
        try:
            for camera_id, cfg in scan_camera_configs():
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
            for camera_id, algorithm_id, cfg in scan_camera_algorithm_bindings():
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
        
        # 4. Engine 重启恢复：若某摄像头心跳 Key 仍有效（前端在点播中），确保加入 live_started 以启动 Writer
        for camera_id in list(self.cameras.keys()):
            if is_camera_heartbeat_active(camera_id):
                self.live_started.add(camera_id)
                logger.info(f"Engine 重启恢复: 摄像头 {camera_id} 心跳有效，已加入 live_started")
        
        logger.info(
            f"从 Redis 加载配置完成: {len(self.cameras)} 个摄像头, "
            f"{len(self.models)} 个模型, live_started={len(self.live_started)}"
        )
    
    def _create_queues(self):
        """创建所有队列"""
        logger.info("创建队列...")
        
        # 为每个模型创建请求队列
        for model_id in self.models:
            self.request_queues[model_id] = MemoryQueue(maxsize=10)
            logger.debug(f"创建请求队列: {model_id}")
        
        # 为每个摄像头创建结果队列
        for camera_id in self.cameras:
            self.result_queues[camera_id] = MemoryQueue(maxsize=10)
            logger.debug(f"创建结果队列: {camera_id}")

    def _init_services(self):
        """初始化 InferenceService 与 PipelineService"""
        logger.info("初始化 Engine 服务层: InferenceService / PipelineService")
        # 推理服务：按当前 models_config 创建实例（需要时再 start）
        models_config = {
            model_id: {
                "id": model.id,
                "name": model.name,
                "path": model.path,
                "model_type": model.model_type,
                "input_size": model.input_size,
                "classes": model.classes,
            }
            for model_id, model in self.models.items()
        }
        self.inference_service = InferenceService(
            models_config=models_config,
            request_queues=self.request_queues,
            result_queues=self.result_queues,
        )
        # Pipeline 服务：持有 cameras/models 视图与队列映射
        self.pipeline_service = PipelineService(
            cameras=self.cameras,
            models=self.models,
            request_queues=self.request_queues,
            result_queues=self.result_queues,
            alarm_queue=self.alarm_queue,
        )
    
    def _start_inference_service(self):
        """启动推理服务（单进程内创建 Worker 线程）"""
        logger.info("启动推理服务...")
        
        # 准备配置（按模型维度）
        models_config = {
            model_id: {
                "id": model.id,
                "name": model.name,
                "path": model.path,
                "model_type": model.model_type,
                "input_size": model.input_size,
                "classes": model.classes,
            }
            for model_id, model in self.models.items()
        }
        
        self.inference_service = InferenceService(
            models_config=models_config,
            request_queues=self.request_queues,
            result_queues=self.result_queues,
        )
        self.inference_service.start()
        logger.info("推理服务已启动（线程池）")

        # Engine 重启场景：为已在 inference_started 集合中的摄像头补发一次绑定事件，
        # 由 InferenceService 内部自行统计模型使用情况并启动对应 Worker。
        for cam_id in list(self.inference_started):
            camera = self.cameras.get(cam_id)
            if not camera or not getattr(camera, "algorithms", None):
                continue
            first_algo = (camera.algorithms[0] or {}) if camera.algorithms else {}
            model_id = first_algo.get("model_id")
            if not model_id:
                continue
            try:
                self.inference_service.on_camera_inference_start(cam_id, model_id)
            except Exception as e:
                logger.error(f"为摄像头 {cam_id} 恢复推理绑定失败: {e}")
    
    def _start_pipelines(self):
        """
        启动所有 Pipeline。
        
        注意：这里只是根据当前 live_started / inference_started 计算“期望状态”，
        具体模式选择统一走 _reconcile_camera_pipeline，避免与运行时调度分叉。
        """
        logger.info("启动所有 Pipeline（按当前 live/inference 状态恢复）...")
        
        for camera_id in self.cameras.keys():
            # 对每个摄像头做一次状态对齐：进入 S0/S1/S2/S3 中的一个
            self._reconcile_camera_pipeline(camera_id)
    
    def _start_pipeline(self, camera_id: str, mode: str = "full"):
        """
        启动或切换单个 Pipeline（full / live_only / inference_only）。
        具体实现委托给 PipelineService。
        """
        if not self.pipeline_service:
            logger.error("PipelineService 未初始化，无法启动 Pipeline")
            return
        self.pipeline_service._ensure_pipeline(camera_id, mode)

    def _stop_pipeline(self, camera_id: str):
        """
        停止某个摄像头的 Pipeline，并清理相关状态。
        """
        if self.pipeline_service:
            self.pipeline_service.stop_pipeline(camera_id)

    def _refresh_camera_algorithms_from_redis(self, camera_id: str):
        """从 Redis 刷新某个摄像头的 algorithms 列表（仅读取该 camera_id 的绑定配置）"""
        camera = self.cameras.get(camera_id)
        if not camera:
            return
        try:
            camera.algorithms = scan_camera_algorithm_configs(camera_id)
        except Exception as e:
            logger.error(f"刷新摄像头算法配置失败: {camera_id}, {e}")

    def _reconcile_camera_pipeline(self, camera_id: str):
        """根据状态机将单路摄像头的目标模式委托给 PipelineService。"""
        camera = self.cameras.get(camera_id)
        if not camera or not self.pipeline_service:
            return
        has_algorithms = bool(camera.algorithms)
        is_live = camera_id in self.live_started
        is_infer = camera_id in self.inference_started
        self.pipeline_service.reconcile_camera(
            camera_id=camera_id,
            has_algorithms=has_algorithms,
            is_live=is_live,
            is_infer=is_infer,
        )

    def _want_inference(self) -> bool:
        """当前是否需要推理服务（任一路摄像头处于推理启动中且存在启用算法）"""
        for cam_id, cam in self.cameras.items():
            if cam_id in self.inference_started and cam.algorithms:
                return True
        return False

    def _reconcile_inference_service(self):
        """
        按需启动推理服务。

        约定：推理进程一旦启动就不再主动停止，只在 Engine 整体关闭时退出。
        资源控制通过队列为空 + Worker 空转来实现，避免频繁重启进程带来的队列/句柄问题。
        """
        want = self._want_inference()
        running = self.inference_service is not None and self.inference_service.running
        if want and not running:
            self._start_inference_service()
        # Worker 的扩缩容由 InferenceService 内部根据 on_camera_inference_start/stop 的记录自行处理，
        # 这里不再进行模型使用计数逻辑，保持 Scheduler 的职责简单。
    
    def add_camera(self, camera_config: CameraConfig):
        """动态添加摄像头"""
        camera_id = camera_config.id
        if camera_id in self.cameras:
            logger.warning(f"摄像头已存在: {camera_id}")
            return
        
        self.cameras[camera_id] = camera_config
        self.result_queues[camera_id] = MemoryQueue(maxsize=100)
        self._reconcile_camera_pipeline(camera_id)
        logger.info(f"已添加摄像头: {camera_config.name}")
    
    def remove_camera(self, camera_id: str):
        """动态移除摄像头"""
        if camera_id not in self.cameras:
            logger.warning(f"摄像头不存在: {camera_id}")
            return
        
        # 停止 Pipeline 并清理控制队列
        self._stop_pipeline(camera_id)
        # 清理资源
        del self.result_queues[camera_id]
        del self.cameras[camera_id]
        self.live_started.discard(camera_id)
        self.inference_started.discard(camera_id)
        
        logger.info(f"已移除摄像头: {camera_id}")
