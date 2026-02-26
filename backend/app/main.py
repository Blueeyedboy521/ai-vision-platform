# -*- coding: utf-8 -*-
"""
FastAPI 应用入口

AI 视觉平台后端服务
"""
import sys
from pathlib import Path
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from common.logging import setup_logging, logger
from app.core.database import init_db, close_db
from app.core.redis import init_redis, close_redis
from app.api import api_router
from app.websocket.manager import connection_manager
from app.websocket.handlers import websocket_handler
from app.services.bootstrap_sync import sync_configs_to_redis_and_streams
from app.consumer.worker_pool import alarm_worker_pool


# 这段代码是 FastAPI（0.92.0+ 版本）中异步生命周期管理的标准写法，核心作用是：
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    在应用启动和关闭时执行初始化和清理工作
    """
    # ==================== 启动阶段 ====================
    logger.info("=" * 50)
    logger.info(f"启动 {settings.PROJECT_NAME}")
    logger.info(f"环境: {settings.ENVIRONMENT}")
    logger.info("=" * 50)
    
    # 初始化日志
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_path=settings.LOG_PATH,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION
    )
    
    # 初始化数据库
    logger.info("初始化数据库...")
    await init_db()
    
    # 初始化 Redis
    logger.info("初始化 Redis...")
    await init_redis()
    
    # 启动时同步配置到 Redis 并初始化流
    try:
        logger.info("启动时同步模型/算法/摄像头配置到 Redis 并初始化流...")
        await sync_configs_to_redis_and_streams()
    except Exception as e:
        logger.warning(f"启动同步 Redis 配置失败: {e}")
    
    # 启动 WebSocket 与告警消费者（依赖 Redis，任一步失败则跳过后续，不阻塞应用启动）
    redis_ok = False
    try:
        logger.info("启动 WebSocket 处理器...")
        await websocket_handler.start()
        redis_ok = True
        logger.info("启动告警消费者线程池...")
        alarm_worker_pool.start(num_workers=settings.ALARM_CONSUMER_WORKERS)
    except Exception as e:
        # 提取完整堆栈信息（字符串格式）
        exc_traceback = traceback.format_exc()
        # 自定义打印内容
        logger.warning(
            "Redis/WebSocket 启动失败，实时推送与告警不可用:\n"
            "异常类型: %s\n"
            "错误描述: %s\n"
            "完整堆栈:\n%s",
            type(e).__name__,
            str(e),
            exc_traceback
        )
        logger.warning("请确认 Redis 已启动（如 docker run -p 6379:6379 redis），然后重启本服务")
    
    logger.info("应用启动完成")
    logger.info("=" * 50)
    
    yield
    
    # ==================== 关闭阶段 ====================
    logger.info("=" * 50)
    logger.info("正在关闭应用...")
    
    if redis_ok:
        logger.info("停止告警消费者线程池...")
        alarm_worker_pool.stop(timeout=5.0)
        logger.info("停止 WebSocket 处理器...")
        await websocket_handler.stop()
    logger.info("关闭 Redis 连接...")
    await close_redis()
    
    # 关闭数据库
    logger.info("关闭数据库连接...")
    await close_db()
    
    logger.info("应用已关闭")
    logger.info("=" * 50)


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI 视觉平台后端 API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)


# ==================== 中间件配置 ====================

# CORS 中间件（.env 中 CORS_ORIGINS 支持 JSON 数组格式）
logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 异常处理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理
    
    捕获未处理的异常，返回统一格式的错误响应
    """
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": -1,
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


# ==================== 路由注册 ====================

# 注册 API 路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# 静态文件服务 (告警截图等)
data_path = Path(settings.LOCAL_STORAGE_PATH)
if data_path.exists():
    app.mount("/static", StaticFiles(directory=str(data_path)), name="static")


# ==================== WebSocket 端点 ====================

@app.websocket("/ws/detections/{camera_id}")
async def websocket_detections(websocket: WebSocket, camera_id: str):
    """
    实时检测结果 WebSocket
    
    订阅指定摄像头的检测框推送
    """
    conn_info = await connection_manager.connect(websocket)
    
    try:
        # 订阅摄像头频道
        await connection_manager.subscribe(websocket, f"camera:{camera_id}")
        
        # 发送连接成功消息
        await connection_manager.send_personal(
            websocket,
            {"type": "connected", "camera_id": camera_id}
        )
        
        # 保持连接，等待客户端消息
        while True:
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息 (如心跳)
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        logger.debug(f"WebSocket 断开: camera={camera_id}")
    finally:
        await connection_manager.disconnect(websocket)


@app.websocket("/ws/alarms")
async def websocket_alarms(websocket: WebSocket):
    """
    实时告警 WebSocket
    
    订阅实时告警推送
    """
    conn_info = await connection_manager.connect(websocket)
    
    try:
        # 订阅告警频道
        await connection_manager.subscribe(websocket, "alarms")
        
        # 发送连接成功消息
        await connection_manager.send_personal(
            websocket,
            {"type": "connected", "channel": "alarms"}
        )
        
        # 保持连接
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        logger.debug("告警 WebSocket 断开")
    finally:
        await connection_manager.disconnect(websocket)


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else None
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
