# -*- coding: utf-8 -*-
"""
告警判定用 bbox 工具（高内聚、可复用）
"""
from typing import List, Optional


def calculate_iou(bbox1: tuple, bbox2: tuple) -> float:
    """计算两个矩形的 IoU。"""
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    union = area1 + area2 - inter
    if union <= 0:
        return 0.0
    return inter / union


def first_bbox_by_class(detections: List[dict], class_name: str) -> Optional[tuple]:
    """取指定 class_name 的第一个检测框 (x1,y1,x2,y2)。"""
    for d in detections:
        if d.get("class_name") != class_name:
            continue
        bbox = d.get("bbox") or []
        if len(bbox) >= 4:
            return tuple(bbox[:4])
    return None


def is_same_alarm_region(now_dets: List[dict], last_dets: List[dict], iou_threshold: float = 0.5) -> bool:
    """判断当前检测与上次告警是否为同一区域（数量、类别一致且对应框 IoU 高）。"""
    if len(now_dets) != len(last_dets):
        return False
    names_now = sorted(d.get("class_name", "") for d in now_dets)
    names_last = sorted(d.get("class_name", "") for d in last_dets)
    if names_now != names_last:
        return False
    for cls in set(names_now):
        now_box = first_bbox_by_class(now_dets, cls)
        last_box = first_bbox_by_class(last_dets, cls)
        if not now_box or not last_box:
            continue
        if calculate_iou(now_box, last_box) < iou_threshold:
            return False
    return True
