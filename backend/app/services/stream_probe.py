# -*- coding: utf-8 -*-
"""
RTSP 流探测服务

使用 OpenCV 或 ffprobe 获取流的宽高、帧率等基本信息
"""
from typing import Optional, Dict, Any

from common.logging import logger
from engine.utils.ffmpeg_path import resolve_ffprobe_path


def build_rtsp_url(
    rtsp_url: str,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> str:
    """构建带认证的 RTSP URL"""
    if not username or not password:
        return rtsp_url
    if "://" in rtsp_url:
        protocol, rest = rtsp_url.split("://", 1)
        return f"{protocol}://{username}:{password}@{rest}"
    return rtsp_url


def probe_stream_opencv(
    rtsp_url: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout_sec: int = 10
) -> Dict[str, Any]:
    """
    使用 OpenCV 探测 RTSP 流信息
    
    Returns:
        {"width": int, "height": int, "fps": float, "resolution": "1920x1080", "success": bool, "error": str|None}
    """
    try:
        import cv2
    except ImportError:
        return {
            "success": False,
            "error": "OpenCV 未安装，请安装: pip install opencv-python-headless",
            "width": None,
            "height": None,
            "fps": None,
            "resolution": None
        }
    
    url = build_rtsp_url(rtsp_url, username, password)
    result = {"success": False, "width": None, "height": None, "fps": None, "resolution": None, "error": None}
    
    cap = None
    try:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        
        if not cap.isOpened():
            result["error"] = "无法打开流，请检查地址或网络"
            return result
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fps_val = cap.get(cv2.CAP_PROP_FPS)
        fps = round(fps_val, 2) if fps_val and fps_val > 0 else None
        
        if width and height:
            result["success"] = True
            result["width"] = width
            result["height"] = height
            result["fps"] = fps
            result["resolution"] = f"{width}x{height}"
            result["error"] = None
        else:
            result["error"] = "无法获取宽高信息"
    except Exception as e:
        logger.exception("流探测异常")
        result["error"] = str(e)
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
    
    return result


def probe_stream_ffprobe(
    rtsp_url: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout_sec: int = 10
) -> Dict[str, Any]:
    """
    使用 ffprobe 探测 RTSP 流信息（备用）
    """
    import subprocess
    import json
    
    url = build_rtsp_url(rtsp_url, username, password)
    result = {"success": False, "width": None, "height": None, "fps": None, "resolution": None, "error": None}
    
    try:
        from config.settings import settings
        ffprobe_exe = resolve_ffprobe_path(settings.FFPROBE_PATH or None)
        cmd = [
            ffprobe_exe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-rtsp_transport", "tcp",
            "-stimeout", str(timeout_sec * 1000000),
            url
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec + 5)
        if out.returncode != 0:
            result["error"] = out.stderr or "ffprobe 执行失败"
            return result
        
        data = json.loads(out.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                result["width"] = int(stream.get("width", 0))
                result["height"] = int(stream.get("height", 0))
                fps_str = stream.get("r_frame_rate", "0/1")
                if "/" in fps_str:
                    n, d = fps_str.split("/", 1)
                    try:
                        result["fps"] = round(int(n) / max(1, int(d)), 2)
                    except (ValueError, ZeroDivisionError):
                        result["fps"] = None
                else:
                    result["fps"] = None
                if result["width"] and result["height"]:
                    result["resolution"] = f"{result['width']}x{result['height']}"
                    result["success"] = True
                break
        if not result["success"]:
            result["error"] = "未找到视频流"
    except FileNotFoundError:
        result["error"] = "未找到 ffprobe，请安装 FFmpeg"
    except subprocess.TimeoutExpired:
        result["error"] = "探测超时"
    except Exception as e:
        logger.exception("ffprobe 异常")
        result["error"] = str(e)
    
    return result


def probe_stream(
    rtsp_url: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout_sec: int = 10
) -> Dict[str, Any]:
    """
    探测 RTSP 流信息，优先 OpenCV，失败时尝试 ffprobe
    """
    res = probe_stream_opencv(rtsp_url, username, password, timeout_sec)
    if res["success"]:
        return res
    return probe_stream_ffprobe(rtsp_url, username, password, timeout_sec)
