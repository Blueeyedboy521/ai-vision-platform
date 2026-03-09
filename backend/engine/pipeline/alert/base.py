# -*- coding: utf-8 -*-
"""
告警触发基类
"""
from typing import List, Protocol


class AlertTrigger(Protocol):
    """告警触发策略协议：根据当前检测与上下文判断是否应触发告警。"""

    def should_raise(self, detections: List[dict], now_ts: float) -> bool:
        """
        是否应在本帧触发告警。
        :param detections: 当前帧清洗后的检测列表
        :param now_ts: 当前时间戳（秒）
        :return: True 表示应触发，由调用方再做告警间隔与同区域去重后决定是否真正推送
        """
        ...
