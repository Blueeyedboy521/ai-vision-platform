# -*- coding: utf-8 -*-
"""
结果处理线程

处理 AI 推理结果，执行以下操作：
1. 在帧上绘制检测框
2. 触发告警并存储
3. 推送实时消息
"""
import threading
import time
import json
from typing import Any, Dict, List, Optional
from queue import Empty

from loguru import logger


class ResultHandler:
    """
    结果处理线程
    
    负责:
    - 从结果队列获取推理结果
    - 绘制检测框
    - 生成告警
    - 推送消息
    """
    
    def __init__(
        self,
        camera_id: str,
        result_queue: Any,
        frame_queue: Any,
        draw_queue: Any,
        algorithms: List[dict]
    ):
        """
        初始化 ResultHandler
        
        Args:
            camera_id: 摄像头 ID
            result_queue: 推理结果队列
            frame_queue: 原始帧队列
            draw_queue: 绘制帧队列
            algorithms: 算法配置列表
        """
        self.camera_id = camera_id
        self.result_queue = result_queue
        self.frame_queue = frame_queue
        self.draw_queue = draw_queue
        self.algorithms = algorithms
        
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        # 告警去重
        self.recent_alarms: Dict[str, float] = {}  # alarm_key -> timestamp
        self.dedup_window = 10.0  # 去重窗口 (秒)
        
        # 统计
        self.processed_results = 0
        self.generated_alarms = 0
        self.pushed_frames = 0
    
    def start(self):
        """启动结果处理"""
        logger.info(f"ResultHandler 启动: {self.camera_id}")
        self.running = True
        
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止结果处理"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"ResultHandler 已停止: {self.camera_id}")
    
    def _process_loop(self):
        """处理循环"""
        logger.debug(f"ResultHandler 进入处理循环: {self.camera_id}")
        
        while self.running:
            try:
                # 获取推理结果
                try:
                    result = self.result_queue.get(timeout=1)
                except Empty:
                    continue
                
                if result is None:
                    continue
                
                self.processed_results += 1
                
                # 获取对应的原始帧
                frame_data = self._get_matching_frame(result.frame_id)
                if frame_data is None:
                    continue
                
                frame = frame_data.get("frame")
                if frame is None:
                    continue
                
                # 处理检测结果
                detections = result.detections if hasattr(result, 'detections') else []
                
                # 绘制检测框
                drawn_frame = self._draw_detections(frame.copy(), detections)
                
                # 放入绘制队列
                try:
                    self.draw_queue.put_nowait({
                        "frame_id": result.frame_id,
                        "frame": drawn_frame,
                        "timestamp": time.time()
                    })
                    self.pushed_frames += 1
                except:
                    pass
                
                # 处理告警
                self._process_alarms(detections, frame)
                
                # 推送实时消息
                self._push_realtime_message(detections)
                
            except Exception as e:
                logger.error(f"ResultHandler 异常: {e}")
    
    def _get_matching_frame(self, frame_id: int) -> Optional[dict]:
        """获取匹配的原始帧"""
        # 从帧队列中查找匹配的帧
        # 注意：简单实现，可能需要优化
        try:
            frame_data = self.frame_queue.get(timeout=0.1)
            return frame_data
        except Empty:
            return None
    
    def _draw_detections(self, frame, detections: list):
        """在帧上绘制检测框"""
        import cv2
        
        for det in detections:
            bbox = det.get("bbox", [])
            if len(bbox) < 4:
                continue
            
            x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
            class_name = det.get("class_name", "unknown")
            confidence = det.get("confidence", 0)
            
            # 根据告警级别选择颜色
            color = self._get_color_by_class(class_name)
            
            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def _get_color_by_class(self, class_name: str) -> tuple:
        """根据类别获取颜色"""
        # 告警类别使用红色
        alarm_classes = ["no_helmet", "no_vest", "fire", "smoke", "intrusion"]
        if class_name.lower() in alarm_classes:
            return (0, 0, 255)  # BGR 红色
        
        # 正常类别使用绿色
        return (0, 255, 0)  # BGR 绿色
    
    def _process_alarms(self, detections: list, frame):
        """处理告警"""
        import cv2
        
        current_time = time.time()
        
        # 清理过期的去重记录
        self._cleanup_dedup_records(current_time)
        
        for det in detections:
            class_name = det.get("class_name", "")
            confidence = det.get("confidence", 0)
            
            # 检查是否触发告警
            if not self._should_trigger_alarm(class_name, confidence):
                continue
            
            # 去重检查
            alarm_key = f"{self.camera_id}_{class_name}"
            if alarm_key in self.recent_alarms:
                continue
            
            # 记录告警
            self.recent_alarms[alarm_key] = current_time
            self.generated_alarms += 1
            
            # 生成告警
            alarm_data = {
                "camera_id": self.camera_id,
                "algorithm_name": class_name,
                "confidence": confidence,
                "bbox": det.get("bbox"),
                "timestamp": current_time
            }
            
            # TODO: 保存告警截图
            # TODO: 存储到数据库
            # TODO: 推送到 Redis
            
            logger.info(f"生成告警: {alarm_data}")
    
    def _should_trigger_alarm(self, class_name: str, confidence: float) -> bool:
        """检查是否应该触发告警"""
        # 告警类别列表
        alarm_classes = ["no_helmet", "no_vest", "fire", "smoke", "intrusion"]
        
        if class_name.lower() not in alarm_classes:
            return False
        
        # 置信度阈值
        if confidence < 0.5:
            return False
        
        return True
    
    def _cleanup_dedup_records(self, current_time: float):
        """清理过期的去重记录"""
        expired_keys = [
            key for key, timestamp in self.recent_alarms.items()
            if current_time - timestamp > self.dedup_window
        ]
        for key in expired_keys:
            del self.recent_alarms[key]
    
    def _push_realtime_message(self, detections: list):
        """推送实时消息"""
        # TODO: 通过 Redis Pub/Sub 推送
        pass
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "processed_results": self.processed_results,
            "generated_alarms": self.generated_alarms,
            "pushed_frames": self.pushed_frames
        }
