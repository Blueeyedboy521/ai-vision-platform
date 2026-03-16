# -*- coding: utf-8 -*-
"""
认证 API Controller

- 负责登录、登出、Token 刷新等 HTTP 路由
- 业务能力通过 security/auth_service 等模块实现
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_password,
)
from app.core.config import settings
from app.api.deps import get_current_user, get_client_ip
from app.services.auth_service import get_auth_service
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LoginResponseData,
    TokenResponse,
    UserInfo,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
)
from app.schemas.common import MessageResponse
from common.redis.channels import RedisKeys
from common.logging import logger

# 用户缓存 TTL（秒），与 access token 一致
_USER_CACHE_TTL = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
_USER_CACHE_KEYS = (
    "id",
    "username",
    "nickname",
    "email",
    "phone",
    "avatar",
    "role",
    "is_active",
)


router = APIRouter()


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录

    验证用户名密码，返回 Access Token 和 Refresh Token
    """
    # 查询用户
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    # 验证用户存在
    if user is None:
        logger.warning(
            f"登录失败: 用户不存在, "
            f"username={login_data.username}, "
            f"ip={get_client_ip(request)}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(login_data.password, user.password):
        logger.warning(
            f"登录失败: 密码错误, "
            f"username={login_data.username}, "
            f"ip={get_client_ip(request)}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 检查用户是否启用
    if not user.is_active:
        logger.warning(
            f"登录失败: 用户已禁用, " f"username={login_data.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用"
        )

    # 生成 Token
    token_data = {"sub": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # 写入用户信息到 Redis，后续请求 get_current_user 优先从缓存读取，减少 DB 查询
    try:
        redis = get_redis()
        cache = {k: getattr(user, k) for k in _USER_CACHE_KEYS}
        await redis.client.set(
            RedisKeys.user_cache(user.id),
            json.dumps(cache, ensure_ascii=False),
            ex=_USER_CACHE_TTL,
        )
    except Exception as e:
        logger.warning(f"登录后写入用户缓存失败: user_id={user.id}, err={e}")

    logger.info(
        f"登录成功: username={user.username}, " f"ip={get_client_ip(request)}"
    )

    return LoginResponse(
        code=0,
        message="登录成功",
        data=LoginResponseData(
            token=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            user=UserInfo(
                id=user.id,
                username=user.username,
                nickname=user.nickname,
                email=user.email,
                phone=user.phone,
                avatar=user.avatar,
                role=user.role,
                is_admin=user.is_admin,
            ),
        ),
    )


@router.post("/refresh", response_model=RefreshTokenResponse, summary="刷新Token")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
):
    """
    刷新 Access Token

    使用 Refresh Token 获取新的 Token 对
    """
    auth_service = get_auth_service()

    result = await auth_service.refresh_access_token(refresh_data.refresh_token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期",
        )

    return RefreshTokenResponse(
        code=0,
        message="success",
        data=TokenResponse(**result),
    )


@router.post("/logout", response_model=MessageResponse, summary="用户登出")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    用户登出

    将当前 Token 加入黑名单
    """
    # 获取当前 Token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header else None

    if token:
        auth_service = get_auth_service()
        await auth_service.blacklist_token(token)

    logger.info(f"用户登出: username={current_user.username}")

    return MessageResponse(code=0, message="登出成功")


@router.get("/me", summary="获取当前用户信息")
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    获取当前登录用户信息
    """
    return {
        "code": 0,
        "message": "success",
        "data": UserInfo(
            id=current_user.id,
            username=current_user.username,
            nickname=current_user.nickname,
            email=current_user.email,
            phone=current_user.phone,
            avatar=current_user.avatar,
            role=current_user.role,
            is_admin=current_user.is_admin,
        ),
    }


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="修改密码",
)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    修改当前用户密码（从 DB 拉取用户以校验旧密码并更新，修改后清除 Redis 用户缓存）
    """
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if not verify_password(password_data.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误",
        )

    user.password = hash_password(password_data.new_password)
    await db.commit()

    # 清除用户缓存，下次请求会从 DB 加载并重新写入缓存
    try:
        redis = get_redis()
        await redis.client.delete(RedisKeys.user_cache(user.id))
    except Exception as e:
        logger.warning(f"修改密码后清除用户缓存失败: user_id={user.id}, err={e}")

    logger.info(f"密码已修改: username={user.username}")
    return MessageResponse(code=0, message="密码修改成功")

