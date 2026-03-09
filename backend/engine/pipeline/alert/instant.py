# -*- coding: utf-8 -*-
"""
立即触发：检测到目标且与上一快照有变化即触发（数量/类别/位置变化）
"""
from typing import List

from .base import TriggerContext
from .bbox_utils import calculate_iou, first_bbox_by_class

INSTANT_IOU_CHANGE_THRESHOLD = 0.3


class InstantTrigger:
    """无状态，仅根据当前检测与上下文判断。"""

    def should_raise(self, detections: List[dict], context: TriggerContext) -> bool:
        return _should_raise_instant(detections, context)


def _should_raise_instant(detections: List[dict], context: TriggerContext) -> bool:
    if not detections:
        return False

    last = context.last_snapshot
    last_ts = context.last_snapshot_ts
    window = context.snapshot_window_sec
    now_ts = context.now_ts

    if last is None or (now_ts - last_ts) >= window:
        return True

    prev_dets = last.get("detections") or []
    if not prev_dets:
        return True

    if len(detections) != len(prev_dets):
        return True

    names_now = sorted(d.get("class_name", "") for d in detections)
    names_prev = sorted(d.get("class_name", "") for d in prev_dets)
    if names_now != names_prev:
        return True

    for cls in set(names_now):
        now_box = first_bbox_by_class(detections, cls)
        prev_box = first_bbox_by_class(prev_dets, cls)
        if not now_box or not prev_box:
            continue
        if calculate_iou(now_box, prev_box) < INSTANT_IOU_CHANGE_THRESHOLD:
            return True

    return False
