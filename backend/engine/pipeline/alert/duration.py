# -*- coding: utf-8 -*-
"""
持续触发：同一目标持续存在 N 秒才触发（跨帧轨迹关联）
"""
from typing import Dict, List, Optional, Tuple

from .base import TriggerContext
from .bbox_utils import calculate_iou

DURATION_IOU_MATCH_THRESHOLD = 0.3
TRACK_EXPIRE_SEC = 5.0


class DurationTrigger:
    """有状态：维护每个目标的首次出现时间，持续 duration_seconds 后触发。"""

    def __init__(self, duration_seconds: float):
        self.duration_seconds = max(0.0, float(duration_seconds))
        self._tracks: Dict[int, _Track] = {}
        self._alarmed: set = set()
        self._next_id = 0

    def should_raise(self, detections: List[dict], context: TriggerContext) -> bool:
        now_ts = context.now_ts
        self._prune_expired(now_ts)

        for d in detections:
            class_name = d.get("class_name") or ""
            bbox = d.get("bbox") or []
            if len(bbox) < 4:
                continue
            bbox_t = tuple(bbox[:4])
            track_id = self._match_or_create_track(class_name, bbox_t, now_ts)
            if track_id is None:
                continue
            if track_id in self._alarmed:
                continue
            first_ts = self._tracks[track_id].first_ts
            if now_ts - first_ts >= self.duration_seconds:
                self._alarmed.add(track_id)
                return True

        return False

    def _match_or_create_track(self, class_name: str, bbox: tuple, now_ts: float) -> Optional[int]:
        best_id: Optional[int] = None
        best_iou = DURATION_IOU_MATCH_THRESHOLD

        for tid, t in self._tracks.items():
            if t.class_name != class_name:
                continue
            iou = calculate_iou(bbox, t.last_bbox)
            if iou > best_iou:
                best_iou = iou
                best_id = tid

        if best_id is not None:
            self._tracks[best_id].last_bbox = bbox
            return best_id

        self._next_id += 1
        self._tracks[self._next_id] = _Track(class_name=class_name, first_ts=now_ts, last_bbox=bbox)
        return self._next_id

    def _prune_expired(self, now_ts: float) -> None:
        to_del = [
            tid for tid, t in self._tracks.items()
            if now_ts - t.first_ts > TRACK_EXPIRE_SEC
        ]
        for tid in to_del:
            self._tracks.pop(tid, None)
            self._alarmed.discard(tid)


class _Track:
    __slots__ = ("class_name", "first_ts", "last_bbox")

    def __init__(self, class_name: str, first_ts: float, last_bbox: tuple):
        self.class_name = class_name
        self.first_ts = first_ts
        self.last_bbox = last_bbox
