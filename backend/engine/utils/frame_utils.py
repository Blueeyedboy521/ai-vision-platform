# -*- coding: utf-8 -*-
"""
帧处理工具

提供图像帧的各种处理功能
"""
import base64
from typing import Optional, Tuple
from io import BytesIO


class FrameUtils:
    """
    帧处理工具类
    
    提供图像帧的编解码、缩放等功能
    """
    
    @staticmethod
    def encode_to_base64(frame, format: str = "JPEG", quality: int = 85) -> str:
        """
        将帧编码为 Base64 字符串
        
        Args:
            frame: numpy 数组格式的图像
            format: 图像格式 (JPEG, PNG)
            quality: 压缩质量 (仅 JPEG 有效)
            
        Returns:
            Base64 编码的字符串
        """
        import cv2
        
        if format.upper() == "JPEG":
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, quality]
            _, buffer = cv2.imencode(".jpg", frame, encode_param)
        else:
            _, buffer = cv2.imencode(".png", frame)
        
        return base64.b64encode(buffer).decode("utf-8")
    
    @staticmethod
    def decode_from_base64(base64_str: str):
        """
        从 Base64 字符串解码帧
        
        Args:
            base64_str: Base64 编码的字符串
            
        Returns:
            numpy 数组格式的图像
        """
        import cv2
        import numpy as np
        
        buffer = base64.b64decode(base64_str)
        nparr = np.frombuffer(buffer, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return frame
    
    @staticmethod
    def resize(frame, width: int, height: int):
        """
        调整帧大小
        
        Args:
            frame: 原始帧
            width: 目标宽度
            height: 目标高度
            
        Returns:
            调整后的帧
        """
        import cv2
        return cv2.resize(frame, (width, height))
    
    @staticmethod
    def resize_keep_ratio(
        frame,
        max_width: int,
        max_height: int,
        pad: bool = False,
        pad_color: Tuple[int, int, int] = (0, 0, 0)
    ):
        """
        保持比例调整帧大小
        
        Args:
            frame: 原始帧
            max_width: 最大宽度
            max_height: 最大高度
            pad: 是否填充到目标大小
            pad_color: 填充颜色 (BGR)
            
        Returns:
            调整后的帧
        """
        import cv2
        import numpy as np
        
        h, w = frame.shape[:2]
        
        # 计算缩放比例
        scale = min(max_width / w, max_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 缩放
        resized = cv2.resize(frame, (new_w, new_h))
        
        if not pad:
            return resized
        
        # 创建填充画布
        canvas = np.full((max_height, max_width, 3), pad_color, dtype=np.uint8)
        
        # 计算偏移
        x_offset = (max_width - new_w) // 2
        y_offset = (max_height - new_h) // 2
        
        # 放置图像
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return canvas
    
    @staticmethod
    def crop(frame, x1: int, y1: int, x2: int, y2: int):
        """
        裁剪帧
        
        Args:
            frame: 原始帧
            x1, y1: 左上角坐标
            x2, y2: 右下角坐标
            
        Returns:
            裁剪后的帧
        """
        h, w = frame.shape[:2]
        
        # 限制坐标范围
        x1 = max(0, min(x1, w))
        y1 = max(0, min(y1, h))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))
        
        return frame[y1:y2, x1:x2]
    
    @staticmethod
    def draw_text(
        frame,
        text: str,
        position: Tuple[int, int],
        font_scale: float = 1.0,
        color: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = 2,
        background: bool = True,
        bg_color: Tuple[int, int, int] = (0, 0, 0)
    ):
        """
        在帧上绘制文本
        
        Args:
            frame: 原始帧
            text: 文本内容
            position: 位置 (x, y)
            font_scale: 字体大小
            color: 文字颜色 (BGR)
            thickness: 线条粗细
            background: 是否绘制背景
            bg_color: 背景颜色 (BGR)
            
        Returns:
            绘制后的帧
        """
        import cv2
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        if background:
            # 计算文本大小
            (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            x, y = position
            
            # 绘制背景
            cv2.rectangle(
                frame,
                (x, y - text_h - baseline),
                (x + text_w, y + baseline),
                bg_color,
                -1
            )
        
        # 绘制文本
        cv2.putText(frame, text, position, font, font_scale, color, thickness)
        
        return frame
    
    @staticmethod
    def save_image(frame, path: str, quality: int = 95) -> bool:
        """
        保存图像到文件
        
        Args:
            frame: 图像帧
            path: 保存路径
            quality: 压缩质量
            
        Returns:
            是否成功
        """
        import cv2
        
        try:
            if path.lower().endswith(".jpg") or path.lower().endswith(".jpeg"):
                cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                cv2.imwrite(path, frame)
            return True
        except Exception:
            return False
