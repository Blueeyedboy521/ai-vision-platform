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
import cv2
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
        logger.info(f"StreamReader 启动: {self.camera_id},rtsp_url: {self.rtsp_url}")
        self.running = True
        # 判断如果rtsp_url为空，则不启动
        if not self.rtsp_url:
            logger.warning(f"摄像头{self.camera_id} RTSP 地址为空，不启动")
            return
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
            # 关键：RTSP URL 后直接加 TCP 传输参数（兼容所有 OpenCV 版本）
            rtsp_tcp_url = f"{self.rtsp_url}?transportmode=unicast&tcpflag=1"
            self.cap = cv2.VideoCapture(rtsp_tcp_url)
            # 强制设置 TCP 传输（双重保障）
            self.cap.set(cv2.CAP_PROP_RTSP_TRANSPORT, cv2.CAP_RTSP_TRANSPORT_TCP)
            # 超时配置（必须）
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 3000)
            # 设置缓冲区大小
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if self.cap.isOpened():
                logger.info(f"摄像头{self.camera_id} RTSP 连接成功")
                return True
            else:
                logger.warning(f"摄像头{self.camera_id} RTSP 连接失败: {self.rtsp_url}")
                return False
                
        except Exception as e:
            logger.error(f"摄像头{self.camera_id} RTSP 连接异常: {e}")
            return False
    
    def _read_loop(self):
        """读取循环：按目标 fps 墙钟节流，避免拉流过快导致下游推流/推理过快"""
        logger.debug(f"摄像头{self.camera_id} StreamReader 进入读取循环")
        
        frame_interval = 1.0 / self.fps
        next_read_time = 0.0  # 下一帧允许读取的墙钟时间（首次不等待）
        
        while self.running:
            try:
                # 检查连接状态
                if self.cap is None or not self.cap.isOpened():
                    logger.warning(f"摄像头{self.camera_id} RTSP 断开，尝试重连: {self.rtsp_url}")
                    time.sleep(1)
                    if self._connect():
                        self.reconnect_count += 1
                        next_read_time = 0.0
                    continue
                sleep_duration = 0.0
                # 按墙钟时间节流：未到下一帧允许读取时间则 sleep 剩余时长
                now = time.perf_counter()
                if next_read_time > 0 and now < next_read_time:
                    sleep_duration = next_read_time - now
                    if sleep_duration > 0.001:
                        time.sleep(sleep_duration)
                    now = time.perf_counter()
                next_read_time = now + frame_interval
                # 读取帧
                ret, frame = self.cap.read()
                if not ret:
                    # 获取 OpenCV 内部错误码和描述
                    err_code = self.cap.getExceptionMode()  # 或直接打印底层信息
                    # 打印失败原因
                    logger.warning(f"摄像头{self.camera_id} 读取帧失败,isOpened: {self.cap.isOpened()},当前缓存区帧数: {self.cap.get(cv2.CAP_PROP_FRAME_COUNT)},错误码: {err_code}")
                    time.sleep(0.1)
                    continue
                
                self.total_frames += 1
                # 打印每个时间
                logger.error(f"摄像头{self.camera_id} StreamReader1 读取帧{self.total_frames} 时间: {now}，next_read_time: {next_read_time}，sleep_duration: {sleep_duration}，frame_interval: {frame_interval}")
                
                
                # 放入原始帧队列
                if self.frame_queue:
                    try:
                        self.frame_queue.put_nowait({
                            "frame_id": self.total_frames,
                            "frame": frame,
                            "timestamp": now
                        })
                    except Full:
                        self.dropped_frames += 1
                        logger.error(f"摄像头{self.camera_id} StreamReader 读取帧{self.total_frames} 队列满{self.frame_queue.qsize()}，dropped_frames: {self.dropped_frames}")              
                        
                logger.error(f"摄像头{self.camera_id} StreamReader2 读取帧{self.total_frames} 时间: {now}，next_read_time: {next_read_time}，sleep_duration: {sleep_duration}，frame_interval: {frame_interval}")
                    
                # 跳帧检查
                if self.total_frames % (self.skip_frames + 1) != 0:
                    continue
                else:
                    # 发送到推理队列（不再携带结果队列对象，避免跨进程传递 Queue）
                    if self.request_queue:
                        request = {
                            "request_id": str(uuid.uuid4()),
                            "camera_id": self.camera_id,
                            "frame_id": self.total_frames,
                            "frame": frame,
                            "timestamp": now,
                        }
                        try:
                            self.request_queue.put_nowait(request)
                            self.inference_frames += 1
                        except Full:
                            self.dropped_frames += 1
                
            except Exception as e:
                logger.error(f"摄像头{self.camera_id} StreamReader 异常: {e}")
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
