# -*- coding: utf-8 -*-
"""
推流线程

将处理后的视频帧推送到流媒体服务器
"""
import threading
import time
from typing import Any, Optional
from queue import Empty

from loguru import logger


class StreamWriter:
    """
    推流线程
    
    负责:
    - 连接 RTMP 推流地址
    - 从绘制队列获取帧
    - 编码并推送到流媒体服务器
    """
    
    def __init__(
        self,
        camera_id: str,
        push_url: str,
        frame_queue: Any,
        fps: int = 25,
        width: int = 1920,
        height: int = 1080
    ):
        """
        初始化 StreamWriter
        
        Args:
            camera_id: 摄像头 ID
            push_url: RTMP 推流地址
            frame_queue: 绘制帧队列
            fps: 视频帧率
            width: 视频宽度
            height: 视频高度
        """
        self.camera_id = camera_id
        self.push_url = push_url
        self.frame_queue = frame_queue
        self.fps = fps
        self.width = width
        self.height = height
        
        self.writer = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        # 统计
        self.pushed_frames = 0
        self.dropped_frames = 0
        self.reconnect_count = 0
    
    def start(self):
        """启动推流"""
        logger.info(f"StreamWriter 启动: {self.camera_id}")
        self.running = True
        
        # 连接推流
        if not self._connect():
            logger.warning(f"StreamWriter 连接失败，将在后台重试: {self.camera_id}")
        
        # 启动线程
        self.thread = threading.Thread(target=self._write_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止推流"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.writer:
            self.writer.release()
        logger.info(f"StreamWriter 已停止: {self.camera_id}")
    
    def _connect(self) -> bool:
        """连接推流地址"""
        try:
            import cv2
            
            # 释放旧连接
            if self.writer:
                self.writer.release()
            
            # 创建 VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*"X264")
            self.writer = cv2.VideoWriter(
                self.push_url,
                fourcc,
                self.fps,
                (self.width, self.height)
            )
            
            if self.writer.isOpened():
                logger.info(f"RTMP 推流连接成功: {self.camera_id}")
                return True
            else:
                logger.warning(f"RTMP 推流连接失败: {self.push_url}")
                return False
                
        except Exception as e:
            logger.error(f"RTMP 推流连接异常: {e}")
            return False
    
    def _write_loop(self):
        """推流循环"""
        logger.debug(f"StreamWriter 进入推流循环: {self.camera_id}")
        
        while self.running:
            try:
                # 从队列获取帧
                try:
                    frame_data = self.frame_queue.get(timeout=1)
                except Empty:
                    continue
                
                if frame_data is None:
                    continue
                
                frame = frame_data.get("frame")
                if frame is None:
                    continue
                
                # 检查连接状态
                if self.writer is None or not self.writer.isOpened():
                    logger.warning(f"RTMP 断开，尝试重连: {self.camera_id}")
                    if self._connect():
                        self.reconnect_count += 1
                    else:
                        time.sleep(1)
                        continue
                
                # 调整帧大小
                import cv2
                if frame.shape[1] != self.width or frame.shape[0] != self.height:
                    frame = cv2.resize(frame, (self.width, self.height))
                
                # 推送帧
                self.writer.write(frame)
                self.pushed_frames += 1
                
            except Exception as e:
                logger.error(f"StreamWriter 异常: {e}")
                time.sleep(0.1)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "pushed_frames": self.pushed_frames,
            "dropped_frames": self.dropped_frames,
            "reconnect_count": self.reconnect_count,
            "connected": self.writer is not None and self.writer.isOpened()
        }
