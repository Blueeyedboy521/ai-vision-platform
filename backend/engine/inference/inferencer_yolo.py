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


def _read_classes_from_redis(model_id: str) -> Optional[List[str]]:
    """从 Redis 模型配置读取 classes，用于覆盖或补充模型自带 names"""
    try:
        from common.redis import get_redis_client
        from common.redis.channels import RedisKeys
        client = get_redis_client()
        client.connect_sync()
        raw = client.sync_client.get(RedisKeys.model_config(model_id))
        if not raw:
            return None
        cfg = json.loads(raw)
        classes = cfg.get("classes")
        if isinstance(classes, list) and len(classes) > 0:
            return [str(c) for c in classes]
        return None
    except Exception as e:
        logger.debug(f"从 Redis 读取模型 classes 失败: model_id={model_id}, err={e}")
        return None


class UltralyticsYoloInferencer:
    """ultralytics YOLO 推理器：load() 加载模型并可选从 Redis 覆盖 class names，infer() 返回 InferenceResult"""

    def __init__(self, model_id: str, model_path: str, device: str):
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
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

        # 可选：用 Redis 配置的 classes 覆盖
        redis_classes = _read_classes_from_redis(self.model_id)
        if redis_classes:
            self._names = {i: name for i, name in enumerate(redis_classes)}
            logger.info(f"YOLO 使用 Redis 配置的 classes: model_id={self.model_id}, count={len(redis_classes)}")

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
                detections.append({
                    "class_id": class_id,
                    "class_name": str(self._names.get(class_id, class_id)),
                    "confidence": conf,
                    "bbox": bbox,
                })
        inference_time_ms = (time.perf_counter() - start) * 1000
        return InferenceResult(
            request_id=request_id,
            camera_id=camera_id,
            frame_id=frame_id,
            detections=detections,
            inference_time_ms=inference_time_ms,
            timestamp=time.time(),
        )

    def draw_boxes(self, result: InferenceResult) -> Any:
        """在 result.frame 上绘制 result.detections 的框与标签"""
        import cv2
        if result.frame is None:
            return None
        drawn = result.frame.copy()
        for det in result.detections:
            bbox = det.get("bbox", [])
            if len(bbox) < 4:
                continue
            x1, y1, x2, y2 = [int(round(v)) for v in bbox[:4]]
            class_name = det.get("class_name", "")
            confidence = det.get("confidence", 0)
            color = (0, 255, 0)  # BGR 绿
            cv2.rectangle(drawn, (x1, y1), (x2, y2), color, 2)
            label = f"{class_name} {confidence:.2f}"
            cv2.putText(drawn, label, (x1, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return drawn

    def close(self) -> None:
        self._model = None
