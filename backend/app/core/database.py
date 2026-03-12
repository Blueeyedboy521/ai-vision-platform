# -*- coding: utf-8 -*-
"""
数据库模块

提供异步数据库连接和会话管理
"""
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import NullPool

from common.logging import logger
from app.core.config import settings


# 全局引擎和会话工厂
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """
    获取数据库引擎
    
    Returns:
        AsyncEngine 实例
    """
    global _engine
    
    if _engine is None:
        # 根据数据库类型设置不同的连接参数
        connect_args = {}
        
        if "mysql" in settings.DATABASE_URL:
            # MySQL 特定配置
            engine_kwargs = {
                "pool_pre_ping": True,
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_recycle": settings.DB_POOL_RECYCLE,
            }
        elif "sqlite" in settings.DATABASE_URL:
            # SQLite 特定配置
            connect_args = {"check_same_thread": False}
            engine_kwargs = {
                "poolclass": NullPool,
            }
        else:
            # 其他数据库默认配置
            engine_kwargs = {
                "pool_pre_ping": True,
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
            }
        
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            connect_args=connect_args,
            **engine_kwargs
        )
        
        logger.info(f"数据库引擎已创建: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    
    return _engine


def get_session_factory() -> async_sessionmaker:
    """
    获取会话工厂
    
    Returns:
        async_sessionmaker 实例
    """
    global _async_session_factory
    
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话 (依赖注入用)
    
    用于 FastAPI 的 Depends 依赖注入
    
    Yields:
        AsyncSession 数据库会话
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话 (上下文管理器)
    
    用于非依赖注入场景，如后台任务
    
    Example:
        async with get_db_session() as session:
            result = await session.execute(select(User))
            
    Yields:
        AsyncSession 数据库会话
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化数据库
    
    创建表结构和插入默认数据
    """
    from app.models.base import Base
    # 导入所有模型，确保 Base.metadata 完整（含通知/推送相关表）
    from app.models import (  # noqa: F401
        User,
        Area,
        Model,
        Algorithm,
        Camera,
        CameraAlgorithm,
        Alarm,
        NotificationEndpoint,
        NotificationTemplate,
        NotificationPolicy,
        NotificationDeliveryLog,
    )
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表结构已创建")
    
    # 插入默认数据
    await _insert_default_data()


async def _insert_default_data() -> None:
    """
    插入默认数据
    
    包括：默认管理员账号、默认区域等
    """
    from sqlalchemy import select
    from app.models import User, Area
    from app.models.base import generate_uuid
    from app.core.security import hash_password
    
    async with get_db_session() as session:
        # 检查是否已有管理员
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        
        if admin is None:
            # 创建默认管理员
            admin = User(
                id=generate_uuid(),
                username="admin",
                password=hash_password("admin123"),
                nickname="系统管理员",
                role="admin",
                is_active=True
            )
            session.add(admin)
            logger.info("默认管理员账号已创建: admin/admin123")
        
        # 检查是否已有默认区域
        result = await session.execute(
            select(Area).where(Area.name == "默认区域")
        )
        default_area = result.scalar_one_or_none()
        
        if default_area is None:
            # 创建默认区域
            default_area = Area(
                id=generate_uuid(),
                name="默认区域",
                description="系统默认区域",
                sort_order=0
            )
            session.add(default_area)
            logger.info("默认区域已创建")
        
        await session.commit()


async def close_db() -> None:
    """
    关闭数据库连接
    """
    global _engine, _async_session_factory
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("数据库连接已关闭")


# 同步会话工厂 (用于后台线程)
_sync_session_factory = None


def get_sync_session_factory():
    """
    获取同步会话工厂
    
    用于在后台线程中访问数据库
    
    Returns:
        sessionmaker 实例
    """
    global _sync_session_factory
    
    if _sync_session_factory is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # 将异步 URL 转换为同步 URL
        sync_url = settings.DATABASE_URL.replace("+aiomysql", "+pymysql")
        sync_url = sync_url.replace("+aiosqlite", "")
        
        sync_engine = create_engine(
            sync_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        
        _sync_session_factory = sessionmaker(
            sync_engine,
            autocommit=False,
            autoflush=False
        )
    
    return _sync_session_factory


def get_sync_db_session():
    """
    获取同步数据库会话
    
    用于在后台线程中访问数据库
    
    Returns:
        Session 上下文管理器
    """
    from contextlib import contextmanager
    
    @contextmanager
    def session_scope():
        session_factory = get_sync_session_factory()
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    return session_scope()
