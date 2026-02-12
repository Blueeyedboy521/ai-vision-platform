# -*- coding: utf-8 -*-
"""
用户 Schema

定义用户相关的请求和响应模式
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    """
    用户基础字段
    """
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名"
    )
    nickname: Optional[str] = Field(
        default=None,
        max_length=50,
        description="昵称"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=100,
        description="邮箱"
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="手机号"
    )
    role: str = Field(
        default="user",
        description="角色: admin/user"
    )
    remark: Optional[str] = Field(
        default=None,
        description="备注"
    )


class UserCreate(UserBase):
    """
    创建用户请求
    """
    
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="密码"
    )


class UserUpdate(BaseModel):
    """
    更新用户请求
    """
    
    nickname: Optional[str] = Field(
        default=None,
        max_length=50,
        description="昵称"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=100,
        description="邮箱"
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="手机号"
    )
    role: Optional[str] = Field(
        default=None,
        description="角色"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="是否启用"
    )
    remark: Optional[str] = Field(
        default=None,
        description="备注"
    )
    password: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=128,
        description="新密码 (可选)"
    )


class UserResponse(BaseModel):
    """
    用户响应
    """
    
    id: str = Field(description="用户ID")
    username: str = Field(description="用户名")
    nickname: Optional[str] = Field(description="昵称")
    email: Optional[str] = Field(description="邮箱")
    phone: Optional[str] = Field(description="手机号")
    avatar: Optional[str] = Field(description="头像URL")
    role: str = Field(description="角色")
    is_active: bool = Field(description="是否启用")
    remark: Optional[str] = Field(description="备注")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """
    用户列表响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: List[UserResponse] = Field(default_factory=list, description="用户列表")
    page_info: Optional[dict] = Field(default=None, description="分页信息")
