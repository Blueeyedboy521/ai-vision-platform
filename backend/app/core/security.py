# -*- coding: utf-8 -*-
"""
安全模块

提供 JWT Token 生成/验证、密码加密等功能
"""
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext

from common.logging import logger
from app.core.config import settings


# 密码加密上下文
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """
    密码哈希
    
    Args:
        password: 原始密码
        
    Returns:
        哈希后的密码
    """
    if not password:
        raise ValueError("密码不能为空")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 原始密码
        hashed_password: 哈希后的密码
        
    Returns:
        是否匹配
    """
    if not plain_password or not hashed_password:
        return False
    
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"密码验证异常: {e}")
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建 Access Token
    
    Args:
        data: 要编码的数据 (通常包含 user_id)
        expires_delta: 过期时间间隔
        
    Returns:
        JWT Token 字符串
    """
    to_encode = data.copy()
    
    # 计算过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # 添加标准 JWT 声明
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    # 编码 Token
    token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return token


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建 Refresh Token
    
    Refresh Token 有效期较长，用于刷新 Access Token
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间间隔
        
    Returns:
        JWT Token 字符串
    """
    to_encode = data.copy()
    
    # 计算过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    # 添加标准 JWT 声明
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    # 编码 Token
    token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return token


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码并验证 Token
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        解码后的数据，验证失败返回 None
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.debug("Token 已过期")
        return None
        
    except jwt.InvalidTokenError as e:
        logger.debug(f"Token 无效: {e}")
        return None


def get_token_remaining_time(token: str) -> int:
    """
    获取 Token 剩余有效时间
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        剩余秒数，已过期返回 0
    """
    payload = decode_access_token(token)
    
    if payload is None:
        return 0
    
    exp = payload.get("exp", 0)
    now = int(time.time())
    remaining = exp - now
    
    return max(remaining, 0)


def get_token_hash(token: str) -> str:
    """
    获取 Token 的哈希值 (用于黑名单)
    
    只取前32个字符作为哈希，减少存储空间
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        Token 哈希值
    """
    import hashlib
    return hashlib.md5(token.encode()).hexdigest()
