# -*- coding: utf-8 -*-
"""
数量触发：当前帧检测数量达到阈值才触发。
内部自维护告警间隔，无需外部上下文。
"""
from typing import Any, Dict, List


class CountTrigger:
    """根据数量阈值 + 告警间隔判断是否触发。"""

    def __init__(self, config: Dict[str, Any]):
        self.count_threshold = max(0, int(config.get("count_threshold") or 1))
        # 同一算法的告警间隔（秒）
        self.alarm_interval_sec: float = float(
            config.get("alarm_interval_sec", 30.0)
        )
        self._last_alarm_ts: float = 0.0

    def should_raise(self, detections: List[dict], now_ts: float) -> bool:
        if not detections:
            return False
        # 告警节流
        if now_ts - self._last_alarm_ts < self.alarm_interval_sec:
            return False

        if self.count_threshold <= 0:
            ok = bool(detections)
        else:
            ok = len(detections) >= self.count_threshold

        if ok:
            self._last_alarm_ts = now_ts
        return ok
