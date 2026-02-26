# -*- coding: utf-8 -*-
"""
拉流线程

从 RTSP 源读取视频帧，支持 OpenCV 或 FFmpeg 子进程（FFmpeg 更稳定，推荐）。
"""
import subprocess
import threading
import time
import uuid
from typing import Any, Optional, Tuple
from queue import Full

import numpy as np
from loguru import logger

# 可选：OpenCV 仅作备用
try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


def _probe_rtsp_resolution(rtsp_url: str, timeout_sec: int = 10) -> Tuple[int, int]:
    """
    使用 ffprobe 获取 RTSP 流宽高。
    PS D:\software\ffmpeg-5.1.2\bin> ffprobe -v error -rtsp_transport tcp -timeout 10000000 -select_streams v:0 -show_entries stream=width,height -of csv=p=0 rtsp://172.21.68.125:8554/live/camera_local
1280,720
    Returns:
        (width, height)，失败时返回 (1920, 1080) 作为默认。
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            "-rtsp_transport", "tcp",
            "-timeout", str(timeout_sec * 1000000),
            rtsp_url,
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec + 5)
        if out.returncode != 0:
            logger.warning(f"ffprobe 失败: {out.stderr or out.stdout}")
            return 1920, 1080
        line = (out.stdout or "").strip()
        if not line:
            return 1920, 1080
        parts = line.split(",")
        if len(parts) >= 2:
            w, h = int(parts[0].strip()), int(parts[1].strip())
            if w > 0 and h > 0:
                return w, h
    except FileNotFoundError:
        logger.warning("未找到 ffprobe，将使用默认分辨率 1920x1080")
    except Exception as e:
        logger.warning(f"ffprobe 异常: {e}")
    return 1920, 1080


class StreamReader:
    """
    拉流线程
    
    支持两种后端：
    - FFmpeg 子进程：从 stdin 读 rawvideo(BGR24)，RTSP 长连更稳定，推荐。
    - OpenCV VideoCapture：部分环境下读一段时间后 read() 易失败。
    """

    def __init__(
        self,
        camera_id: str,
        rtsp_url: str,
        fps: int = 25,
        skip_frames: int = 3,
        frame_queue: Optional[Any] = None,
        request_queue: Optional[Any] = None,
        result_queue: Optional[Any] = None,
        use_ffmpeg: bool = True,
    ):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.fps = fps
        self.skip_frames = skip_frames
        self.frame_queue = frame_queue
        self.request_queue = request_queue
        self.result_queue = result_queue
        self.use_ffmpeg = bool(use_ffmpeg)

        self.cap = None
        self._ffmpeg_process: Optional[subprocess.Popen] = None
        self._ffmpeg_width = 0
        self._ffmpeg_height = 0
        self.thread: Optional[threading.Thread] = None
        self.running = False

        self.total_frames = 0
        self.inference_frames = 0
        self.dropped_frames = 0
        self.reconnect_count = 0

    def start(self):
        """启动拉流"""
        logger.info(
            f"StreamReader 启动: {self.camera_id}, rtsp_url={self.rtsp_url[:60]}..., use_ffmpeg={self.use_ffmpeg}"
        )
        self.running = True
        if not self.rtsp_url:
            logger.warning(f"摄像头{self.camera_id} RTSP 地址为空，不启动")
            return
        if not self._connect():
            logger.warning(f"StreamReader 连接失败，将在后台重试: {self.camera_id}")
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """停止拉流"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self._close_opencv()
        self._close_ffmpeg()
        logger.info(f"StreamReader 已停止: {self.camera_id}")

    def _close_opencv(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def _close_ffmpeg(self):
        if self._ffmpeg_process is None:
            return
        try:
            self._ffmpeg_process.terminate()
            self._ffmpeg_process.wait(timeout=3)
        except Exception:
            try:
                self._ffmpeg_process.kill()
            except Exception:
                pass
        self._ffmpeg_process = None

    def _connect(self) -> bool:
        """建立连接：优先 FFmpeg，否则 OpenCV"""
        if self.use_ffmpeg:
            return self._connect_ffmpeg()
        return self._connect_opencv()

    def _connect_ffmpeg(self) -> bool:
        """使用 FFmpeg 子进程拉 RTSP，输出 rawvideo BGR24 到 pipe"""
        try:
            self._close_ffmpeg()
            width, height = _probe_rtsp_resolution(self.rtsp_url)
            self._ffmpeg_width = width
            self._ffmpeg_height = height
            cmd = [
                "ffmpeg",
                "-y",
                "-rtsp_transport", "tcp",
                "-timeout", "5000000",
                "-i", self.rtsp_url,
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-s", f"{width}x{height}",
                "-r", str(self.fps),
                "pipe:1",
            ]
            # 将cmd拼接成可执行命令打印出来
            cmd_str = " ".join(cmd)
            logger.info(f"摄像头{self.camera_id} FFmpeg 拉流启动命令: {cmd_str}")
            self._ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=width * height * 3 * 2,
            )
            # 获取启动返回值，判断是否真的启动
            if self._ffmpeg_process.poll() is not None:
                logger.error(f"摄像头{self.camera_id} FFmpeg 拉流启动失败，命令: {cmd_str}")
                return False
            else:
                logger.info(f"摄像头{self.camera_id} FFmpeg 拉流启动成功，命令: {cmd_str}")
                return True
        except FileNotFoundError:
            logger.error(f"摄像头{self.camera_id} 未找到 ffmpeg，请安装并加入 PATH")
            return False
        except Exception as e:
            logger.error(f"摄像头{self.camera_id} FFmpeg 拉流启动异常: {e}")
            return False

    def _connect_opencv(self) -> bool:
        """使用 OpenCV VideoCapture 拉 RTSP（备用）"""
        if not _CV2_AVAILABLE:
            logger.error("OpenCV 未安装，无法使用 OpenCV 拉流")
            return False
        try:
            self._close_opencv()
            rtsp_tcp_url = f"{self.rtsp_url}?transportmode=unicast&tcpflag=1"
            self.cap = cv2.VideoCapture(rtsp_tcp_url)
            self.cap.set(cv2.CAP_PROP_RTSP_TRANSPORT, cv2.CAP_RTSP_TRANSPORT_TCP)
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 3000)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if self.cap.isOpened():
                logger.info(f"摄像头{self.camera_id} OpenCV RTSP 连接成功")
                return True
            logger.warning(f"摄像头{self.camera_id} OpenCV RTSP 连接失败: {self.rtsp_url}")
            return False
        except Exception as e:
            logger.error(f"摄像头{self.camera_id} OpenCV 拉流异常: {e}")
            return False

    def _read_frame_ffmpeg(self) -> Optional[np.ndarray]:
        """从 FFmpeg 子进程读一帧 BGR24，失败返回 None"""
        if self._ffmpeg_process is None or self._ffmpeg_process.poll() is not None:
            return None
        w, h = self._ffmpeg_width, self._ffmpeg_height
        n = w * h * 3
        try:
            buf = self._ffmpeg_process.stdout.read(n)
        except Exception:
            return None
        if not buf or len(buf) != n:
            return None
        return np.frombuffer(buf, dtype=np.uint8).reshape((h, w, 3))

    def _read_frame_opencv(self) -> Optional[np.ndarray]:
        """OpenCV 读一帧，失败返回 None"""
        if self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None
        return frame

    def _read_loop(self):
        """读取循环：按目标 fps 墙钟节流"""
        frame_interval = 1.0 / self.fps
        next_read_time = 0.0
        # 每隔一段时间打印一次存活日志，便于排查拉流是否仍在运行
        last_alive_log_time = time.time()
        alive_log_interval = 10.0  # 秒

        while self.running:
            try:
                # 检查连接
                if self.use_ffmpeg:
                    proc = self._ffmpeg_process
                    if proc is None:
                        connected = False
                        logger.warning(f"摄像头{self.camera_id} 拉流进程不存在 (_ffmpeg_process is None)")
                    else:
                        connected = proc.poll() is None
                else:
                    connected = self.cap is not None and self.cap.isOpened()

                if not connected:
                    logger.warning(
                        f"摄像头{self.camera_id} 拉流断开，尝试重连 (use_ffmpeg={self.use_ffmpeg})"
                    )
                    time.sleep(1)
                    if self._connect():
                        self.reconnect_count += 1
                        next_read_time = 0.0
                    continue

                # 墙钟节流
                now = time.perf_counter()
                if next_read_time > 0 and now < next_read_time:
                    sleep_duration = next_read_time - now
                    if sleep_duration > 0.001:
                        time.sleep(sleep_duration)
                    now = time.perf_counter()
                next_read_time = now + frame_interval

                # 读一帧
                if self.use_ffmpeg:
                    frame = self._read_frame_ffmpeg()
                else:
                    frame = self._read_frame_opencv()

                if frame is None:
                    if self.use_ffmpeg:
                        self._close_ffmpeg()
                    time.sleep(0.1)
                    continue

                self.total_frames += 1

                # 周期性打印拉流存活日志
                now_wall = time.time()
                if now_wall - last_alive_log_time >= alive_log_interval:
                    last_alive_log_time = now_wall
                    logger.info(
                        f"摄像头{self.camera_id} StreamReader 仍在拉流中，"
                        f"total_frames={self.total_frames}, "
                        f"inference_frames={self.inference_frames}, "
                        f"dropped_frames={self.dropped_frames}, "
                        f"use_ffmpeg={self.use_ffmpeg}"
                    )

                if self.frame_queue:
                    try:
                        self.frame_queue.put_nowait({
                            "frame_id": self.total_frames,
                            "frame": frame,
                            "timestamp": now,
                        })
                    except Full:
                        self.dropped_frames += 1

                if self.total_frames % (self.skip_frames + 1) != 0:
                    continue

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
        if self.use_ffmpeg:
            connected = (
                self._ffmpeg_process is not None
                and self._ffmpeg_process.poll() is None
            )
        else:
            connected = self.cap is not None and self.cap.isOpened()
        return {
            "total_frames": self.total_frames,
            "inference_frames": self.inference_frames,
            "dropped_frames": self.dropped_frames,
            "reconnect_count": self.reconnect_count,
            "connected": connected,
            "use_ffmpeg": self.use_ffmpeg,
        }
