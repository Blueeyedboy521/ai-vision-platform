# -*- coding: utf-8 -*-
"""
日志配置模块

使用 Loguru 提供统一的日志记录功能
"""
import sys
import os
from typing import Optional

from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_path: str = "./logs",
    rotation: str = "00:00",
    retention: str = "30 days",
    enable_console: bool = True
) -> None:
    """
    配置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        log_path: 日志文件目录
        rotation: 日志轮转时间或大小
        retention: 日志保留时间
        enable_console: 是否输出到控制台
    """
    # 移除默认的 handler
    logger.remove()
    
    # 日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 简化的控制台格式
    console_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 添加控制台输出
    if enable_console:
        logger.add(
            sys.stdout,
            format=console_format,
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # 确保日志目录存在
    if log_path:
        os.makedirs(log_path, exist_ok=True)
        
        # 添加文件输出 - 所有日志
        logger.add(
            os.path.join(log_path, "app_{time:YYYY-MM-DD}.log"),
            format=log_format,
            level=log_level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            enqueue=True,  # 异步写入
            backtrace=True,
            diagnose=True
        )
        
        # 添加文件输出 - 错误日志
        logger.add(
            os.path.join(log_path, "error_{time:YYYY-MM-DD}.log"),
            format=log_format,
            level="ERROR",
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
    
    logger.info(f"日志系统初始化完成 | 级别: {log_level} | 路径: {log_path}")


def get_logger(name: Optional[str] = None):
    """
    获取带有自定义名称的 logger
    
    Args:
        name: 日志名称，通常为模块名
        
    Returns:
        配置好的 logger 实例
    """
    if name:
        return logger.bind(name=name)
    return logger


# 导出默认 logger
__all__ = ["logger", "setup_logging", "get_logger"]
