# -*- coding: utf-8 -*-
"""
API 依赖注入

提供认证、数据库会话等依赖
"""
from typing import Optional, AsyncGenerator

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.redis import get_redis
from app.services.auth_service import get_auth_service
from app.models import User
from common.logging import logger


# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    
    从 Token 中解析用户ID，并从数据库获取用户信息
    
    Args:
        credentials: HTTP Bearer 凭证
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败
    """
    # 检查是否提供了凭证
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    # 解码 Token
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 检查 Token 类型
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 类型错误",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 检查是否在黑名单中
    auth_service = get_auth_service()
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已失效",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 获取用户ID
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少用户信息",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 检查用户是否启用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    获取当前登录用户 (可选)
    
    如果未提供 Token 或 Token 无效，返回 None
    
    Args:
        credentials: HTTP Bearer 凭证
        db: 数据库会话
        
    Returns:
        当前用户对象或 None
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前管理员用户
    
    仅允许管理员访问
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前用户对象 (必须是管理员)
        
    Raises:
        HTTPException: 权限不足
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return current_user


def get_client_ip(request: Request) -> str:
    """
    获取客户端 IP 地址
    
    优先从 X-Forwarded-For 头获取
    
    Args:
        request: 请求对象
        
    Returns:
        客户端 IP 地址
    """
    # 尝试从代理头获取
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一个 IP (客户端真实 IP)
        return forwarded_for.split(",")[0].strip()
    
    # 尝试从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 使用直连 IP
    if request.client:
        return request.client.host
    
    return "unknown"
