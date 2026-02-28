# -*- coding: utf-8 -*-
"""
推理器接口定义（Engine 内部使用）

- Inferencer：infer(params) 接收请求参数字典，推理后直接返回完整 InferenceResult，Worker 只负责入队
- InferenceResult：完整推理结果（含 request_id/camera_id/frame_id/detections/inference_time_ms/timestamp）
- build_inferencer：工厂，按 model_type 创建实现类实例，由 Worker 调用 load() 后循环调用 infer(params)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class InferenceResult:
    """推理结果（由各实现类 infer(params) 内组装并返回，Worker 直接 put 到结果队列）"""
    request_id: str
    camera_id: str
    frame_id: int
    detections: List[Dict[str, Any]]  # 与 ResultHandler 兼容: class_id, class_name, confidence, bbox
    inference_time_ms: float
    timestamp: float
    frame: Optional[Any] = None  # 可选，仅用于 draw_boxes 时由 Worker 传入，不入队


class Inferencer(Protocol):
    """推理器接口：infer 接收请求字典，内部推理并组装完整 InferenceResult 返回；draw_boxes 由各实现类绘制检测框"""

    def load(self) -> None:
        """加载模型并初始化（下载、读 Redis 配置 classes 等均由实现类完成）"""
        ...

    def infer(self, params: Dict[str, Any]) -> InferenceResult:
        """
        执行推理。params 至少包含: frame, request_id, camera_id, frame_id；
        实现类内部计时、推理、组装 InferenceResult 后返回，Worker 不再二次组装。
        """
        ...

    def draw_boxes(self, result: InferenceResult) -> Any:
        """
        在 result.frame 上绘制 result.detections 的框与标签，由各实现类实现。
        返回绘制后的图像；若 result.frame 为空则返回 None。不修改原图。
        """
        ...

    def close(self) -> None:
        """释放资源"""
        ...


# 实现类 load() 中下载模型时的本地根目录
MODEL_DOWNLOAD_PATH = "/tmp"


def build_inferencer(
    *,
    model_type: str,
    model_id: str,
    model_path: str,
    device: str,
    input_size: tuple,
) -> Inferencer:
    """
    按 model_type 创建对应推理实现类实例（未调用 load）。
    Worker 中：先 build_inferencer，再调用 inferencer.load()，循环中调用 inferencer.infer(frame)。
    """
    t = (model_type or "").lower()
    if t == "yolo":
        from .inferencer_yolo import UltralyticsYoloInferencer
        return UltralyticsYoloInferencer(
            model_id=model_id,
            model_path=model_path,
            device=device,
        )
    if t == "onnx":
        from .inferencer_onnx import OnnxYolo11Inferencer
        return OnnxYolo11Inferencer(
            model_id=model_id,
            model_path=model_path,
            device=device,
            input_size=input_size,
        )
    raise ValueError(f"不支持的模型类型: {model_type}")
