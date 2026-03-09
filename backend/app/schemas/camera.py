# -*- coding: utf-8 -*-
"""
摄像头 Schema

定义摄像头相关的请求和响应模式
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class CameraBase(BaseModel):
    """
    摄像头基础字段
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="摄像头名称"
    )
    code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="摄像头编码"
    )
    description: Optional[str] = Field(
        default=None,
        description="摄像头描述"
    )
    area_id: Optional[str] = Field(
        default=None,
        description="所属区域ID"
    )
    rtsp_url: str = Field(
        ...,
        max_length=500,
        description="RTSP 流地址（可含认证，如 rtsp://user:pass@host/path）"
    )
    manufacturer: Optional[str] = Field(
        default=None,
        max_length=50,
        description="设备厂商"
    )
    device_model: Optional[str] = Field(
        default=None,
        max_length=50,
        description="设备型号"
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=50,
        description="设备IP"
    )
    location: Optional[str] = Field(
        default=None,
        max_length=200,
        description="安装位置"
    )
    longitude: Optional[float] = Field(
        default=None,
        description="经度"
    )
    latitude: Optional[float] = Field(
        default=None,
        description="纬度"
    )
    fps: int = Field(
        default=25,
        ge=1,
        le=60,
        description="帧率"
    )
    inference_interval_sec: int = Field(
        default=5,
        ge=1,
        le=3600,
        description="识别间隔(秒)，控制该摄像头推理抽帧频率"
    )
    resolution: Optional[str] = Field(
        default=None,
        max_length=20,
        description="分辨率"
    )


class CameraCreate(CameraBase):
    """
    创建摄像头请求
    """
    
    is_enabled: bool = Field(
        default=True,
        description="是否启用"
    )


class CameraUpdate(BaseModel):
    """
    更新摄像头请求
    """
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="摄像头名称"
    )
    code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="摄像头编码"
    )
    description: Optional[str] = Field(
        default=None,
        description="摄像头描述"
    )
    area_id: Optional[str] = Field(
        default=None,
        description="所属区域ID"
    )
    rtsp_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="RTSP 流地址"
    )
    manufacturer: Optional[str] = Field(
        default=None,
        description="设备厂商"
    )
    device_model: Optional[str] = Field(
        default=None,
        description="设备型号"
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="设备IP"
    )
    location: Optional[str] = Field(
        default=None,
        description="安装位置"
    )
    longitude: Optional[float] = Field(
        default=None,
        description="经度"
    )
    latitude: Optional[float] = Field(
        default=None,
        description="纬度"
    )
    fps: Optional[int] = Field(
        default=None,
        ge=1,
        le=60,
        description="帧率"
    )
    inference_interval_sec: Optional[int] = Field(
        default=None,
        ge=1,
        le=3600,
        description="识别间隔(秒)，控制该摄像头推理抽帧频率"
    )
    resolution: Optional[str] = Field(
        default=None,
        description="分辨率"
    )
    is_enabled: Optional[bool] = Field(
        default=None,
        description="是否启用"
    )


class CameraResponse(BaseModel):
    """
    摄像头响应
    """
    
    id: str = Field(description="摄像头ID")
    name: str = Field(description="摄像头名称")
    code: Optional[str] = Field(description="摄像头编码")
    description: Optional[str] = Field(description="摄像头描述")
    area_id: Optional[str] = Field(description="所属区域ID")
    area_name: Optional[str] = Field(default=None, description="所属区域名称")
    rtsp_url: str = Field(description="RTSP 流地址")
    manufacturer: Optional[str] = Field(description="设备厂商")
    device_model: Optional[str] = Field(description="设备型号")
    ip_address: Optional[str] = Field(description="设备IP")
    location: Optional[str] = Field(description="安装位置")
    longitude: Optional[float] = Field(description="经度")
    latitude: Optional[float] = Field(description="纬度")
    fps: int = Field(description="帧率")
    inference_interval_sec: int = Field(description="识别间隔(秒)")
    resolution: Optional[str] = Field(description="分辨率")
    is_enabled: bool = Field(description="是否启用")
    status: str = Field(description="在线状态")
    algorithm_count: int = Field(default=0, description="关联算法数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = {"from_attributes": True}


class CameraListResponse(BaseModel):
    """
    摄像头列表响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: List[CameraResponse] = Field(
        default_factory=list,
        description="摄像头列表"
    )
    page_info: Optional[dict] = Field(
        default=None,
        description="分页信息"
    )


class CameraStatusResponse(BaseModel):
    """
    摄像头状态响应
    """
    
    id: str = Field(description="摄像头ID")
    name: str = Field(description="摄像头名称")
    status: str = Field(description="状态: online/offline/error")
    is_enabled: bool = Field(description="是否启用")
    play_url: Optional[str] = Field(default=None, description="播放地址")
    
    model_config = {"from_attributes": True}


class CameraPlayUrlResponse(BaseModel):
    """
    摄像头播放地址响应
    """
    
    camera_id: str = Field(description="摄像头ID")
    flv_url: Optional[str] = Field(default=None, description="HTTP-FLV 播放地址")
    rtsp_url: Optional[str] = Field(default=None, description="RTSP 播放地址")
    hls_url: Optional[str] = Field(default=None, description="HLS 播放地址")
