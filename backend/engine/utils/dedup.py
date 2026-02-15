# -*- coding: utf-8 -*-
"""
告警去重

基于时间窗口和 IoU 的告警去重机制
"""
import time
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class AlarmRecord:
    """告警记录"""
    alarm_type: str
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    timestamp: float
    camera_id: str


class AlarmDeduplicator:
    """
    告警去重器
    
    使用时间窗口和 IoU 进行去重：
    - 时间窗口内的相同类型告警会被过滤
    - IoU 超过阈值的告警会被视为重复
    """
    
    def __init__(
        self,
        time_window: float = 10.0,
        iou_threshold: float = 0.5,
        max_records: int = 1000
    ):
        """
        初始化去重器
        
        Args:
            time_window: 时间窗口 (秒)
            iou_threshold: IoU 阈值
            max_records: 最大记录数
        """
        self.time_window = time_window
        self.iou_threshold = iou_threshold
        self.max_records = max_records
        
        # 按摄像头分组的告警记录
        self._records: Dict[str, List[AlarmRecord]] = {}
    
    def is_duplicate(
        self,
        camera_id: str,
        alarm_type: str,
        bbox: Tuple[float, float, float, float]
    ) -> bool:
        """
        检查是否为重复告警
        
        Args:
            camera_id: 摄像头 ID
            alarm_type: 告警类型
            bbox: 边界框 (x1, y1, x2, y2)
            
        Returns:
            是否重复
        """
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup(camera_id, current_time)
        
        # 获取该摄像头的记录
        records = self._records.get(camera_id, [])
        
        # 检查是否与现有记录重复
        for record in records:
            # 检查类型
            if record.alarm_type != alarm_type:
                continue
            
            # 检查时间窗口
            if current_time - record.timestamp > self.time_window:
                continue
            
            # 检查 IoU
            iou = self._calculate_iou(bbox, record.bbox)
            if iou >= self.iou_threshold:
                return True
        
        return False
    
    def add_record(
        self,
        camera_id: str,
        alarm_type: str,
        bbox: Tuple[float, float, float, float]
    ):
        """
        添加告警记录
        
        Args:
            camera_id: 摄像头 ID
            alarm_type: 告警类型
            bbox: 边界框
        """
        if camera_id not in self._records:
            self._records[camera_id] = []
        
        record = AlarmRecord(
            alarm_type=alarm_type,
            bbox=bbox,
            timestamp=time.time(),
            camera_id=camera_id
        )
        
        self._records[camera_id].append(record)
        
        # 控制记录数量
        if len(self._records[camera_id]) > self.max_records:
            self._records[camera_id] = self._records[camera_id][-self.max_records:]
    
    def _cleanup(self, camera_id: str, current_time: float):
        """清理过期记录"""
        if camera_id not in self._records:
            return
        
        self._records[camera_id] = [
            r for r in self._records[camera_id]
            if current_time - r.timestamp <= self.time_window
        ]
    
    def _calculate_iou(
        self,
        bbox1: Tuple[float, float, float, float],
        bbox2: Tuple[float, float, float, float]
    ) -> float:
        """
        计算两个边界框的 IoU
        
        Args:
            bbox1: 第一个边界框 (x1, y1, x2, y2)
            bbox2: 第二个边界框 (x1, y1, x2, y2)
            
        Returns:
            IoU 值
        """
        # 计算交集
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        
        # 计算并集
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        if union <= 0:
            return 0.0
        
        return intersection / union
    
    def clear(self, camera_id: str = None):
        """
        清空记录
        
        Args:
            camera_id: 摄像头 ID，None 表示清空所有
        """
        if camera_id:
            self._records.pop(camera_id, None)
        else:
            self._records.clear()
