# -*- coding: utf-8 -*-
"""
ResultHandler -> StreamWriter 最新绘框状态

写入时对 detections 深拷贝，避免 result 销毁后 Writer 读到无效引用。
"""
from __future__ import annotations

import copy
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

@dataclass
class OverlayState:
    """
    线程间共享的“最新检测结果”状态，用于推流侧实时绘框（方案A）。
    ResultHandler 写入（update 内深拷贝），StreamWriter 读取（snapshot 返回副本）。
    每路摄像头一个 Pipeline 进程，各自一个 OverlayState，进程间不共享。
    """

    camera_id: str = ""  # 仅用于日志，区分是哪一路
    lock: threading.Lock = field(default_factory=threading.Lock)
    frame_id: Optional[int] = None
    detections: List[Dict[str, Any]] = field(default_factory=list)
    updated_at: float = 0.0

    def update(self, frame_id: Optional[int], detections: List[Dict[str, Any]]) -> None:
        """写入最新结果，detections 深拷贝一份存贮（result 销毁后仍有效）。"""
        now = time.time()
        with self.lock:
            # logger.debug(  f"OverlayState 写入 camera_id={self.camera_id} pid={os.getpid()} frame_id={frame_id} detections_len={len(detections) if detections else 0}")
            self.frame_id = frame_id
            self.detections = copy.deepcopy(detections) if detections else []
            self.updated_at = now

    def snapshot(self) -> Tuple[Optional[int], List[Dict[str, Any]], float]:
        """读当前快照，返回副本供 Writer 使用。"""
        with self.lock:
            # logger.debug(f"OverlayState 读取 camera_id={self.camera_id} pid={os.getpid()} frame_id={self.frame_id} detections_len={len(self.detections)}" )
            return self.frame_id, list(self.detections), self.updated_at
