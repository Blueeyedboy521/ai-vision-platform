# -*- coding: utf-8 -*-
"""
Ultralytics YOLO 推理实现

- load()：从 Redis 读取 model:config:{model_id} 的 classes 做可选覆盖，加载 YOLO 模型
- infer()：返回 InferenceResult(detections=...)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from .inferencer import InferenceResult
from .draw_utils import draw_detections_inplace


class UltralyticsYoloInferencer:
    """ultralytics YOLO 推理器：load() 加载模型，classes/class_algo_map 由 Scheduler 传入，不再读 Redis"""

    def __init__(
        self,
        model_id: str,
        model_path: str,
        device: str,
        classes: Optional[List[str]] = None,
        class_algo_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self._classes = classes  # 由 Scheduler 传入，不再从 Redis 读
        self._class_algo_map = class_algo_map or {}
        self._model = None
        self._names: Dict[int, str] = {}

    def load(self) -> None:
        """加载 YOLO 模型（如需则先下载）；可选从 Redis model:config 读取 classes 覆盖模型 names"""
        import os
        from .inferencer import MODEL_DOWNLOAD_PATH
        if os.path.isabs(self.model_path) and os.path.exists(self.model_path):
            path_to_load = self.model_path
        else:
            local_path = os.path.join(MODEL_DOWNLOAD_PATH, self.model_path)
            if not os.path.exists(local_path):
                from common.storage import get_storage
                logger.info(f"YOLO 模型文件不存在，开始下载: {self.model_path} -> {local_path}")
                os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
                get_storage().download_file(self.model_path, local_path)
            path_to_load = local_path

        try:
            from ultralytics import YOLO
        except Exception as e:
            raise RuntimeError("请先安装 ultralytics: pip install ultralytics") from e

        self._model = YOLO(path_to_load)
        self._names = getattr(self._model, "names", {}) or {}
        if not isinstance(self._names, dict):
            self._names = {i: str(v) for i, v in enumerate(self._names)} if self._names else {}

        # 使用 Scheduler 传入的 classes 覆盖（不再读 Redis）
        if self._classes:
            self._names = {i: name for i, name in enumerate(self._classes)}
            logger.info(f"YOLO 使用配置的 classes: model_id={self.model_id}, count={len(self._classes)}")
        # class_algo_map 已在 __init__ 中由 Scheduler 传入

        try:
            self._model.to(self.device)
        except Exception as e:
            logger.warning(f"ultralytics YOLO 切换到 {self.device} 失败，回退 cpu: {e}")
            try:
                self._model.to("cpu")
            except Exception:
                pass
        logger.info(f"YOLO 模型加载完成: {self.model_path}")

    def infer(self, params: Dict[str, Any]) -> InferenceResult:
        import time
        frame = params.get("frame")
        request_id = params.get("request_id", "")
        camera_id = params.get("camera_id", "")
        frame_id = int(params.get("frame_id", 0))
        ts = float(params.get("timestamp", time.time()))

        if frame is None:
            return InferenceResult(
                request_id=request_id,
                camera_id=camera_id,
                frame_id=frame_id,
                detections=[],
                inference_time_ms=0.0,
                timestamp=ts,
                frame=None,
            )

        start = time.perf_counter()
        results = self._model.predict(frame, verbose=False)
        detections: List[Dict[str, Any]] = []

        for r in results or []:
            boxes = getattr(r, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                try:
                    class_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    bbox = box.xyxy[0].tolist()
                except Exception:
                    continue
                class_name = str(self._names.get(class_id, class_id))
                algo_id: Optional[str] = None
                # 按 target_class（class_name）在模型算法映射中查找对应算法 id
                if self._class_algo_map:
                    info = self._class_algo_map.get(class_name) or {}
                    algo_id = str(info.get("id") or "") or None

                det: Dict[str, Any] = {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": conf,
                    "bbox": bbox,
                }
                if algo_id:
                    det["algorithm_id"] = algo_id
                detections.append(det)
        inference_time_ms = (time.perf_counter() - start) * 1000
        return InferenceResult(
            request_id=request_id,
            camera_id=camera_id,
            frame_id=frame_id,
            detections=detections,
            inference_time_ms=inference_time_ms,
            timestamp=time.time(),
            frame=frame,
        )

    def draw_boxes(self, result: InferenceResult) -> Any:
        """在 result.frame 上绘制 result.detections 的框与标签"""
        if result.frame is None:
            return None
        drawn = result.frame.copy()
        return draw_detections_inplace(drawn, result.detections)

    def close(self) -> None:
        self._model = None
