# -*- coding: utf-8 -*-
"""
立即触发：检测到目标且与上一快照有变化即触发（数量/类别/位置变化）。
内部自维护上一快照与告警间隔，无需外部上下文。
"""
from typing import Any, Dict, List, Optional

from .bbox_utils import calculate_iou, first_bbox_by_class
from loguru import logger
INSTANT_IOU_CHANGE_THRESHOLD = 0.3


class InstantTrigger:
    """
    立即触发策略：
    - 任意一次检测满足“与上一快照有明显变化”即触发；
    - 内部维护上一快照与告警时间戳，并结合 alarm_interval_sec 做节流。
    """

    def __init__(self, config: Dict[str, Any]):
        # 同一算法的告警间隔（秒），直接作为时间窗口使用
        self.alarm_interval_sec: float = float(config.get("alarm_interval_sec", 30.0))
        self._last_snapshot: Optional[Dict[str, Any]] = None
        self._last_alarm_ts: float = 0.0

    def should_raise(self, detections: List[dict], now_ts: float) -> bool:
        if not detections:
            return False

        # 告警节流：同一算法内部维护自己的间隔
        logger.info(f"InstantTrigger 告警节流: now_ts: {now_ts}，last_alarm_ts: {self._last_alarm_ts}，sec: {now_ts - self._last_alarm_ts}")
        if now_ts - self._last_alarm_ts < self.alarm_interval_sec:
            return False

        if self._should_raise_instant(detections):
            self._last_alarm_ts = now_ts
            self._last_snapshot = {"detections": list(detections)}
            return True
        return False

    def _should_raise_instant(self, detections: List[dict]) -> bool:
        last = self._last_snapshot
        if last is None:
            return True

        prev_dets = last.get("detections") or []
        logger.info(f"InstantTrigger 对比检测结果: prev_dets: {prev_dets}，detections: {detections}")
        if not prev_dets:
            return True

        if len(detections) != len(prev_dets):
            return True
        return True
