# -*- coding: utf-8 -*-
"""
模型 Schema

定义 AI 模型相关的请求和响应模式
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class ModelBase(BaseModel):
    """
    模型基础字段
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="模型名称"
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="模型编码"
    )
    description: Optional[str] = Field(
        default=None,
        description="模型描述"
    )
    model_type: str = Field(
        default="yolo",
        description="模型类型: yolo/onnx/tensorrt"
    )
    model_path: str = Field(
        ...,
        max_length=500,
        description="模型文件路径"
    )
    version: Optional[str] = Field(
        default=None,
        max_length=20,
        description="模型版本"
    )
    classes: List[str] = Field(
        default_factory=list,
        description="支持的检测类别"
    )
    gpu_memory_mb: Optional[int] = Field(
        default=None,
        ge=0,
        description="GPU显存占用(MB)"
    )
    inference_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="推理耗时(ms)"
    )
    input_width: Optional[int] = Field(
        default=None,
        ge=0,
        description="输入宽度"
    )
    input_height: Optional[int] = Field(
        default=None,
        ge=0,
        description="输入高度"
    )


class ModelCreate(ModelBase):
    """
    创建模型请求
    """
    
    is_enabled: bool = Field(
        default=True,
        description="是否启用"
    )


class ModelUpdate(BaseModel):
    """
    更新模型请求
    """
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="模型名称"
    )
    description: Optional[str] = Field(
        default=None,
        description="模型描述"
    )
    model_type: Optional[str] = Field(
        default=None,
        description="模型类型"
    )
    model_path: Optional[str] = Field(
        default=None,
        max_length=500,
        description="模型文件路径"
    )
    version: Optional[str] = Field(
        default=None,
        max_length=20,
        description="模型版本"
    )
    classes: Optional[List[str]] = Field(
        default=None,
        description="支持的检测类别"
    )
    gpu_memory_mb: Optional[int] = Field(
        default=None,
        ge=0,
        description="GPU显存占用(MB)"
    )
    inference_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="推理耗时(ms)"
    )
    input_width: Optional[int] = Field(
        default=None,
        ge=0,
        description="输入宽度"
    )
    input_height: Optional[int] = Field(
        default=None,
        ge=0,
        description="输入高度"
    )
    is_enabled: Optional[bool] = Field(
        default=None,
        description="是否启用"
    )


class ModelResponse(BaseModel):
    """
    模型响应
    """
    
    id: str = Field(description="模型ID")
    name: str = Field(description="模型名称")
    code: str = Field(description="模型编码")
    description: Optional[str] = Field(description="模型描述")
    model_type: str = Field(description="模型类型")
    model_path: str = Field(description="模型文件路径")
    version: Optional[str] = Field(description="模型版本")
    classes: List[str] = Field(description="支持的检测类别")
    gpu_memory_mb: Optional[int] = Field(description="GPU显存占用(MB)")
    inference_ms: Optional[int] = Field(description="推理耗时(ms)")
    input_width: Optional[int] = Field(description="输入宽度")
    input_height: Optional[int] = Field(description="输入高度")
    is_enabled: bool = Field(description="是否启用")
    algorithm_count: int = Field(default=0, description="关联算法数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = {"from_attributes": True}


class ModelListResponse(BaseModel):
    """
    模型列表响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: List[ModelResponse] = Field(
        default_factory=list,
        description="模型列表"
    )
    page_info: Optional[dict] = Field(
        default=None,
        description="分页信息"
    )
