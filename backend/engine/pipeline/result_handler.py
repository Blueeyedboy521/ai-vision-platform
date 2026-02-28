# -*- coding: utf-8 -*-
"""
结果处理线程

处理 AI 推理结果，执行以下操作：
1. 清洗推理结果，推送给 StreamWriter 用于实时绘框（方案A）
2. 触发告警并存储（预留）
3. 推送实时消息（预留）
"""
import threading
import time
from typing import Any, Dict, List, Optional
from queue import Empty

from loguru import logger

from .overlay_state import OverlayState


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
        algorithms: List[dict],
        overlay_state: OverlayState,
    ):
        """
        初始化 ResultHandler
        
        Args:
            camera_id: 摄像头 ID
            result_queue: 推理结果队列
            algorithms: 算法配置列表
            overlay_state: 推送给 StreamWriter 的最新绘框状态（update 内深拷贝）
        """
        self.camera_id = camera_id
        self.result_queue = result_queue
        self.algorithms = algorithms
        self.overlay_state = overlay_state
        
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

                frame_id = getattr(result, "frame_id", None)
                detections = result.detections if hasattr(result, "detections") else []

                # 方案A：写入 overlay_state（内部分深拷贝，result 销毁后 Writer 仍可读）
                try:
                    self.overlay_state.update(frame_id=frame_id, detections=detections)
                except Exception:
                    pass
                self.pushed_frames += 1

                # 预留：告警/消息推送后续再接入，避免阻塞实时链路
                # self._process_alarms(detections, frame)
                # self._push_realtime_message(detections)
                
            except Exception as e:
                logger.error(f"ResultHandler 异常: {e}")
    
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
