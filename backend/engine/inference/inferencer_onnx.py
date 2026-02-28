# -*- coding: utf-8 -*-
"""
ONNX YOLO11 推理实现

- load()：下载模型到本地、从 Redis 读取 model:config 的 classes，创建 ONNX Session
- infer()：返回 InferenceResult(detections=...)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Set

from loguru import logger

from .inferencer import InferenceResult, MODEL_DOWNLOAD_PATH
from .draw_utils import draw_detections_inplace

def _read_classes_from_redis(model_id: str) -> Optional[Dict[str, Dict[str, str]]]:
    """
    从 Redis 读取模型配置的 algorithms，并构造 {target_class -> {code, name}} 的映射。
    """
    try:
        from common.redis import get_redis_client
        from common.redis.channels import RedisKeys

        client = get_redis_client()
        client.connect_sync()
        r = client.sync_client

        raw_model = r.get(RedisKeys.model_config(model_id))
        if not raw_model:
            return None
        try:
            cfg_model = json.loads(raw_model)
        except Exception:
            logger.warning(f"ONNX 解析模型配置失败: model_id={model_id}")
            return None
        algorithms_cfg = cfg_model.get("algorithms")
        if not isinstance(algorithms_cfg, list):
            return None

        class_map: Dict[str, Dict[str, str]] = {}
        for item in algorithms_cfg:
            # 预期结构: {"id": algo_id, "name": ..., "code": algo_code, "target_classes": [...]}
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or "")
            name = str(item.get("name") or "")
            targets = item.get("target_classes") or []
            if not code or not isinstance(targets, list):
                continue
            for t in targets:
                if t is None:
                    continue
                key = str(t)
                class_map[key] = {"code": code, "name": name}

        if class_map:
            logger.info(
                f"ONNX 从 model:config.algorithms 构造 target_class->{{code,name}} 映射: model_id={model_id}, count={len(class_map)}"
            )
            return class_map
        return None
    except Exception as e:
        logger.warning(f"从 Redis 读取模型 classes 失败: model_id={model_id}, err={e}")
        return None


def _safe_class_name(class_id: int, class_names: Optional[List[str]]) -> str:
    if class_names and 0 <= class_id < len(class_names):
        return str(class_names[class_id])
    return str(class_id)


@dataclass(frozen=True)
class _OnnxSessionInfo:
    input_name: str
    input_hw: Tuple[int, int]
    output_names: List[str]
    providers: List[str]


def _onnx_create_session(model_path: str, device: str, input_hw_hint: Optional[Tuple[int, int]]) -> tuple:
    import onnxruntime as ort
    providers: List[str] = []
    if device.lower().startswith("cuda"):
        providers.append("CUDAExecutionProvider")
    providers.append("CPUExecutionProvider")
    sess = ort.InferenceSession(model_path, providers=providers)
    input_meta = sess.get_inputs()[0]
    h, w = 640, 640
    shape = input_meta.shape
    if isinstance(shape, (list, tuple)) and len(shape) >= 4:
        maybe_h, maybe_w = shape[-2], shape[-1]
        if isinstance(maybe_h, int) and isinstance(maybe_w, int) and maybe_h > 0 and maybe_w > 0:
            h, w = int(maybe_h), int(maybe_w)
        elif input_hw_hint:
            h, w = int(input_hw_hint[0]), int(input_hw_hint[1])
    elif input_hw_hint:
        h, w = int(input_hw_hint[0]), int(input_hw_hint[1])
    info = _OnnxSessionInfo(
        input_name=input_meta.name,
        input_hw=(h, w),
        output_names=[o.name for o in sess.get_outputs()],
        providers=sess.get_providers(),
    )
    return sess, info


def _letterbox(img_bgr, new_shape: Tuple[int, int], color=(114, 114, 114)):
    import cv2
    new_h, new_w = new_shape
    h, w = img_bgr.shape[:2]
    r = min(new_w / w, new_h / h)
    resized_w = int(round(w * r))
    resized_h = int(round(h * r))
    resized = cv2.resize(img_bgr, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)
    dw = (new_w - resized_w) / 2
    dh = (new_h - resized_h) / 2
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    out = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return out, r, (left, top)


def _preprocess_bgr_to_nchw_float(img_bgr, input_hw: Tuple[int, int]):
    import numpy as np
    import cv2
    lb, r, (pad_w, pad_h) = _letterbox(img_bgr, input_hw)
    rgb = cv2.cvtColor(lb, cv2.COLOR_BGR2RGB)
    x = rgb.astype("float32") / 255.0
    x = np.transpose(x, (2, 0, 1))
    x = np.expand_dims(x, axis=0)
    return x, r, (pad_w, pad_h)


def _xywh_to_xyxy(xywh):
    import numpy as np
    x, y, w, h = xywh[:, 0], xywh[:, 1], xywh[:, 2], xywh[:, 3]
    return np.stack([x - w / 2, y - h / 2, x + w / 2, y + h / 2], axis=1)


def _nms_xyxy(boxes, scores, iou_thres: float):
    import numpy as np
    if boxes.size == 0:
        return []
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1).clip(min=0) * (y2 - y1).clip(min=0)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        if order.size == 1:
            break
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = (xx2 - xx1).clip(min=0)
        h = (yy2 - yy1).clip(min=0)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-9)
        inds = np.where(iou <= iou_thres)[0]
        order = order[inds + 1]
    return keep


def _decode_yolo11_outputs(outputs, input_hw: Tuple[int, int], conf_thres: float, iou_thres: float):
    import numpy as np
    if not outputs:
        return np.zeros((0, 4), np.float32), np.zeros((0,), np.float32), np.zeros((0,), np.int64)
    in_h, in_w = input_hw
    arr = np.array(outputs[0])
    if arr.ndim == 3 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.ndim != 2:
        raise RuntimeError(f"YOLO11 输出维度不符合预期: {arr.shape}")
    if arr.shape[0] < arr.shape[1] and arr.shape[0] <= 300 and arr.shape[1] >= 300:
        arr = arr.T
    num, dim = arr.shape
    if dim <= 4:
        raise RuntimeError(f"YOLO11 输出 dim 太小: {arr.shape}")
    boxes_xywh = arr[:, 0:4].astype(np.float32)
    cls_scores = arr[:, 4:].astype(np.float32)
    class_ids = cls_scores.argmax(axis=1).astype(np.int64)
    scores = cls_scores.max(axis=1).astype(np.float32)
    mask = scores >= conf_thres
    if mask.sum() == 0:
        return np.zeros((0, 4), np.float32), np.zeros((0,), np.float32), np.zeros((0,), np.int64)
    boxes_xyxy = _xywh_to_xyxy(boxes_xywh[mask])
    scores = scores[mask]
    class_ids = class_ids[mask]
    if boxes_xyxy.size > 0 and float(boxes_xyxy.max()) <= 2.0:
        boxes_xyxy[:, [0, 2]] *= float(in_w)
        boxes_xyxy[:, [1, 3]] *= float(in_h)
    keep = _nms_xyxy(boxes_xyxy, scores, iou_thres=iou_thres)
    return boxes_xyxy[keep], scores[keep], class_ids[keep]


class OnnxYolo11Inferencer:
    """ONNX YOLO11 推理器：load() 下载模型、读 Redis classes、创建 Session，infer() 返回 InferenceResult"""

    def __init__(
        self,
        model_id: str,
        model_path: str,
        device: str,
        input_size: tuple,
        conf_thres: float = 0.25,
        iou_thres: float = 0.45,
    ):
        self.model_id = model_id
        self.model_path = model_path  # 存储路径，load 时下载到本地
        self.device = device
        self.input_size = input_size or (640, 640)
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self._sess = None
        self._info: Optional[_OnnxSessionInfo] = None
        # target_class -> {code, name} 的映射（来自 model_config.algorithms）
        self._class_name_map: Optional[Dict[str, Dict[str, str]]] = None
        self._local_path: Optional[str] = None

    def load(self) -> None:
        """下载模型到本地（若非绝对路径）、从 Redis 读取 classes、创建 ONNX Session"""
        if os.path.isabs(self.model_path) and os.path.exists(self.model_path):
            self._local_path = self.model_path
        else:
            local_dir = os.path.join(MODEL_DOWNLOAD_PATH, os.path.dirname(self.model_path))
            local_path = os.path.join(MODEL_DOWNLOAD_PATH, self.model_path)
            if not os.path.exists(local_path):
                from common.storage import get_storage
                logger.info(f"ONNX 模型文件不存在，开始下载: {self.model_path} -> {local_path}")
                os.makedirs(local_dir, exist_ok=True)
                get_storage().download_file(self.model_path, local_path)
            self._local_path = local_path

        self._class_name_map = _read_classes_from_redis(self.model_id)
        if not self._class_name_map:
            logger.warning(
                f"ONNX 未从 Redis 读取到 classes 映射，将使用 class_id 作为 class_name: model_id={self.model_id}"
            )

        input_hw = None
        if self.input_size and len(self.input_size) >= 2:
            input_hw = (int(self.input_size[0]), int(self.input_size[1]))
        self._sess, self._info = _onnx_create_session(self._local_path, self.device, input_hw)
        logger.info(f"ONNX session 就绪: providers={self._info.providers}, input_hw={self._info.input_hw}")

    def infer(self, params: Dict[str, Any]) -> InferenceResult:
        import time
        import numpy as np
        frame = params.get("frame")
        request_id = params.get("request_id", "")
        camera_id = params.get("camera_id", "")
        frame_id = int(params.get("frame_id", 0))
        ts = float(params.get("timestamp", time.time()))

        if self._sess is None or self._info is None or frame is None:
            return InferenceResult(
                request_id=request_id,
                camera_id=camera_id,
                frame_id=frame_id,
                detections=[],
                inference_time_ms=0.0,
                timestamp=ts,
            )

        start = time.perf_counter()
        x, r, (pad_w, pad_h) = _preprocess_bgr_to_nchw_float(frame, self._info.input_hw)
        outputs = self._sess.run(self._info.output_names, {self._info.input_name: x})

        boxes, scores, class_ids = _decode_yolo11_outputs(
            outputs, input_hw=self._info.input_hw, conf_thres=self.conf_thres, iou_thres=self.iou_thres
        )

        if boxes.size > 0:
            boxes = boxes.copy()
            boxes[:, [0, 2]] -= float(pad_w)
            boxes[:, [1, 3]] -= float(pad_h)
            boxes /= float(r)
            h0, w0 = frame.shape[:2]
            boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, w0 - 1)
            boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, h0 - 1)

        detections: List[Dict[str, Any]] = []
        for (x1, y1, x2, y2), score, cid in zip(boxes, scores, class_ids):
            class_id = int(cid)
            # 近似将 class_id 映射到某个 target_class：按 key 排序后取第 class_id 个
            algo_code = str(class_id)
            algo_name = str(class_id)
            if self._class_name_map:
                sorted_keys = sorted(self._class_name_map.keys())
                if 0 <= class_id < len(sorted_keys):
                    target_class = sorted_keys[class_id]
                    info = self._class_name_map.get(target_class) or {}
                    algo_code = str(info.get("code") or target_class)
                    algo_name = str(info.get("name") or target_class)
            detections.append({
                "class_id": class_id,
                "class_name": algo_code,  # 绘框等使用英文 code，避免中文导致 cv2.putText 乱码
                "confidence": float(score),
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "algo_name": algo_name,   # 预留中文名称，后续告警推送可以使用
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
        if result.frame is None:
            return None
        drawn = result.frame.copy()
        return draw_detections_inplace(drawn, result.detections)

    def close(self) -> None:
        self._sess = None
        self._info = None
