from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _get_color_by_class(class_name: str) -> Tuple[int, int, int]:
    alarm_classes = {"no_helmet", "no_vest", "fire", "smoke", "intrusion"}
    if str(class_name).lower() in alarm_classes:
        return (0, 0, 255)  # BGR 红色
    return (0, 255, 0)  # BGR 绿色


def draw_detections_inplace(frame: Any, detections: List[Dict[str, Any]]) -> Any:
    """
    在给定 frame(BGR) 上原地绘制 detections（bbox + label），并返回该 frame。

    detections item 格式要求：
    - bbox: [x1,y1,x2,y2]
    - class_name: str
    - confidence: float
    """
    if frame is None or not detections:
        return frame

    import cv2

    for det in detections:
        bbox = det.get("bbox", [])
        if not bbox or len(bbox) < 4:
            continue
        try:
            x1, y1, x2, y2 = [int(round(v)) for v in bbox[:4]]
        except Exception:
            continue
        class_name = det.get("class_name", "")
        confidence = det.get("confidence", 0.0)
        # 允许各推理实现通过 det["color"] 自定义颜色；未提供则按类别默认
        color = det.get("color") or _get_color_by_class(class_name)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{class_name} {float(confidence):.2f}"
        cv2.putText(
            frame,
            label,
            (x1, max(0, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    return frame

