# -*- coding: utf-8 -*-
"""
认证服务

提供 Token 刷新、黑名单管理等功能
"""
from typing import Optional
from datetime import datetime, timedelta

from common.logging import logger
from common.redis import get_redis_client, RedisKeys
from app.core.security import (
    decode_access_token,
    create_access_token,
    create_refresh_token,
    get_token_hash,
    get_token_remaining_time
)
from app.core.config import settings


class AuthService:
    """
    认证服务
    
    管理 Token 的刷新和黑名单
    """
    
    def __init__(self):
        """初始化认证服务"""
        self._redis = get_redis_client()
    
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Optional[dict]:
        """
        刷新 Access Token
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的 Token 信息，验证失败返回 None
        """
        # 验证 Refresh Token
        payload = decode_access_token(refresh_token)
        
        if payload is None:
            logger.warning("Refresh Token 验证失败")
            return None
        
        # 检查 Token 类型
        if payload.get("type") != "refresh":
            logger.warning("Token 类型不正确，期望 refresh")
            return None
        
        # 检查是否在黑名单中
        if await self.is_token_blacklisted(refresh_token):
            logger.warning("Refresh Token 已被加入黑名单")
            return None
        
        # 获取用户信息
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token 中缺少用户ID")
            return None
        
        # 生成新的 Token
        token_data = {"sub": user_id}
        
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        # 将旧的 Refresh Token 加入黑名单
        await self.blacklist_token(refresh_token)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    async def blacklist_token(self, token: str) -> bool:
        """
        将 Token 加入黑名单
        
        Args:
            token: JWT Token
            
        Returns:
            是否成功
        """
        if not token:
            return False
        
        try:
            # 获取 Token 剩余有效期
            remaining = get_token_remaining_time(token)
            
            if remaining <= 0:
                # Token 已过期，无需加入黑名单
                return True
            
            # 使用 Token 哈希作为 Key
            token_hash = get_token_hash(token)
            key = RedisKeys.token_blacklist(token_hash)
            
            # 设置黑名单，过期时间等于 Token 剩余有效期
            await self._redis.client.setex(key, remaining, "1")
            
            logger.info(f"Token 已加入黑名单: {token_hash[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"加入黑名单失败: {e}")
            return False
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """
        检查 Token 是否在黑名单中
        
        Args:
            token: JWT Token
            
        Returns:
            是否在黑名单中
        """
        if not token:
            return True
        
        try:
            token_hash = get_token_hash(token)
            key = RedisKeys.token_blacklist(token_hash)
            
            exists = await self._redis.client.exists(key)
            return exists > 0
            
        except Exception as e:
            logger.error(f"检查黑名单失败: {e}")
            # 出错时为了安全，认为在黑名单中
            return True
    
    async def logout(
        self,
        access_token: str,
        refresh_token: Optional[str] = None
    ) -> bool:
        """
        登出
        
        将当前的 Access Token 和 Refresh Token 加入黑名单
        
        Args:
            access_token: 访问令牌
            refresh_token: 刷新令牌 (可选)
            
        Returns:
            是否成功
        """
        success = await self.blacklist_token(access_token)
        
        if refresh_token:
            success = success and await self.blacklist_token(refresh_token)
        
        return success


# 全局服务实例
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """
    获取认证服务实例
    
    Returns:
        AuthService 实例
    """
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
