# -*- coding: utf-8 -*-
"""
FFmpeg / ffprobe 可执行文件路径解析

优先使用配置路径，未配置时自动检测：
1. shutil.which("ffmpeg") / which("ffprobe")
2. Windows 常见安装目录（若 which 未找到）
"""
import os
import shutil
from typing import Optional


def _common_windows_ffmpeg_paths() -> list:
    """Windows 下常见 FFmpeg 安装目录（bin 下含 ffmpeg.exe），which 未找到时使用"""
    candidates = []
    for base in [
        r"D:\software\ffmpeg-5.1.2\bin",
        r"D:\software\ffmpeg\bin",
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        os.path.expandvars(r"%LOCALAPPDATA%\ffmpeg\bin"),
    ]:
        if base and os.path.isdir(base):
            p = os.path.join(base, "ffmpeg.exe")
            if os.path.isfile(p):
                candidates.append(base)
    return candidates


def resolve_ffmpeg_path(configured: Optional[str] = None) -> str:
    """
    解析 ffmpeg 可执行文件路径。
    - 若 configured 非空且对应文件存在，直接返回
    - 否则 shutil.which("ffmpeg")
    - Windows 下若 which 失败，尝试常见安装目录
    默认回退 "ffmpeg"（依赖 PATH）
    """
    if configured and configured.strip():
        p = configured.strip()
        if os.path.isfile(p):
            return p
        # 可能是目录，补全 ffmpeg[.exe]
        for name in ("ffmpeg.exe", "ffmpeg"):
            full = os.path.join(p, name)
            if os.path.isfile(full):
                return full

    found = shutil.which("ffmpeg")
    if found:
        return found

    if os.name == "nt":
        for base in _common_windows_ffmpeg_paths():
            full = os.path.join(base, "ffmpeg.exe")
            if os.path.isfile(full):
                return full

    return "ffmpeg"


def resolve_ffprobe_path(configured: Optional[str] = None) -> str:
    """
    解析 ffprobe 可执行文件路径。
    逻辑同 resolve_ffmpeg_path，ffprobe 通常与 ffmpeg 同目录。
    """
    if configured and configured.strip():
        p = configured.strip()
        if os.path.isfile(p):
            return p
        for name in ("ffprobe.exe", "ffprobe"):
            full = os.path.join(p, name)
            if os.path.isfile(full):
                return full

    found = shutil.which("ffprobe")
    if found:
        return found

    if os.name == "nt":
        for base in _common_windows_ffmpeg_paths():
            full = os.path.join(base, "ffprobe.exe")
            if os.path.isfile(full):
                return full

    return "ffprobe"
