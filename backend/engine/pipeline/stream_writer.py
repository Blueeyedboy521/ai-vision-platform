# -*- coding: utf-8 -*-
"""
推流线程

通过 FFmpeg 子进程将处理后的视频帧推送到流媒体服务器（RTMP/FLV）
"""
import os
import subprocess
import cv2
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from queue import Empty

from loguru import logger
from config.settings import settings

from engine.redis import mark_camera_live_started
from engine.utils.ffmpeg_path import resolve_ffmpeg_path

from .overlay_state import OverlayState
from engine.inference.inferencer import InferenceResult

class StreamWriter:
    """
    推流线程
    
    使用 FFmpeg 子进程从 stdin 接收 rawvideo(BGR24)，编码为 H.264 后推送到 RTMP。
    相比 OpenCV VideoWriter，FFmpeg 对 RTMP 支持稳定、兼容性好。
    """
    
    def __init__(
        self,
        camera_id: str,
        push_url: str,
        frame_queue: Any,
        fps: int = 25,
        width: int = 1920,
        height: int = 1080,
        overlay_state: Optional[OverlayState] = None,
        inferencer: Optional[Any] = None,
    ):
        """
        初始化 StreamWriter
        
        Args:
            camera_id: 摄像头 ID
            push_url: RTMP 推流地址 (如 rtmp://host:1935/live/camera_xxx)
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

        # 实时绘框（方案A）：从 overlay_state 读最新 (frame_id, detections, updated_at)
        self.overlay_state = overlay_state
        self.inferencer = inferencer
        self.enable_overlay_draw = bool(getattr(settings, "ENGINE_STREAM_DRAW_BOXES", False))
        self.overlay_ttl_sec = float(getattr(settings, "ENGINE_STREAM_DRAW_TTL_SEC", 2.0))
        
        self._process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        # 统计
        self.pushed_frames = 0
        self.dropped_frames = 0
        self.reconnect_count = 0

        self._live_started_reported = False

    def _get_overlay_snapshot(self) -> Tuple[Optional[int], List[Dict], float]:
        if self.overlay_state is None:
            return None, [], 0.0
        return self.overlay_state.snapshot()

    def _should_draw_overlay(self, updated_at: float) -> bool:
        if not self.enable_overlay_draw:
            return False
        if self.inferencer is None:
            return False
        if updated_at <= 0:
            return False
        return (time.time() - updated_at) <= self.overlay_ttl_sec

    def _mark_live_started(self):
        """
        将当前摄像头加入 cameras:live:started 集合。
        只在本进程生命周期内上报一次，避免与心跳监控的 SREM 抢状态。
        """
        if self._live_started_reported:
            return
        try:
            mark_camera_live_started(self.camera_id, live_set_ttl_sec=60)
            self._live_started_reported = True
        except Exception as e:
            logger.warning(f"摄像头{self.camera_id} 标记推流状态到 Redis 失败: {e}")
    
    def start(self):
        """启动推流"""
        logger.info(f"摄像头{self.camera_id} StreamWriter 启动, push_url: {self.push_url}，inferencer: {self.inferencer}")
        self.running = True
        
        if not self._connect():
            logger.warning(f"摄像头{self.camera_id} StreamWriter 连接失败，将在后台重试")
        
        self.thread = threading.Thread(target=self._write_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止推流"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self._close_process()
        logger.info(f"摄像头{self.camera_id} StreamWriter 已停止")
    
    def _close_process(self):
        """关闭 FFmpeg 进程"""
        if self._process is None:
            return
        try:
            if self._process.stdin and not self._process.stdin.closed:
                self._process.stdin.close()
            self._process.wait(timeout=3)
        except Exception:
            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
        self._process = None
    
    def _connect(self) -> bool:
        """启动 FFmpeg 子进程，从 pipe 读 rawvideo 推送到 RTMP"""
        try:
            ffmpeg_exe = resolve_ffmpeg_path(settings.FFMPEG_PATH or None)
            self._close_process()
            
            # rawvideo: BGR24, 与 OpenCV 默认一致
            cmd = [
                ffmpeg_exe,
                "-y",
                "-fflags", "nobuffer",       # 关闭输入缓冲
                "-flags", "low_delay",        # 低延迟模式
                "-flags2", "fast",          # 快速模式
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-s", f"{self.width}x{self.height}",
                "-r", str(self.fps),
                "-i", "pipe:0",
                "-c:v", "libx264",
                "-preset", "ultrafast",          # 更激进一点
                "-tune", "zerolatency",
                "-g", str(self.fps),             # 1 秒一个关键帧，例如 25fps -> g=25
                "-keyint_min", str(self.fps),
                "-sc_threshold", "0",
                "-maxrate", "3000k",             # 根据你实际码率需求自己调
                "-bufsize", "3000k",
                "-pix_fmt", "yuv420p",
                "-f", "flv",
                self.push_url,
            ]
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"摄像头{self.camera_id} FFmpeg 推流进程已启动 -> {self.push_url}")
            return True
        except FileNotFoundError:
            logger.error(f"摄像头{self.camera_id} 未找到 ffmpeg，请确保已安装并加入 PATH")
            return False
        except Exception as e:
            logger.error(f"摄像头{self.camera_id} 启动 FFmpeg 推流异常: {e}")
            return False
    
    def _write_loop(self):
        """推流循环：从队列取帧，按墙钟时间节流后写入 FFmpeg stdin"""
        logger.debug(f"摄像头{self.camera_id} StreamWriter 进入推流循环")
        target_interval = 1.0 / self.fps
        next_send_time = 0.0  # 下一帧允许发送的墙钟时间（首次不等待）
        
        sleep_duration = 0.0
        # 每隔一段时间打印一次存活日志，便于排查推流是否仍在运行
        last_alive_log_time = time.time()
        alive_log_interval = 10.0  # 秒
        while self.running:
            try:
                # logger.debug(f"摄像头{self.camera_id} StreamWriter 推流循环时间1: {time.perf_counter()},队列大小: {self.frame_queue.qsize()}")
                try:
                    frame_data = self.frame_queue.get(timeout=target_interval)
                except Empty:
                    continue
                # logger.debug(f"摄像头{self.camera_id} StreamWriter 推流循环时间2: {time.perf_counter()},队列大小: {self.frame_queue.qsize()}，frame_data is None: {frame_data is None}")
                
                if frame_data is None:
                    continue
                
                frame = frame_data.get("frame")
                frame_id = frame_data.get("frame_id")
                if frame is None:
                    continue

                # 方案A：按 TTL 使用“最新检测结果”，调用 Inferencer.draw_boxes(result) 绘框
                overlay_frame_id, overlay_dets, overlay_updated_at = self._get_overlay_snapshot()
                # logger.info(f"摄像头{self.camera_id} StreamWriter 绘框条件: {overlay_frame_id} {overlay_dets} {overlay_updated_at} {self.inferencer}")
                if self._should_draw_overlay(overlay_updated_at) and overlay_dets and self.inferencer is not None:
                    result = InferenceResult(
                        request_id="",
                        camera_id=self.camera_id,
                        frame_id=overlay_frame_id or 0,
                        detections=overlay_dets,
                        inference_time_ms=0.0,
                        timestamp=time.time(),
                        frame=frame,
                    )
                    # logger.info(f"摄像头{self.camera_id} StreamWriter 绘框结果: {result}")
                    drawn = self.inferencer.draw_boxes(result)
                    if drawn is not None:
                        # save_draw_path = getattr(settings, "ENGINE_TEST_SAVE_DRAW_DIR", "G:/ai/temp/draw")
                        # os.makedirs(save_draw_path, exist_ok=True)
                        # save_draw_path = os.path.join(save_draw_path, f"{self.camera_id}_{frame_id}.jpg")
                        # cv2.imwrite(save_draw_path, drawn)
                        # logger.info(f"摄像头{self.camera_id} StreamWriter 绘框结果: {result}")
                        frame = drawn
                
                if self._process is None or self._process.poll() is not None:
                    logger.warning(f"摄像头{self.camera_id} FFmpeg 未运行，尝试重连")
                    if self._connect():
                        self.reconnect_count += 1
                        next_send_time = 0.0
                    else:
                        time.sleep(1)
                    continue
                # 按墙钟时间节流：未到下一帧允许发送时间则 sleep
                now = time.perf_counter()
                # logger.debug(f"摄像头{self.camera_id} StreamWriter 发送帧{frame_id} 时间1: {now}，next_send_time: {next_send_time}，sleep_duration: {sleep_duration}，target_interval: {target_interval}")
                if next_send_time > 0 and now < next_send_time:
                    sleep_duration = next_send_time - now
                    if sleep_duration > 0.001:
                        time.sleep(sleep_duration)
                        pass
                    now = time.perf_counter()
                next_send_time = now + target_interval
                # 打印每个时间
                # logger.debug(f"摄像头{self.camera_id} StreamWriter 发送帧{frame_id} 时间2: {now}，next_send_time: {next_send_time}，sleep_duration: {sleep_duration}，target_interval: {target_interval}")
                if frame.shape[1] != self.width or frame.shape[0] != self.height:
                    frame = cv2.resize(frame, (self.width, self.height))
                
                try:
                    self._process.stdin.write(frame.tobytes())
                    self._process.stdin.flush()
                    self.pushed_frames += 1
                except BrokenPipeError:
                    logger.warning(f"摄像头{self.camera_id} FFmpeg 管道断开")
                    self._process = None
                except Exception as e:
                    logger.error(f"摄像头{self.camera_id} 写入帧失败: {e}")
                    self._process = None

                # 周期性打印推流存活日志
                now_wall = time.time()
                if now_wall - last_alive_log_time >= alive_log_interval:
                    last_alive_log_time = now_wall
                    # 更新 Redis 中的推流状态，便于心跳监控感知当前仍有推流
                    self._mark_live_started()
                    logger.info(
                        f"摄像头{self.camera_id} StreamWriter 仍在推流中，"
                        f"pushed_frames={self.pushed_frames}, "
                        f"dropped_frames={self.dropped_frames}, "
                        f"reconnect_count={self.reconnect_count}"
                    )
                # logger.debug(f"摄像头{self.camera_id} StreamWriter 发送帧{frame_id} 时间3: {now}，next_send_time: {next_send_time}，sleep_duration: {sleep_duration}，target_interval: {target_interval}")
                    
            except Exception as e:
                logger.error(f"摄像头{self.camera_id} StreamWriter 异常: {e}")
                time.sleep(0.1)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        connected = (
            self._process is not None
            and self._process.poll() is None
            and self._process.stdin is not None
            and not self._process.stdin.closed
        )
        return {
            "pushed_frames": self.pushed_frames,
            "dropped_frames": self.dropped_frames,
            "reconnect_count": self.reconnect_count,
            "connected": connected,
        }
