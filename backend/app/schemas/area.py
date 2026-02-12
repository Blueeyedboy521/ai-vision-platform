# -*- coding: utf-8 -*-
"""
区域 Schema

定义区域相关的请求和响应模式
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class AreaBase(BaseModel):
    """
    区域基础字段
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="区域名称"
    )
    code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="区域编码"
    )
    description: Optional[str] = Field(
        default=None,
        description="区域描述"
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="父区域ID"
    )
    sort_order: int = Field(
        default=0,
        ge=0,
        description="排序序号"
    )


class AreaCreate(AreaBase):
    """
    创建区域请求
    """
    pass


class AreaUpdate(BaseModel):
    """
    更新区域请求
    """
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="区域名称"
    )
    code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="区域编码"
    )
    description: Optional[str] = Field(
        default=None,
        description="区域描述"
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="父区域ID"
    )
    sort_order: Optional[int] = Field(
        default=None,
        ge=0,
        description="排序序号"
    )


class AreaResponse(BaseModel):
    """
    区域响应
    """
    
    id: str = Field(description="区域ID")
    name: str = Field(description="区域名称")
    code: Optional[str] = Field(description="区域编码")
    description: Optional[str] = Field(description="区域描述")
    parent_id: Optional[str] = Field(description="父区域ID")
    sort_order: int = Field(description="排序序号")
    camera_count: int = Field(default=0, description="摄像头数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = {"from_attributes": True}


class AreaTreeNode(BaseModel):
    """
    区域树节点
    """
    
    id: str = Field(description="区域ID")
    name: str = Field(description="区域名称")
    code: Optional[str] = Field(description="区域编码")
    parent_id: Optional[str] = Field(description="父区域ID")
    sort_order: int = Field(description="排序序号")
    camera_count: int = Field(default=0, description="摄像头数量")
    children: List["AreaTreeNode"] = Field(
        default_factory=list,
        description="子区域"
    )
    
    model_config = {"from_attributes": True}


class AreaTreeResponse(BaseModel):
    """
    区域树响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: List[AreaTreeNode] = Field(
        default_factory=list,
        description="区域树"
    )


class AreaListResponse(BaseModel):
    """
    区域列表响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: List[AreaResponse] = Field(
        default_factory=list,
        description="区域列表"
    )


# 更新前向引用
AreaTreeNode.model_rebuild()
