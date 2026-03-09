# -*- coding: utf-8 -*-
"""
数量触发：当前帧检测数量达到阈值才触发
"""
from typing import List

from .base import TriggerContext


class CountTrigger:
    """无状态，仅根据数量阈值判断。"""

    def __init__(self, count_threshold: int):
        self.count_threshold = max(0, int(count_threshold))

    def should_raise(self, detections: List[dict], context: TriggerContext) -> bool:
        if self.count_threshold <= 0:
            return bool(detections)
        return len(detections) >= self.count_threshold
