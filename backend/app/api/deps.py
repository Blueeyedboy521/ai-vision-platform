# -*- coding: utf-8 -*-
"""
API 依赖注入

提供认证、数据库会话等依赖。

认证流程：
- 登录成功后用户信息写入 Redis（user:cache:{user_id}），TTL 与 access token 一致
- 每次请求首次调用 get_current_user 时：先看请求内是否已解析过（request.state.current_user），
  有则直接返回；否则先查 Redis，命中则回填 request.state 并返回；未命中再查 DB 并回写 Redis，
  实现同请求内多次依赖 get_current_user/get_current_admin 只解析一次，且多数请求不查 DB
"""
import json
from typing import Optional, AsyncGenerator

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.redis import get_redis
from app.core.config import settings
from app.services.auth_service import get_auth_service
from app.models import User
from common.redis.channels import RedisKeys
from common.logging import logger


# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)

# 用户缓存 TTL（秒），与 access token 有效期一致
USER_CACHE_TTL = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24) * 60

# 缓存字段（不包含 password）
_USER_CACHE_KEYS = ("id", "username", "nickname", "email", "phone", "avatar", "role", "is_active")


def _user_to_cache_dict(user: User) -> dict:
    return {k: getattr(user, k) for k in _USER_CACHE_KEYS}


def _user_from_cache_dict(data: dict) -> User:
    """从 Redis 缓存 dict 构造用于请求内的 User 实例（仅做只读，不绑定 session）"""
    user = User()
    for k in _USER_CACHE_KEYS:
        if k in data:
            setattr(user, k, data[k])
    return user


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前登录用户

    优先使用本请求内已解析的 current_user（request.state），避免同请求多次查 Redis/DB；
    否则先查 Redis 用户缓存，未命中再查 DB 并回写缓存。
    """
    # 同请求内已解析过，直接返回（类似线程/请求级令牌）
    if getattr(request.state, "current_user", None) is not None:
        return request.state.current_user

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 类型错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = get_auth_service()
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少用户信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 先查 Redis 用户缓存
    try:
        redis = get_redis()
        raw = await redis.client.get(RedisKeys.user_cache(user_id))
        if raw:
            data = json.loads(raw)
            user = _user_from_cache_dict(data)
            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
            request.state.current_user = user
            return user
    except HTTPException:
        raise
    except Exception as e:
        logger.debug(f"读取用户缓存失败，回退 DB: user_id={user_id}, err={e}")

    # 缓存未命中或异常：查 DB 并回写缓存
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")

    try:
        await redis.client.set(
            RedisKeys.user_cache(user_id),
            json.dumps(_user_to_cache_dict(user), ensure_ascii=False),
            ex=USER_CACHE_TTL,
        )
    except Exception as e:
        logger.debug(f"写入用户缓存失败: user_id={user_id}, err={e}")

    request.state.current_user = user
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """获取当前登录用户（可选）；未提供或无效 Token 时返回 None。"""
    if credentials is None:
        return None
    try:
        return await get_current_user(request, credentials, db)
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
