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

from engine.utils.ffmpeg_path import resolve_ffmpeg_path, resolve_ffprobe_path
from datetime import datetime

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
        from config.settings import settings
        ffprobe_exe = resolve_ffprobe_path(settings.FFPROBE_PATH or None)
        cmd = [
            ffprobe_exe,
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
        use_ffmpeg: bool = False,
        # 调试用途：关闭推理 + FFmpeg 直推远端（用于定位播放延迟来源）
        disable_inference: bool = False,
        direct_push_url: Optional[str] = None,
        direct_push_ffmpeg: bool = False,
        direct_push_only: bool = False,
    ):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.fps = fps
        self.skip_frames = skip_frames
        self.frame_queue = frame_queue
        self.request_queue = request_queue
        self.result_queue = result_queue
        self.use_ffmpeg = bool(use_ffmpeg)

        # 调试开关：关闭推理、以及在 Reader 内部用 FFmpeg 直推到远端
        self.disable_inference = bool(disable_inference)
        self.direct_push_url = direct_push_url
        self.direct_push_ffmpeg = bool(direct_push_ffmpeg)
        self.direct_push_only = bool(direct_push_only)
        self._push_process: Optional[subprocess.Popen] = None
        self._push_width: int = 0
        self._push_height: int = 0

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
        self.direct_pushed_frames = 0

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
        self._close_push_ffmpeg()
        logger.info(f"StreamReader 已停止: {self.camera_id}")

    def _close_push_ffmpeg(self) -> None:
        p = self._push_process
        if p is None:
            return
        try:
            if p.stdin and not p.stdin.closed:
                try:
                    p.stdin.close()
                except Exception:
                    pass
            p.wait(timeout=3)
        except Exception:
            try:
                p.terminate()
                p.wait(timeout=2)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        self._push_process = None

    def _ensure_push_ffmpeg(self, frame: np.ndarray) -> bool:
        """
        懒初始化 FFmpeg 推流子进程（用于调试直推远端）。
        stdin 接收 rawvideo(BGR24)，输出 RTMP(FLV/H264)。
        """
        if not self.direct_push_ffmpeg or not self.direct_push_url:
            return False
        if self._push_process is not None and self._push_process.poll() is None:
            return True

        h, w = frame.shape[:2]
        fps = int(self.fps) if self.fps else 25
        self._push_width, self._push_height = w, h

        try:
            from config.settings import settings
            ffmpeg_exe = resolve_ffmpeg_path(settings.FFMPEG_PATH or None)
            self._close_push_ffmpeg()
            cmd = [
                ffmpeg_exe,
                "-y",
                "-fflags", "nobuffer",
                "-flags", "low_delay",
                "-flags2", "fast",
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-s", f"{w}x{h}",
                "-r", str(fps),
                "-i", "pipe:0",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-tune", "zerolatency",
                "-g", str(fps),
                "-keyint_min", str(fps),
                "-sc_threshold", "0",
                "-pix_fmt", "yuv420p",
                "-f", "flv",
                self.direct_push_url,
            ]
            self._push_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if self._push_process.poll() is not None:
                logger.error(f"摄像头{self.camera_id} 调试 FFmpeg 直推启动失败: {self.direct_push_url}")
                self._push_process = None
                return False
            logger.info(f"摄像头{self.camera_id} 调试 FFmpeg 直推已开启 -> {self.direct_push_url} ({w}x{h}@{fps})")
            return True
        except FileNotFoundError:
            logger.error(f"摄像头{self.camera_id} 未找到 ffmpeg，请确保已安装并加入 PATH")
            return False
        except Exception as e:
            logger.error(f"摄像头{self.camera_id} 启动调试 FFmpeg 直推异常: {e}")
            self._push_process = None
            return False

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
            from config.settings import settings
            ffmpeg_exe = resolve_ffmpeg_path(settings.FFMPEG_PATH or None)
            self._close_ffmpeg()
            width, height = _probe_rtsp_resolution(self.rtsp_url)
            self._ffmpeg_width = width
            self._ffmpeg_height = height
            cmd = [
                ffmpeg_exe,
                "-y",
                "-rtsp_transport", "tcp",
                # 低延迟拉流参数
                "-fflags", "nobuffer",
                "-flags", "low_delay",
                "-flags2", "fast",
                "-analyzeduration", "0",
                "-probesize", "32",
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
            rtsp_tcp_url = f"{self.rtsp_url}"
            self.cap = cv2.VideoCapture(rtsp_tcp_url)
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
        """读取循环：尽快读取最新帧并分发给后续处理（不再在此按 fps 节流）"""
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

                # 如需逐帧调试，可在此打印 time.perf_counter() 等信息，但请注意会影响延迟与性能

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
                now = time.perf_counter()

                # 周期性打印拉流存活日志
                now_wall = time.time()
                if now_wall - last_alive_log_time >= alive_log_interval:
                    last_alive_log_time = now_wall
                    logger.info(
                        f"摄像头{self.camera_id} StreamReader 仍在拉流中，"
                        f"total_frames={self.total_frames}, "
                        f"inference_frames={self.inference_frames}, "
                        f"dropped_frames={self.dropped_frames}, "
                        f"use_ffmpeg={self.use_ffmpeg}",
                        f"skip_frames={self.skip_frames}"
                    )

                # 调试：在 StreamReader 内部用 FFmpeg 直接推到远端，用于定位播放延迟来源
                if self.direct_push_ffmpeg and self.direct_push_url:
                    if self._ensure_push_ffmpeg(frame):
                        try:
                            if self._push_process and self._push_process.stdin:
                                self._push_process.stdin.write(frame.tobytes())
                            self.direct_pushed_frames += 1
                        except Exception as e:
                            logger.error(f"摄像头{self.camera_id} FFmpeg 直推写入失败: {e}")
                            self._close_push_ffmpeg()
                    else:
                        logger.error(f"摄像头{self.camera_id} FFmpeg 直推启动失败")
                # 默认路径：写入帧队列供 StreamWriter 使用（直推 only 时跳过）
                if not self.direct_push_only:
                    if self.frame_queue:
                        try:
                            self.frame_queue.put_nowait({
                                "frame_id": self.total_frames,
                                "frame": frame,
                                "timestamp": now,
                            })
                        except Full:
                            self.dropped_frames += 1
                # logger.info(f"摄像头{self.camera_id} StreamReader 读取帧{self.total_frames} 时间: {now}，队列大小: {self.frame_queue.qsize()},disable_inference: {self.disable_inference},request_queue: {self.request_queue}")
                # 关闭推理（调试）或未配置 request_queue 时，不发送推理请求
                if self.disable_inference or not self.request_queue:
                    continue

                # 推理节流：按 skip_frames 控制推理频率
                if self.total_frames % (self.skip_frames + 1) != 0:
                    continue

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
            "direct_pushed_frames": self.direct_pushed_frames,
            "connected": connected,
            "use_ffmpeg": self.use_ffmpeg,
        }
