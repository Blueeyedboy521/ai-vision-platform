# -*- coding: utf-8 -*-
"""
图片处理工具（公共库）

用于缩略图生成、压缩等通用能力，避免在业务代码中散落 OpenCV/PIL 逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from common.logging import logger


@dataclass(frozen=True)
class ThumbnailOptions:
    max_side: int = 320
    quality: int = 70
    output_format: str = "jpg"  # 目前仅支持 jpg


def make_thumbnail_jpeg_from_file(
    filepath: str,
    options: Optional[ThumbnailOptions] = None,
) -> Optional[bytes]:
    """
    从本地图片文件生成缩略图 JPEG bytes。
    """
    options = options or ThumbnailOptions()
    try:
        import cv2
        import numpy as np
    except Exception as e:
        logger.error(f"生成缩略图失败(OpenCV 未安装或导入失败): {e}")
        return None

    try:
        img = cv2.imread(filepath)
        if img is None:
            return None

        h, w = img.shape[:2]
        if h <= 0 or w <= 0:
            return None

        max_side = max(1, int(options.max_side))
        scale = min(1.0, max_side / float(max(h, w)))
        if scale < 1.0:
            new_w = max(1, int(round(w * scale)))
            new_h = max(1, int(round(h * scale)))
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        quality = int(options.quality)
        quality = 1 if quality < 1 else 95 if quality > 95 else quality
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not ok:
            return None
        return buf.tobytes()
    except Exception as e:
        logger.error(f"生成缩略图异常: {e}")
        return None


def build_thumb_key(origin_key: str) -> str:
    """
    由原图 key 推导缩略图 key：同目录下追加 `__thumb` 后缀。
    - xxx.jpg -> xxx__thumb.jpg
    - xxx.jpeg -> xxx__thumb.jpeg
    - 无扩展名 -> xxx__thumb.jpg
    """
    key = (origin_key or "").replace("\\", "/").lstrip("/")
    lower = key.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if lower.endswith(ext):
            return key[: -len(ext)] + "__thumb" + key[-len(ext) :]
    return key + "__thumb.jpg"

