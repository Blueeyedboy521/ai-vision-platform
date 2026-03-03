# -*- coding: utf-8 -*-
"""
PipelineService

高内聚封装每路摄像头 Pipeline 的创建/销毁与模式切换逻辑。

职责：
- 持有 camera_id -> Pipeline 实例映射
- 根据 Scheduler 传入的状态（has_algorithms / is_live / is_infer）决定目标模式
- 调用 Pipeline.start/stop/set_mode，内部管理 StreamReader/StreamWriter/ResultHandler 线程
"""
from typing import Dict, Optional

from loguru import logger

from engine.queue.memory_queue import MemoryQueue
from .pipeline import Pipeline, PipelineConfig


class PipelineService:
    """
    Pipeline 管理服务
    """

    def __init__(
        self,
        cameras: Dict[str, object],
        models: Dict[str, object],
        request_queues: Dict[str, MemoryQueue],
        result_queues: Dict[str, MemoryQueue],
        alarm_queue: Optional[object] = None,
    ):
        """
        Args:
            cameras: Scheduler 维护的摄像头配置 dict（camera_id -> CameraConfig）
            models: Scheduler 维护的模型配置 dict（model_id -> ModelConfig）
            request_queues: 模型维度的请求队列
            result_queues: 摄像头维度的结果队列
        """
        self.cameras = cameras
        self.models = models
        self.request_queues = request_queues
        self.result_queues = result_queues

        # Engine 级别的告警队列（由 Scheduler 创建），ResultHandler 清洗后的告警通过此队列异步交给调度器写 Redis。
        self.alarm_queue = alarm_queue

        self.pipelines: Dict[str, Pipeline] = {}
        self.pipeline_modes: Dict[str, str] = {}

    # ==== 对外接口 ====

    def reconcile_camera(
        self,
        camera_id: str,
        has_algorithms: bool,
        is_live: bool,
        is_infer: bool,
    ) -> None:
        """
        按 S0-S3 状态机为单路摄像头调整 Pipeline，幂等化处理：
        - S0: 不起 Pipeline（live=false, infer=false）
        - S1: live_only（仅推流）
        - S2: inference_only（仅推理）
        - S3: full（推流 + 推理）
        若目标模式与当前模式一致，则不做任何操作。
        """
        camera = self.cameras.get(camera_id)
        if not camera:
            return

        # 计算目标模式（None 代表 S0：不需要 Pipeline）
        if not is_live and not is_infer:
            target_mode: Optional[str] = None
        elif is_live and not is_infer:
            # S1：只播放、不推理 → live_only
            target_mode = "live_only"
        elif is_infer and not is_live:
            # S2：只推理、不播放
            if not has_algorithms:
                # 推理开启但没有算法配置，本质上等价于 S0
                target_mode = None
            else:
                target_mode = "inference_only"
        else:
            # S3：既播放又推理
            if not has_algorithms:
                # 播放+推理开启但无算法配置，仅启动推流，相当于 S1
                target_mode = "live_only"
            else:
                target_mode = "full"

        # 当前模式（None 代表没有运行中的 Pipeline）
        current_mode: Optional[str] = None
        existing = self.pipelines.get(camera_id)
        if existing and existing.running:
            current_mode = self.pipeline_modes.get(camera_id)

        # 若目标模式与当前模式一致，则不做任何操作（完全幂等）
        if target_mode == current_mode:
            return

        # S0：目标为不需要 Pipeline，则停止之
        if target_mode is None:
            logger.info(f"摄像头{camera_id} 目标模式为 S0（不播放且不推理），停止 Pipeline")
            self.stop_pipeline(camera_id)
            return

        # 其余情况交给内部 _ensure_pipeline 按目标模式启动/切换
        self._ensure_pipeline(camera_id, target_mode)

    def stop_pipeline(self, camera_id: str) -> None:
        """停止某个摄像头的 Pipeline，并清理状态。"""
        pipeline = self.pipelines.get(camera_id)
        if pipeline and pipeline.running:
            logger.info(f"PipelineService 停止 Pipeline: {camera_id}")
            try:
                pipeline.stop()
            except Exception as e:
                logger.error(f"Pipeline {camera_id} 停止失败: {e}")
        self.pipelines.pop(camera_id, None)
        self.pipeline_modes.pop(camera_id, None)

    def stop_all(self) -> None:
        """停止所有 Pipeline。供 Scheduler.stop 调用。"""
        for camera_id in list(self.pipelines.keys()):
            self.stop_pipeline(camera_id)

    # ==== 内部实现 ====

    def _ensure_pipeline(self, camera_id: str, mode: str) -> None:
        """确保指定摄像头的 Pipeline 以目标模式运行。"""
        camera = self.cameras.get(camera_id)
        if not camera:
            logger.error(f"PipelineService: 摄像头配置不存在: {camera_id}")
            return
        if not camera.rtsp_url:
            logger.warning(f"PipelineService: 摄像头{camera_id} RTSP 地址为空，不启动 Pipeline")
            self.stop_pipeline(camera_id)
            return

        # 若已存在 Pipeline 且模式一致，则不重复启动
        existing = self.pipelines.get(camera_id)
        if existing and existing.running:
            current_mode = self.pipeline_modes.get(camera_id)
            if current_mode == mode:
                return
            logger.info(f"PipelineService: 切换 Pipeline 模式: {camera_id}, {current_mode} -> {mode}")
            existing.set_mode(mode)
            self.pipeline_modes[camera_id] = mode
            return

        # 构造 PipelineConfig
        pipeline_config = PipelineConfig(
            camera_id=camera.id,
            camera_name=camera.name,
            rtsp_url=camera.rtsp_url,
            fps=camera.fps,
            skip_frames=camera.skip_frames,
            algorithms=camera.algorithms if mode != "live_only" else [],
            mode=mode,
            draw_model=self._build_draw_model(camera),
        )

        # 获取/创建相关队列
        request_queue: Optional[MemoryQueue] = None
        if mode in ("full", "inference_only") and camera.algorithms:
            model_id = camera.algorithms[0].get("model_id")
            if model_id:
                if model_id not in self.request_queues:
                    logger.info(f"PipelineService: 为模型{model_id} 创建请求队列（首次启用算法）")
                    self.request_queues[model_id] = MemoryQueue(maxsize=100)
                request_queue = self.request_queues.get(model_id)

        result_queue = self.result_queues.get(camera_id)
        if result_queue is None:
            logger.info(f"PipelineService: 为摄像头{camera_id} 创建结果队列（首次进入推理/推流状态）")
            result_queue = MemoryQueue(maxsize=100)
            self.result_queues[camera_id] = result_queue

        pipeline_obj = Pipeline(
            config=pipeline_config,
            request_queue=request_queue,
            result_queue=result_queue,
            alarm_queue=self.alarm_queue,
        )
        pipeline_obj.start()

        self.pipelines[camera_id] = pipeline_obj
        self.pipeline_modes[camera_id] = mode
        logger.info(f"PipelineService: Pipeline 已启动: {camera.name} (mode={mode})")

    def _build_draw_model(self, camera) -> Optional[dict]:
        """构造绘框用的模型信息（供 Pipeline 内 build_inferencer(for_draw=True) 使用）。"""
        if not camera.algorithms:
            return None
        model_id = camera.algorithms[0].get("model_id")
        model = self.models.get(model_id) if model_id else None
        if not model:
            return None
        return {
            "model_type": model.model_type,
            "model_id": model.id,
            "model_path": model.path,
            "device": "cpu",
            "input_size": model.input_size or (640, 640),
        }

