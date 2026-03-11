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
    get_camera_config,
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


def _model_algorithms_to_class_map(algorithms: List[dict]) -> Dict[str, dict]:
    """从 model config 的 algorithms 列表构造 {target_class -> {id, code, name}}，与 engine.redis.get_model_algorithms_class_map 逻辑一致。"""
    if not algorithms:
        return {}
    out: Dict[str, dict] = {}
    for item in algorithms if isinstance(algorithms, list) else []:
        if not isinstance(item, dict):
            continue
        algo_id = str(item.get("id") or "")
        code = str(item.get("code") or "")
        name = str(item.get("name") or "")
        targets = item.get("target_classes") or []
        if not algo_id or not code or not isinstance(targets, list):
            continue
        for t in targets:
            if t is not None:
                out[str(t)] = {"id": algo_id, "code": code, "name": name}
    return out


@dataclass
class ModelConfig:
    """模型配置"""
    id: str
    name: str
    path: str
    model_type: str  # yolo, onnx, tensorrt
    input_size: tuple = (640, 640)
    classes: List[str] = field(default_factory=list)
    algorithms: List[dict] = field(default_factory=list)  # 用于生成 class_algo_map，不直接给推理器
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

        # 本地截图上传去重与回收（多算法同帧复用）：
        # key: local_snapshot_path
        # value: {"snapshot_path": str, "total": int, "seen": int}
        uploaded_snapshots: Dict[str, dict] = {}

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

                        # 将本地截图上传到 Storage 的正式目录，并生成缩略图（列表/冒泡使用 variant=thumb）。
                        # 同一 local_snapshot_path 可能被多条告警引用：用 ref_total 做去重与回收。
                        camera_id = str(alarm.get("camera_id") or "")
                        ts_str = str(alarm.get("timestamp") or "")
                        local_path = alarm.pop("local_snapshot_path", None)
                        ref_total_raw = alarm.get("local_snapshot_ref_total") or 1
                        try:
                            ref_total = int(ref_total_raw)
                        except Exception:
                            ref_total = 1
                        ref_total = max(1, ref_total)

                        if local_path and camera_id:
                            try:
                                import os
                                from datetime import datetime
                                from common.storage import get_storage
                                from common.media.image import (
                                    ThumbnailOptions,
                                    build_thumb_key,
                                    make_thumbnail_jpeg_from_file,
                                )

                                entry = uploaded_snapshots.get(local_path)
                                if entry is None:
                                    if not os.path.exists(local_path):
                                        logger.error(f"本地告警截图不存在: {local_path}")
                                    else:
                                        storage = get_storage()
                                        try:
                                            dt = datetime.fromisoformat(ts_str)
                                        except Exception:
                                            dt = datetime.now()
                                        date_path = dt.strftime("%Y/%m/%d")
                                        file_id = str(int(dt.timestamp() * 1000))
                                        origin_key = f"alarm/{date_path}/{camera_id}/{file_id}.jpg"

                                        # 上传原图（不在 Engine 绘框）
                                        try:
                                            with open(local_path, "rb") as f:
                                                origin_bytes = f.read()
                                            storage.save_file(origin_bytes, origin_key, content_type="image/jpeg")
                                            alarm["snapshot_path"] = origin_key
                                        except Exception as e:
                                            logger.error(f"上传告警原图失败: {local_path}, err={e}")

                                        # 生成并上传缩略图（失败不影响主流程）
                                        try:
                                            thumb_bytes = make_thumbnail_jpeg_from_file(
                                                local_path, ThumbnailOptions(max_side=320, quality=70)
                                            )
                                            if thumb_bytes:
                                                thumb_key = build_thumb_key(origin_key)
                                                storage.save_file(thumb_bytes, thumb_key, content_type="image/jpeg")
                                        except Exception as e:
                                            logger.warning(f"上传告警缩略图失败(可忽略): {e}")

                                        uploaded_snapshots[local_path] = {
                                            "snapshot_path": alarm.get("snapshot_path"),
                                            "total": ref_total,
                                            "seen": 1,
                                        }
                                        entry = uploaded_snapshots[local_path]
                                else:
                                    # 已经上传过该本地截图：直接复用远程路径
                                    if entry.get("snapshot_path"):
                                        alarm["snapshot_path"] = entry["snapshot_path"]
                                    entry["seen"] += 1

                                # 判断是否所有引用都已消费完，若是则回收本地文件与缓存
                                if entry and entry["seen"] >= entry["total"]:
                                    try:
                                        if os.path.exists(local_path):
                                            os.remove(local_path)
                                    except Exception as e:
                                        logger.warning(f"删除本地告警截图失败(可忽略): {e}")
                                    finally:
                                        uploaded_snapshots.pop(local_path, None)
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
        模型/摄像头/算法增改时从 Redis 刷新运行时配置；启停推理/直播时再拉取最新配置并控制 Pipeline。
        """
        if not action:
            return
        
        logger.info(f"Engine 收到配置事件: {action} - {data}")
        
        # 模型增改：从 Redis 刷新该模型配置到 self.models，并确保 request_queues 存在
        if action in ("model_add", "model_update"):
            model_id = data.get("model_id")
            if model_id:
                self._apply_model_config_from_redis(model_id)
                logger.info(f"Engine 已刷新模型配置: {model_id}")

        # 摄像头增改：从 Redis 刷新该摄像头基础配置与算法绑定到 self.cameras
        if action in ("camera_add", "camera_update"):
            camera_id = data.get("camera_id")
            if camera_id:
                self._refresh_camera_from_redis(camera_id)
                logger.info(f"Engine 已刷新摄像头配置: {camera_id}")
        
        # 算法增改：刷新所有摄像头的算法列表（来自 Redis 的摄像头-算法绑定会反映算法变更）
        if action in ("algorithm_add", "algorithm_update"):
            self._refresh_all_cameras_algorithms_from_redis()
            logger.info("Engine 已刷新所有摄像头的算法配置")
        
        # 摄像头-算法绑定增改：刷新该摄像头的算法配置
        if action in ("camera_algorithm_add", "camera_algorithm_update"):
            camera_id = data.get("camera_id")
            if camera_id:
                self._refresh_camera_from_redis(camera_id)
                logger.info(f"Engine 已刷新摄像头算法绑定: {camera_id}")
        
        # 摄像头启动/停止：先从 Redis 拉取最新摄像头与算法配置，再控制 Pipeline
        if action == "camera_start":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头启动命令: {camera_id}")
            self._refresh_camera_from_redis(camera_id)
            self.live_started.add(camera_id)
            # 点播开始：默认 live_only；若同时启动推理且存在启用算法，则 full
            self._reconcile_camera_pipeline(camera_id)
        
        if action == "camera_stop":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头停止命令: {camera_id}")
            self._refresh_camera_from_redis(camera_id)
            self.live_started.discard(camera_id)
            # 点播结束：不点播则只可能保留 inference_only（需要显式启动推理）
            self._reconcile_camera_pipeline(camera_id)

        if action == "camera_inference_start":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头推理启动命令: {camera_id}")
            self._refresh_camera_from_redis(camera_id)
            self.inference_started.add(camera_id)
            self._reconcile_camera_pipeline(camera_id)
            # 通知 InferenceService 某个摄像头开始推理，由服务内部自行计数与扩缩容
            if self.inference_service:
                camera = self.cameras.get(camera_id)
                if camera and camera.algorithms:
                    # 同一摄像头可能绑定多个模型：为每个模型分别绑定一次
                    model_ids = []
                    for algo in camera.algorithms:
                        mid = (algo or {}).get("model_id")
                        if mid and mid not in model_ids:
                            model_ids.append(str(mid))
                    for mid in model_ids:
                        self.inference_service.on_camera_inference_start(camera_id, mid)
            self._reconcile_inference_service()

        if action == "camera_inference_stop":
            camera_id = data.get("camera_id")
            if not camera_id:
                return
            logger.info(f"Engine 收到摄像头推理停止命令: {camera_id}")
            self._refresh_camera_from_redis(camera_id)
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
                    algorithms=list(cfg.get("algorithms") or []),
                    inference_time_ms=float(cfg.get("inference_ms", 30.0)),
                    gpu_memory_mb=int(cfg.get("gpu_memory_mb", 500)),
                )
        except Exception as e:
            logger.error(f"从 Redis 加载模型配置失败: {e}")

        # 2/3/4 合并：收集摄像头 ID → 逐个从 Redis 刷新摄像头基础配置 + 算法配置 + skip_frames，并做心跳恢复
        camera_ids: set[str] = set()
        try:
            for camera_id, _cfg in scan_camera_configs():
                if camera_id:
                    camera_ids.add(camera_id)
        except Exception as e:
            logger.error(f"从 Redis 扫描摄像头配置失败: {e}")
        try:
            for camera_id, _algorithm_id, _cfg in scan_camera_algorithm_bindings():
                if camera_id:
                    camera_ids.add(camera_id)
        except Exception as e:
            logger.error(f"从 Redis 扫描摄像头算法绑定失败: {e}")

        for camera_id in list(camera_ids):
            self._refresh_camera_from_redis(camera_id)
            # Engine 重启恢复：若某摄像头心跳 Key 仍有效（前端在点播中），确保加入 live_started 以启动 Writer
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
                "class_algo_map": _model_algorithms_to_class_map(model.algorithms),
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
        
        # 准备配置（按模型维度），含 class_algo_map 供推理器使用，不再在推理器内读 Redis
        models_config = {
            model_id: {
                "id": model.id,
                "name": model.name,
                "path": model.path,
                "model_type": model.model_type,
                "input_size": model.input_size,
                "classes": model.classes,
                "class_algo_map": _model_algorithms_to_class_map(model.algorithms),
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
            try:
                model_ids = []
                for algo in camera.algorithms:
                    mid = (algo or {}).get("model_id")
                    if mid and mid not in model_ids:
                        model_ids.append(str(mid))
                for mid in model_ids:
                    self.inference_service.on_camera_inference_start(cam_id, mid)
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
    
    def _stop_pipeline(self, camera_id: str):
        """
        停止某个摄像头的 Pipeline，并清理相关状态。
        """
        if self.pipeline_service:
            self.pipeline_service.stop_pipeline(camera_id)

    def _apply_model_config_from_redis(self, model_id: str) -> None:
        """从 Redis 读取模型配置并更新 self.models，新模型时创建 request_queue。"""
        cfg = get_model_config(model_id)
        if not cfg or not cfg.get("is_enabled", True):
            return
        self.models[model_id] = ModelConfig(
            id=model_id,
            name=cfg.get("name", model_id),
            path=cfg.get("model_path", ""),
            model_type=cfg.get("model_type", "yolo"),
            input_size=(
                int(cfg.get("input_height", 640)),
                int(cfg.get("input_width", 640)),
            ),
            classes=list(cfg.get("classes") or []),
            algorithms=list(cfg.get("algorithms") or []),
            inference_time_ms=float(cfg.get("inference_ms", 30.0)),
            gpu_memory_mb=int(cfg.get("gpu_memory_mb", 500)),
        )
        if model_id not in self.request_queues:
            self.request_queues[model_id] = MemoryQueue(maxsize=10)

    def _refresh_all_cameras_algorithms_from_redis(self) -> None:
        """刷新所有摄像头的算法列表（来自 Redis），并重算各摄像头的 skip_frames。"""
        for camera_id in list(self.cameras.keys()):
            camera = self.cameras.get(camera_id)
            if not camera:
                continue
            try:
                camera.algorithms = scan_camera_algorithm_configs(camera_id)
            except Exception as e:
                logger.error(f"刷新摄像头算法配置失败: {camera_id}, {e}")
                continue
            if camera.algorithms:
                intervals = [
                    (a.get("config") or {}).get("inference_interval_sec", 5)
                    for a in camera.algorithms
                ]
                min_interval = min(intervals) if intervals else 5
                camera.skip_frames = max(0, int(camera.fps * min_interval) - 1)

    def _refresh_camera_from_redis(self, camera_id: str):
        """启停推理/直播时从 Redis 拉取该摄像头最新基础配置与算法配置，并回写 self.cameras。"""
        cfg = get_camera_config(camera_id)
        # 允许“只有算法绑定但没有 camera_config”的占位摄像头：先确保 self.cameras[camera_id] 存在
        if camera_id not in self.cameras:
            self.cameras[camera_id] = CameraConfig(
                id=camera_id,
                name=(cfg.get("name", camera_id) if cfg else camera_id),
                rtsp_url=(cfg.get("rtsp_url", "") if cfg else ""),
                fps=int((cfg.get("fps", 25) if cfg else 25)),
                skip_frames=0,
                algorithms=[],
            )
        if camera_id not in self.result_queues:
            self.result_queues[camera_id] = MemoryQueue(maxsize=10)

        # 若存在 camera_config，则覆盖更新基础字段
        if cfg:
            cam = self.cameras[camera_id]
            cam.name = cfg.get("name", cam.name)
            cam.rtsp_url = cfg.get("rtsp_url", cam.rtsp_url)
            cam.fps = int(cfg.get("fps", cam.fps))
            # 摄像头级识别间隔(秒)，用于统一控制抽帧频率；若未配置则默认 5 秒
            interval_sec = int(cfg.get("inference_interval_sec", 5))
            cam.skip_frames = max(0, int(cam.fps * interval_sec) - 1)
        camera = self.cameras.get(camera_id)
        if not camera:
            return
        try:
            camera.algorithms = scan_camera_algorithm_configs(camera_id)
        except Exception as e:
            logger.error(f"刷新摄像头算法配置失败: {camera_id}, {e}")
            return

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
