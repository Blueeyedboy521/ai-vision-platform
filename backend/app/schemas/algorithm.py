# -*- coding: utf-8 -*-
"""
算法 Schema

定义检测算法相关的请求和响应模式
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class AlgorithmBase(BaseModel):
    """
    算法基础字段
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="算法名称"
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="算法编码"
    )
    description: Optional[str] = Field(
        default=None,
        description="算法描述"
    )
    model_id: str = Field(
        ...,
        description="关联模型ID"
    )
    target_classes: List[str] = Field(
        default_factory=list,
        description="目标检测类别"
    )
    default_confidence: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="默认置信度阈值"
    )
    alert_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="告警配置"
    )


class AlgorithmCreate(AlgorithmBase):
    """
    创建算法请求
    """
    
    is_enabled: bool = Field(
        default=True,
        description="是否启用"
    )


class AlgorithmUpdate(BaseModel):
    """
    更新算法请求
    """
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="算法名称"
    )
    description: Optional[str] = Field(
        default=None,
        description="算法描述"
    )
    model_id: Optional[str] = Field(
        default=None,
        description="关联模型ID"
    )
    target_classes: Optional[List[str]] = Field(
        default=None,
        description="目标检测类别"
    )
    default_confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="默认置信度阈值"
    )
    alert_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="告警配置"
    )
    is_enabled: Optional[bool] = Field(
        default=None,
        description="是否启用"
    )


class AlgorithmResponse(BaseModel):
    """
    算法响应
    """
    
    id: str = Field(description="算法ID")
    name: str = Field(description="算法名称")
    code: str = Field(description="算法编码")
    description: Optional[str] = Field(description="算法描述")
    model_id: str = Field(description="关联模型ID")
    model_name: Optional[str] = Field(default=None, description="关联模型名称")
    target_classes: List[str] = Field(description="目标检测类别")
    default_confidence: float = Field(description="默认置信度阈值")
    alert_config: Dict[str, Any] = Field(description="告警配置")
    is_enabled: bool = Field(description="是否启用")
    camera_count: int = Field(default=0, description="关联摄像头数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = {"from_attributes": True}


class AlgorithmListResponse(BaseModel):
    """
    算法列表响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: List[AlgorithmResponse] = Field(
        default_factory=list,
        description="算法列表"
    )
    page_info: Optional[dict] = Field(
        default=None,
        description="分页信息"
    )


# ==================== 摄像头-算法配置 ====================

class CameraAlgorithmBase(BaseModel):
    """
    摄像头-算法配置基础字段
    """
    
    camera_id: str = Field(
        ...,
        description="摄像头ID"
    )
    algorithm_id: str = Field(
        ...,
        description="算法ID"
    )
    model_id: str = Field(
        ...,
        description="模型ID"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="置信度阈值(覆盖算法默认值)"
    )
    alert_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="告警配置(覆盖算法默认值)"
    )
    regions: Optional[List[List[List[float]]]] = Field(
        default=None,
        description="检测区域"
    )


class CameraAlgorithmCreate(CameraAlgorithmBase):
    """
    创建摄像头-算法配置请求
    """
    
    is_enabled: bool = Field(
        default=True,
        description="是否启用"
    )


class CameraAlgorithmUpdate(BaseModel):
    """
    更新摄像头-算法配置请求
    """
    
    confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="置信度阈值"
    )
    alert_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="告警配置"
    )
    regions: Optional[List[List[List[float]]]] = Field(
        default=None,
        description="检测区域"
    )
    is_enabled: Optional[bool] = Field(
        default=None,
        description="是否启用"
    )


class CameraAlgorithmResponse(BaseModel):
    """
    摄像头-算法配置响应
    """
    
    id: str = Field(description="配置ID")
    camera_id: str = Field(description="摄像头ID")
    camera_name: Optional[str] = Field(default=None, description="摄像头名称")
    algorithm_id: str = Field(description="算法ID")
    algorithm_name: Optional[str] = Field(default=None, description="算法名称")
    model_id: str = Field(description="模型ID")
    model_name: Optional[str] = Field(default=None, description="模型名称")
    confidence: Optional[float] = Field(description="置信度阈值")
    effective_confidence: float = Field(description="生效的置信度")
    alert_config: Optional[Dict[str, Any]] = Field(description="告警配置")
    effective_alert_config: Dict[str, Any] = Field(description="生效的告警配置")
    regions: List[List[List[float]]] = Field(description="检测区域")
    is_enabled: bool = Field(description="是否启用")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = {"from_attributes": True}
