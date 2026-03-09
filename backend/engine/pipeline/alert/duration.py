# -*- coding: utf-8 -*-
"""
持续触发：同一目标持续存在 N 秒才触发（跨帧轨迹关联）。
内部自维护轨迹与告警间隔，无需外部上下文。
"""
from typing import Any, Dict, List, Optional, Tuple

from .bbox_utils import calculate_iou

DURATION_IOU_MATCH_THRESHOLD = 0.3
TRACK_EXPIRE_SEC = 5.0


class DurationTrigger:
    """有状态：维护每个目标的首次出现时间，持续 duration_seconds 后触发，并内置告警间隔控制。"""

    def __init__(self, config: Dict[str, Any]):
        self.duration_seconds = max(
            0.0, float(config.get("duration_seconds") or 3.0)
        )
        # 同一算法的告警间隔（秒）
        self.alarm_interval_sec: float = float(
            config.get("alarm_interval_sec", 30.0)
        )
        self._tracks: Dict[int, _Track] = {}
        self._alarmed: set = set()
        self._next_id = 0
        self._last_alarm_ts: float = 0.0

    def should_raise(self, detections: List[dict], now_ts: float) -> bool:
        # 告警节流：同一算法内部维护自己的间隔
        if now_ts - self._last_alarm_ts < self.alarm_interval_sec:
            return False

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
            # 对同一 track 只告警一次；如需重复告警可移除此判断
            if track_id in self._alarmed:
                continue
            first_ts = self._tracks[track_id].first_ts
            if now_ts - first_ts >= self.duration_seconds:
                self._alarmed.add(track_id)
                self._last_alarm_ts = now_ts
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
