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
    for_draw: bool = False,
) -> Inferencer:
    """
    按 model_type 创建对应推理实现类实例（未调用 load）。
    
    用法约定：
    - 推理 Worker 场景：for_draw=False，创建完整推理器实例，后续需要调用 load() + infer()
    - 推流绘框场景：for_draw=True，调用方只会使用 draw_boxes(result)，不会调用 load()/infer()，
      这样在 Pipeline 进程内就不会触发模型下载与 Session 创建，构造成本轻量。
    """
    t = (model_type or "").lower()
    if t == "yolo":
        from .inferencer_yolo import UltralyticsYoloInferencer
        # for_draw=True 时，调用方不会调用 load()/infer()，只用 draw_boxes()，构造开销极小
        return UltralyticsYoloInferencer(
            model_id=model_id,
            model_path=model_path,
            device=device,
        )
    if t == "onnx":
        from .inferencer_onnx import OnnxYolo11Inferencer
        # 同上，for_draw=True 时仅用 draw_boxes，不触发 load()/Session 创建
        return OnnxYolo11Inferencer(
            model_id=model_id,
            model_path=model_path,
            device=device,
            input_size=input_size,
        )
    raise ValueError(f"不支持的模型类型: {model_type}")
