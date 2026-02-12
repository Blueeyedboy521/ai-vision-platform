# -*- coding: utf-8 -*-
"""
通用 Schema

定义通用的请求和响应模式
"""
from typing import Any, Generic, List, Optional, TypeVar
from datetime import datetime

from pydantic import BaseModel, Field


# 泛型类型变量
T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """
    统一响应基类
    
    所有 API 响应都使用此结构
    """
    
    code: int = Field(
        default=0,
        description="状态码: 0成功, 非0失败"
    )
    message: str = Field(
        default="success",
        description="响应消息"
    )
    data: Optional[T] = Field(
        default=None,
        description="响应数据"
    )


class PageRequest(BaseModel):
    """
    分页请求参数
    """
    
    page: int = Field(
        default=1,
        ge=1,
        description="页码, 从1开始"
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="每页数量, 最大100"
    )
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """获取限制数量"""
        return self.page_size


class PageInfo(BaseModel):
    """
    分页信息
    """
    
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total: int = Field(description="总记录数")
    total_pages: int = Field(description="总页数")
    
    @classmethod
    def create(cls, page: int, page_size: int, total: int) -> "PageInfo":
        """创建分页信息"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )


class PageResponse(BaseModel, Generic[T]):
    """
    分页响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: List[T] = Field(default_factory=list, description="数据列表")
    page_info: PageInfo = Field(description="分页信息")


class IdResponse(BaseModel):
    """
    ID 响应
    
    用于创建操作返回新记录的 ID
    """
    
    id: str = Field(description="记录ID")


class MessageResponse(BaseModel):
    """
    消息响应
    
    用于不返回数据的操作
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="响应消息")


class ErrorResponse(BaseModel):
    """
    错误响应
    """
    
    code: int = Field(description="错误码")
    message: str = Field(description="错误消息")
    detail: Optional[str] = Field(default=None, description="详细错误信息")


class AuditInfo(BaseModel):
    """
    审计信息
    """
    
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    created_by: Optional[str] = Field(default=None, description="创建人ID")
    updated_by: Optional[str] = Field(default=None, description="更新人ID")


def success_response(
    data: Any = None,
    message: str = "success"
) -> dict:
    """
    构建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        
    Returns:
        响应字典
    """
    return {
        "code": 0,
        "message": message,
        "data": data
    }


def error_response(
    message: str,
    code: int = -1,
    detail: Optional[str] = None
) -> dict:
    """
    构建错误响应
    
    Args:
        message: 错误消息
        code: 错误码
        detail: 详细错误信息
        
    Returns:
        响应字典
    """
    response = {
        "code": code,
        "message": message
    }
    if detail:
        response["detail"] = detail
    return response


def page_response(
    data: List[Any],
    page: int,
    page_size: int,
    total: int,
    message: str = "success"
) -> dict:
    """
    构建分页响应
    
    Args:
        data: 数据列表
        page: 当前页码
        page_size: 每页数量
        total: 总记录数
        message: 响应消息
        
    Returns:
        响应字典
    """
    return {
        "code": 0,
        "message": message,
        "data": data,
        "page_info": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    }
