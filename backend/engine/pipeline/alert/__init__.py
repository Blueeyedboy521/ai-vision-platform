# -*- coding: utf-8 -*-
"""
告警触发策略：高内聚低耦合，三种触发方式独立实现，由工厂统一入口。
"""
from typing import Any, Dict, List

from .base import AlertTrigger, TriggerContext
from .instant import InstantTrigger
from .duration import DurationTrigger
from .count import CountTrigger
from . import bbox_utils

__all__ = [
    "get_trigger",
    "TriggerContext",
    "AlertTrigger",
    "bbox_utils",
]


def get_trigger(trigger_type: str, config: Dict[str, Any]) -> AlertTrigger:
    """
    根据 trigger_type 与 config 返回对应触发策略实例。
    - instant: 立即触发
    - duration: 持续触发，config 需含 duration_seconds
    - count: 数量触发，config 需含 count_threshold
    未知类型回退到 instant。
    """
    t = (trigger_type or "").strip().lower()
    if t == "duration":
        sec = float(config.get("duration_seconds") or 3)
        return DurationTrigger(duration_seconds=sec)
    if t == "count":
        th = int(config.get("count_threshold") or 1)
        return CountTrigger(count_threshold=th)
    return InstantTrigger()
