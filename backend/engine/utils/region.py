# -*- coding: utf-8 -*-
"""
区域检测

判断检测点/框是否在指定区域内
"""
from typing import List, Tuple


class RegionDetector:
    """
    区域检测器
    
    支持多边形区域的检测
    """
    
    def __init__(self, polygon: List[Tuple[float, float]]):
        """
        初始化区域检测器
        
        Args:
            polygon: 多边形顶点列表 [(x1, y1), (x2, y2), ...]
        """
        self.polygon = polygon
    
    def point_in_region(self, x: float, y: float) -> bool:
        """
        判断点是否在区域内
        
        使用射线法判断点是否在多边形内
        
        Args:
            x: 点的 x 坐标
            y: 点的 y 坐标
            
        Returns:
            是否在区域内
        """
        if len(self.polygon) < 3:
            return False
        
        n = len(self.polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = self.polygon[i]
            xj, yj = self.polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    def bbox_in_region(
        self,
        bbox: Tuple[float, float, float, float],
        mode: str = "center"
    ) -> bool:
        """
        判断边界框是否在区域内
        
        Args:
            bbox: 边界框 (x1, y1, x2, y2)
            mode: 检测模式
                - "center": 中心点在区域内
                - "any": 任意角点在区域内
                - "all": 所有角点在区域内
                
        Returns:
            是否在区域内
        """
        x1, y1, x2, y2 = bbox
        
        if mode == "center":
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            return self.point_in_region(cx, cy)
        
        elif mode == "any":
            corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            return any(self.point_in_region(x, y) for x, y in corners)
        
        elif mode == "all":
            corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            return all(self.point_in_region(x, y) for x, y in corners)
        
        else:
            raise ValueError(f"不支持的检测模式: {mode}")
    
    def filter_detections(
        self,
        detections: List[dict],
        bbox_key: str = "bbox",
        mode: str = "center"
    ) -> List[dict]:
        """
        过滤不在区域内的检测结果
        
        Args:
            detections: 检测结果列表
            bbox_key: 边界框字段名
            mode: 检测模式
            
        Returns:
            过滤后的检测结果
        """
        result = []
        
        for det in detections:
            bbox = det.get(bbox_key)
            if bbox is None:
                continue
            
            if len(bbox) < 4:
                continue
            
            if self.bbox_in_region(tuple(bbox[:4]), mode):
                result.append(det)
        
        return result
    
    @staticmethod
    def create_from_normalized(
        points: List[Tuple[float, float]],
        width: int,
        height: int
    ) -> "RegionDetector":
        """
        从归一化坐标创建检测器
        
        Args:
            points: 归一化坐标列表 (0-1 范围)
            width: 图像宽度
            height: 图像高度
            
        Returns:
            RegionDetector 实例
        """
        polygon = [(x * width, y * height) for x, y in points]
        return RegionDetector(polygon)
