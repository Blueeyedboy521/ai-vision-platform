# -*- coding: utf-8 -*-
"""
认证 Schema

定义登录、Token 等相关的请求和响应模式
"""
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    登录请求
    """
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名"
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="密码"
    )


class TokenResponse(BaseModel):
    """
    Token 响应
    """
    
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间(秒)")


class UserInfo(BaseModel):
    """
    用户信息 (登录返回)
    """
    
    id: str = Field(description="用户ID")
    username: str = Field(description="用户名")
    nickname: Optional[str] = Field(default=None, description="昵称")
    email: Optional[str] = Field(default=None, description="邮箱")
    phone: Optional[str] = Field(default=None, description="手机号")
    avatar: Optional[str] = Field(default=None, description="头像URL")
    role: str = Field(description="角色")
    is_admin: bool = Field(description="是否管理员")


class LoginResponse(BaseModel):
    """
    登录响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="登录成功", description="消息")
    data: Optional["LoginResponseData"] = Field(default=None, description="数据")


class LoginResponseData(BaseModel):
    """
    登录响应数据
    """
    
    token: TokenResponse = Field(description="Token信息")
    user: UserInfo = Field(description="用户信息")


class RefreshTokenRequest(BaseModel):
    """
    刷新 Token 请求
    """
    
    refresh_token: str = Field(
        ...,
        description="刷新令牌"
    )


class RefreshTokenResponse(BaseModel):
    """
    刷新 Token 响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[TokenResponse] = Field(default=None, description="新Token")


class ChangePasswordRequest(BaseModel):
    """
    修改密码请求
    """
    
    old_password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="旧密码"
    )
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="新密码"
    )


# 更新前向引用
LoginResponse.model_rebuild()
