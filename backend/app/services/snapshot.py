# -*- coding: utf-8 -*-
"""
摄像头抓拍服务

从 RTSP 流抓取一帧并保存为图片
"""
from pathlib import Path
from typing import Optional, Tuple

from common.logging import logger


def capture_frame(
    rtsp_url: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout_sec: int = 10
) -> Optional[bytes]:
    """
    从 RTSP 流抓取一帧，返回 JPEG 字节
    
    Returns:
        JPEG 字节，失败返回 None
    """
    try:
        import cv2
    except ImportError:
        logger.warning("OpenCV 未安装，无法抓拍")
        return None
    
    from app.services.stream_probe import build_rtsp_url
    url = build_rtsp_url(rtsp_url, username, password)
    
    cap = None
    try:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MS, timeout_sec * 1000)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        if not ret or frame is None:
            return None
        _, jpeg = cv2.imencode(".jpg", frame)
        return jpeg.tobytes()
    except Exception as e:
        logger.exception("抓拍异常: %s", e)
        return None
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass


def save_snapshot(
    camera_id: str,
    rtsp_url: str,
    save_dir: Path,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    抓拍并保存到文件，返回 (成功, 相对路径或 None)
    
    保存路径: save_dir / f"{camera_id}.jpg"
    相对路径返回: snapshots/{camera_id}.jpg
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    jpeg = capture_frame(rtsp_url, username, password)
    if not jpeg:
        return False, None
    
    filename = f"{camera_id}.jpg"
    filepath = save_dir / filename
    try:
        filepath.write_bytes(jpeg)
        relative = f"snapshots/{filename}"
        return True, relative
    except Exception as e:
        logger.exception("保存抓拍失败: %s", e)
        return False, None
