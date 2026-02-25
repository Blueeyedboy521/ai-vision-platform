# -*- coding: utf-8 -*-
"""
摄像头抓拍服务

从 RTSP 流抓取一帧并保存为图片
"""
from pathlib import Path
from typing import Optional, Tuple

from common.logging import logger
from common.storage import get_storage


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
        if not cap.isOpened():
            return None
        frame = None
        # 读取一段时间的帧，取稍后的第 50 帧，避免第一帧是空黑画面
        for i in range(60):
            ret, f = cap.read()
            if not ret or f is None:
                continue
            if i < 49:
                continue
            frame = f
            break
        if frame is None:
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
    save_dir: Path,  # 保留参数以兼容旧调用，不再直接使用磁盘路径
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    抓拍并保存到存储（本地或 MinIO），返回 (成功, 存储 key 或 None)
    """
    jpeg = capture_frame(rtsp_url, username, password)
    if not jpeg:
        return False, None

    storage = get_storage()
    import time
    key = storage.generate_snapshot_path(camera_id, time.time(), extension="jpg")
    try:
        storage.save_file(jpeg, key, content_type="image/jpeg")
        return True, key
    except Exception as e:
        logger.exception("保存抓拍失败: %s", e)
        return False, None
