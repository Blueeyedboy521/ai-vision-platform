# -*- coding: utf-8 -*-
"""
拉流线程

从 RTSP 源读取视频帧，进行预处理并发送到推理队列
"""
import threading
import time
import uuid
from typing import Any, Optional
from queue import Full

from loguru import logger


class StreamReader:
    """
    拉流线程
    
    负责:
    - 连接 RTSP 源
    - 按帧率读取视频帧
    - 跳帧处理
    - 发送到推理队列
    """
    
    def __init__(
        self,
        camera_id: str,
        rtsp_url: str,
        fps: int = 25,
        skip_frames: int = 3,
        frame_queue: Optional[Any] = None,
        request_queue: Optional[Any] = None,
        result_queue: Optional[Any] = None
    ):
        """
        初始化 StreamReader
        
        Args:
            camera_id: 摄像头 ID
            rtsp_url: RTSP 地址
            fps: 视频帧率
            skip_frames: 跳帧数 (每 N 帧推理一次)
            frame_queue: 原始帧队列 (用于结果处理)
            request_queue: 推理请求队列
            result_queue: 推理结果队列
        """
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.fps = fps
        self.skip_frames = skip_frames
        self.frame_queue = frame_queue
        self.request_queue = request_queue
        self.result_queue = result_queue
        
        self.cap = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        # 统计
        self.total_frames = 0
        self.inference_frames = 0
        self.dropped_frames = 0
        self.reconnect_count = 0
    
    def start(self):
        """启动拉流"""
        logger.info(f"StreamReader 启动: {self.camera_id}")
        self.running = True
        
        # 连接 RTSP
        if not self._connect():
            logger.warning(f"StreamReader 连接失败，将在后台重试: {self.camera_id}")
        
        # 启动线程
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止拉流"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.cap:
            self.cap.release()
        logger.info(f"StreamReader 已停止: {self.camera_id}")
    
    def _connect(self) -> bool:
        """连接 RTSP 源"""
        try:
            import cv2
            
            # 释放旧连接
            if self.cap:
                self.cap.release()
            
            # 创建新连接
            self.cap = cv2.VideoCapture(self.rtsp_url)
            
            # 设置缓冲区大小
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if self.cap.isOpened():
                logger.info(f"RTSP 连接成功: {self.camera_id}")
                return True
            else:
                logger.warning(f"RTSP 连接失败: {self.rtsp_url}")
                return False
                
        except Exception as e:
            logger.error(f"RTSP 连接异常: {e}")
            return False
    
    def _read_loop(self):
        """读取循环"""
        logger.debug(f"StreamReader 进入读取循环: {self.camera_id}")
        
        frame_interval = 1.0 / self.fps
        last_frame_time = time.time()
        
        while self.running:
            try:
                # 检查连接状态
                if self.cap is None or not self.cap.isOpened():
                    logger.warning(f"RTSP 断开，尝试重连: {self.camera_id}")
                    time.sleep(1)
                    if self._connect():
                        self.reconnect_count += 1
                    continue
                
                # 控制帧率
                current_time = time.time()
                if current_time - last_frame_time < frame_interval:
                    time.sleep(0.001)  # 短暂休眠
                    continue
                
                # 读取帧
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning(f"读取帧失败: {self.camera_id}")
                    time.sleep(0.1)
                    continue
                
                last_frame_time = current_time
                self.total_frames += 1
                
                # 放入原始帧队列
                if self.frame_queue:
                    try:
                        self.frame_queue.put_nowait({
                            "frame_id": self.total_frames,
                            "frame": frame,
                            "timestamp": current_time
                        })
                    except Full:
                        self.dropped_frames += 1
                
                # 跳帧检查
                if self.total_frames % (self.skip_frames + 1) != 0:
                    continue
                
                # 发送到推理队列
                if self.request_queue:
                    request = {
                        "request_id": str(uuid.uuid4()),
                        "camera_id": self.camera_id,
                        "frame_id": self.total_frames,
                        "frame": frame,
                        "timestamp": current_time,
                        "result_queue": self.result_queue
                    }
                    
                    try:
                        self.request_queue.put_nowait(request)
                        self.inference_frames += 1
                    except Full:
                        self.dropped_frames += 1
                
            except Exception as e:
                logger.error(f"StreamReader 异常: {e}")
                time.sleep(0.1)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_frames": self.total_frames,
            "inference_frames": self.inference_frames,
            "dropped_frames": self.dropped_frames,
            "reconnect_count": self.reconnect_count,
            "connected": self.cap is not None and self.cap.isOpened()
        }
