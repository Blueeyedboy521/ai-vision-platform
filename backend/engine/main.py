# -*- coding: utf-8 -*-
"""
视频处理引擎入口

启动命令: python engine/main.py

启动流程:
1. 初始化日志
2. 加载配置
3. 创建 Scheduler
4. 启动引擎
"""
import os
import sys
import signal
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import settings
from engine.scheduler import Scheduler
from common.logging import setup_logging, logger


def main():
    """引擎主函数"""
    # 统一使用 common.logging 组件（与 app 一致），仅区分日志文件名前缀
    setup_logging(
        log_level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else ("DEBUG" if settings.DEBUG else "INFO"),
        log_path=settings.LOG_PATH if hasattr(settings, "LOG_PATH") else str(ROOT_DIR / "logs"),
        rotation=getattr(settings, "LOG_ROTATION", "00:00"),
        retention=getattr(settings, "LOG_RETENTION", "30 days"),
        file_prefix="engine",
    )
    logger.info("=" * 60)
    logger.info("AI 视觉平台 - 视频处理引擎")
    logger.info("=" * 60)
    
    # 创建调度器
    scheduler = Scheduler()
    
    # 注册信号处理
    def signal_handler(signum, frame):
        logger.warning(f"收到信号 {signum}，正在关闭引擎...")
        scheduler.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动调度器
        scheduler.start()
        
        # 进入监控循环
        logger.info("引擎启动完成，进入监控循环...")
        while scheduler.running:
            # 每 5 秒检查一次状态
            import time
            time.sleep(10)
            scheduler.health_check()
            
    except KeyboardInterrupt:
        logger.warning("收到中断信号，正在关闭引擎...")
    except Exception as e:
        logger.exception(f"引擎运行异常: {e}")
    finally:
        scheduler.stop()
        logger.info("引擎已关闭")


if __name__ == "__main__":
    main()
