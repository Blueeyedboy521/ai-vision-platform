# -*- coding: utf-8 -*-
"""
推理服务

高内聚封装：
- 负责模型维度的 Worker 线程创建/销毁
- 封装 request_queues/result_queues 的使用细节
Scheduler 只通过 InferenceService 暴露的方法进行操作，不直接管理 Worker。
"""
from typing import Dict, List, Optional
import math

from loguru import logger

from .worker import InferenceWorker


class InferenceService:
    """
    推理服务（单进程内的 Worker 管理器）
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
        # 记录“当前有哪些摄像头在使用哪个模型”，供内部自行计数与扩缩容
        self._camera_model: Dict[str, str] = {}  # camera_id -> model_id
        self.running: bool = False

    # ==== 生命周期 ====

    def start(self) -> None:
        """
        启动推理服务。

        注意：不在这里预创建所有模型的 Worker，
        具体哪些模型需要多少个 Worker 由 ensure_workers_for_models 按需控制。
        """
        if self.running:
            return
        logger.info("InferenceService 启动中...")
        self.running = True
        logger.info("InferenceService 启动完成，等待调度创建 Worker")

    def stop(self) -> None:
        """停止推理服务，优雅关闭所有 Worker 线程。"""
        if not self.running:
            return
        logger.info("InferenceService 停止中...")
        self.running = False

        for model_id, workers in list(self.workers.items()):
            for worker in workers:
                try:
                    worker.stop()
                except Exception as e:
                    logger.error(f"停止 Worker 失败: {worker.worker_id}, {e}")
        self.workers.clear()

        logger.info("InferenceService 已停止")

    # ==== Worker 管理接口 ====

    def on_camera_inference_start(self, camera_id: str, model_id: str) -> None:
        """
        通知 InferenceService：某个摄像头开始推理，绑定到指定模型。

        Scheduler 只需要在接收到“摄像头推理启动”事件时调用该方法，
        其余模型计数与 Worker 扩缩容逻辑全部在服务内部完成。
        """
        if not self.running:
            logger.warning("InferenceService 未启动，忽略 on_camera_inference_start 调用")
            return
        if not model_id:
            return

        # 1. 更新 camera -> model 映射（若原来绑定的是其他 model，可认为切换模型）
        prev_model = self._camera_model.get(camera_id)
        self._camera_model[camera_id] = model_id

        # 2. 基于最新映射重新统计每个模型被多少摄像头使用
        model_usage: Dict[str, int] = {}
        for cam, mid in self._camera_model.items():
            if not mid:
                continue
            model_usage[mid] = model_usage.get(mid, 0) + 1

        # 3. 调整各模型 Worker 数量
        self._reconcile_workers(model_usage)

        logger.info(
            f"InferenceService: 摄像头 {camera_id} 绑定模型 {model_id} 开始推理，"
            f"当前模型使用计数: {model_usage}"
        )

    def on_camera_inference_stop(self, camera_id: str) -> None:
        """
        通知 InferenceService：某个摄像头停止推理。

        服务内部会更新 camera -> model 映射并据此重新统计各模型使用情况，
        再决定是否回收或收紧对应模型的 Worker。
        """
        if not self.running:
            return

        # 1. 移除 camera -> model 绑定
        prev_model = self._camera_model.pop(camera_id, None)
        if not prev_model:
            return

        # 2. 基于最新映射重新统计每个模型被多少摄像头使用
        model_usage: Dict[str, int] = {}
        for cam, mid in self._camera_model.items():
            if not mid:
                continue
            model_usage[mid] = model_usage.get(mid, 0) + 1

        # 3. 调整各模型 Worker 数量
        self._reconcile_workers(model_usage)

        logger.info(
            f"InferenceService: 摄像头 {camera_id} 停止推理，"
            f"当前模型使用计数: {model_usage}"
        )

    # ==== 内部实现 ====

    def _reconcile_workers(self, model_usage: Dict[str, int]) -> None:
        """
        根据最新的 {model_id: 摄像头数量} 统计结果，统一调整所有模型的 Worker。
        """
        # 1. 回收已经不再被任何摄像头使用的模型 Worker
        active_model_ids = set(model_usage.keys())
        for model_id in list(self.workers.keys()):
            if model_id not in active_model_ids:
                workers = self.workers.get(model_id) or []
                if workers:
                    logger.info(
                        f"InferenceService: 模型 {model_id} 当前无摄像头使用，停止全部 {len(workers)} 个 Worker"
                    )
                    for worker in workers:
                        try:
                            worker.stop()
                        except Exception as e:
                            logger.error(f"停止 Worker 失败: {worker.worker_id}, {e}")
                self.workers.pop(model_id, None)

        # 2. 为仍在使用的模型按需扩缩容
        for model_id, camera_count in model_usage.items():
            cfg = self.models_config.get(model_id)
            if not cfg:
                continue
            target_count = self._calc_target_workers(camera_count)
            self._ensure_workers_for_model(model_id, cfg, target_count=target_count)

    def _calc_target_workers(self, camera_count: int) -> int:
        """
        根据使用该模型的摄像头数量计算期望 Worker 数量。

        目前策略（可后续抽到配置）：
            - 每个模型至少 1 个 Worker（只要有摄像头使用）；
            - 每 N 路摄像头增加 1 个 Worker，上限为 MAX_WORKERS_PER_MODEL。
        """
        if camera_count <= 0:
            return 0

        CAMERAS_PER_WORKER = 4
        MAX_WORKERS_PER_MODEL = 4

        return max(
            1,
            min(
                MAX_WORKERS_PER_MODEL,
                math.ceil(camera_count / CAMERAS_PER_WORKER),
            ),
        )

    def _ensure_workers_for_model(self, model_id: str, cfg: dict, target_count: int) -> None:
        """
        确保指定模型的 Worker 数量与 target_count 一致：
            - target_count == 0: 停止并清理所有 Worker；
            - target_count > 当前数量: 创建并启动新的 Worker；
            - target_count < 当前数量: 停止多余的 Worker。
        """
        request_queue = self.request_queues.get(model_id)
        if not request_queue:
            logger.warning(f"模型 {model_id} 没有对应的请求队列")
            return

        current_workers = list(self.workers.get(model_id) or [])

        # 收紧到 0：全部关闭
        if target_count <= 0:
            if current_workers:
                logger.info(
                    f"InferenceService: 模型 {model_id} 目标 Worker 数为 0，停止全部 {len(current_workers)} 个 Worker"
                )
                for worker in current_workers:
                    try:
                        worker.stop()
                    except Exception as e:
                        logger.error(f"停止 Worker 失败: {worker.worker_id}, {e}")
            self.workers.pop(model_id, None)
            return

        # 若当前数量大于目标数量，先收紧多余的 Worker
        if len(current_workers) > target_count:
            to_stop = current_workers[target_count:]
            logger.info(
                f"InferenceService: 模型 {model_id} 收紧 Worker 数量: {len(current_workers)} -> {target_count}"
            )
            for worker in to_stop:
                try:
                    worker.stop()
                except Exception as e:
                    logger.error(f"停止 Worker 失败: {worker.worker_id}, {e}")
            current_workers = current_workers[:target_count]

        # 若当前数量小于目标数量，补足缺失的 Worker
        workers: List[InferenceWorker] = list(current_workers)
        while len(workers) < target_count:
            idx = len(workers)
            worker = InferenceWorker(
                worker_id=f"{model_id}_worker_{idx}",
                model_id=model_id,
                model_path=cfg.get("path", ""),
                model_type=cfg.get("model_type", "yolo"),
                input_size=cfg.get("input_size", (640, 640)),
                request_queue=request_queue,
                result_queues=self.result_queues,
                classes=cfg.get("classes"),
                class_algo_map=cfg.get("class_algo_map"),
            )
            worker.start()
            workers.append(worker)
            logger.info(f"InferenceService: 为模型 {model_id} 启动 Worker {worker.worker_id}")

        self.workers[model_id] = workers