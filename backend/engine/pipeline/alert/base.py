# -*- coding: utf-8 -*-
"""
告警触发基类与上下文
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class TriggerContext:
    """告警判定上下文（只读，由 ResultHandler 注入）"""
    now_ts: float
    last_snapshot: Optional[Dict[str, Any]]
    last_snapshot_ts: float
    snapshot_window_sec: float = 3.0


class AlertTrigger(Protocol):
    """告警触发策略协议：根据当前检测与上下文判断是否应触发告警。"""

    def should_raise(self, detections: List[dict], context: TriggerContext) -> bool:
        """
        是否应在本帧触发告警。
        :param detections: 当前帧清洗后的检测列表
        :param context: 上下文（上一快照、时间等）
        :return: True 表示应触发，由调用方再做告警间隔与同区域去重后决定是否真正推送
        """
        ...
