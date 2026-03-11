# -*- coding: utf-8 -*-
"""
告警 Schema

定义告警相关的请求和响应模式
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class AlarmResponse(BaseModel):
    """
    告警响应
    """
    
    id: str = Field(description="告警ID")
    camera_id: str = Field(description="摄像头ID")
    camera_name: Optional[str] = Field(default=None, description="摄像头名称")
    area_name: Optional[str] = Field(default=None, description="区域名称")
    algorithm_id: str = Field(description="算法ID")
    algorithm_name: Optional[str] = Field(default=None, description="算法名称")
    alarm_type: str = Field(description="告警类型")
    level: str = Field(description="告警级别")
    title: Optional[str] = Field(description="告警标题")
    description: Optional[str] = Field(description="告警描述")
    alarm_time: datetime = Field(description="告警时间")
    snapshot_url: Optional[str] = Field(description="告警截图URL")
    video_url: Optional[str] = Field(description="告警视频URL")
    detection_data: Any = Field(description="检测数据（通常为检测结果列表）")
    status: str = Field(description="处理状态")
    confirmed_by: Optional[str] = Field(description="确认人ID")
    confirmed_at: Optional[datetime] = Field(description="确认时间")
    confirm_remark: Optional[str] = Field(description="确认备注")
    is_pushed: bool = Field(description="是否已推送")
    created_at: datetime = Field(description="创建时间")
    
    model_config = {"from_attributes": True}


class AlarmListResponse(BaseModel):
    """
    告警列表响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: List[AlarmResponse] = Field(
        default_factory=list,
        description="告警列表"
    )
    page_info: Optional[dict] = Field(
        default=None,
        description="分页信息"
    )


class AlarmConfirmRequest(BaseModel):
    """
    告警确认请求
    """
    
    status: str = Field(
        default="confirmed",
        description="新状态: confirmed/ignored/processed"
    )
    remark: Optional[str] = Field(
        default=None,
        max_length=500,
        description="确认备注"
    )


class AlarmBatchConfirmRequest(BaseModel):
    """
    批量确认告警请求
    """
    
    alarm_ids: List[str] = Field(
        ...,
        min_length=1,
        description="告警ID列表"
    )
    status: str = Field(
        default="confirmed",
        description="新状态"
    )
    remark: Optional[str] = Field(
        default=None,
        max_length=500,
        description="确认备注"
    )


class AlarmQueryParams(BaseModel):
    """
    告警查询参数
    """
    
    camera_id: Optional[str] = Field(
        default=None,
        description="摄像头ID"
    )
    algorithm_id: Optional[str] = Field(
        default=None,
        description="算法ID"
    )
    area_id: Optional[str] = Field(
        default=None,
        description="区域ID"
    )
    level: Optional[str] = Field(
        default=None,
        description="告警级别"
    )
    status: Optional[str] = Field(
        default=None,
        description="处理状态"
    )
    alarm_type: Optional[str] = Field(
        default=None,
        description="告警类型"
    )
    start_time: Optional[datetime] = Field(
        default=None,
        description="开始时间"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="结束时间"
    )
    keyword: Optional[str] = Field(
        default=None,
        description="关键词搜索"
    )


class AlarmStatsItem(BaseModel):
    """
    告警统计项
    """
    
    label: str = Field(description="标签")
    value: int = Field(description="数量")


class AlarmStatsResponse(BaseModel):
    """
    告警统计响应
    """
    
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: "AlarmStatsData" = Field(description="统计数据")


class AlarmStatsData(BaseModel):
    """
    告警统计数据
    """
    
    total: int = Field(description="总告警数")
    unconfirmed: int = Field(description="未确认数")
    confirmed: int = Field(description="已确认数")
    ignored: int = Field(description="已忽略数")
    processed: int = Field(description="已处理数")
    by_level: List[AlarmStatsItem] = Field(
        default_factory=list,
        description="按级别统计"
    )
    by_camera: List[AlarmStatsItem] = Field(
        default_factory=list,
        description="按摄像头统计"
    )
    by_algorithm: List[AlarmStatsItem] = Field(
        default_factory=list,
        description="按算法统计"
    )
    trend: List["AlarmTrendItem"] = Field(
        default_factory=list,
        description="趋势数据"
    )


class AlarmTrendItem(BaseModel):
    """
    告警趋势项
    """
    
    date: str = Field(description="日期/时间")
    count: int = Field(description="数量")


class AlarmOverviewStats(BaseModel):
    """
    告警概览统计（顶部卡片数据）
    """
    
    total: int = Field(description="总告警数")
    total_trend: float = Field(description="总数趋势百分比")
    total_new: int = Field(description="较昨日新增数")
    unconfirmed: int = Field(description="待处理数")
    unconfirmed_trend: float = Field(description="待处理趋势百分比")
    urgent_count: int = Field(description="紧急处理中数量")
    confirmed: int = Field(description="已解决数")
    confirmed_trend: float = Field(description="已解决趋势百分比")
    avg_handle_time: float = Field(description="平均处理时间(分钟)")
    completion_rate: float = Field(description="处理完成率")
    completion_trend: float = Field(description="完成率趋势百分比")
    site_rank_percent: float = Field(description="站点排名百分比")


class AlarmDeviceTopItem(BaseModel):
    """
    高频告警设备项
    """
    
    camera_id: str = Field(description="摄像头ID")
    camera_name: str = Field(description="设备名称")
    area_name: Optional[str] = Field(description="所属区域")
    count: int = Field(description="告警数")


class AlarmAreaTopItem(BaseModel):
    """
    高频告警区域项
    """
    
    area_name: str = Field(description="区域名称")
    count: int = Field(description="告警数")
    percentage: float = Field(description="占比百分比")


class AlarmTypeStatsItem(BaseModel):
    """
    告警类型统计项
    """
    
    algorithm_id: str = Field(description="算法ID")
    algorithm_name: str = Field(description="告警类型名称")
    count: int = Field(description="数量")
    percentage: float = Field(description="占比百分比")


class AlarmLevelStatsItem(BaseModel):
    """
    告警等级统计项
    """
    
    level: str = Field(description="等级: info/warning/danger/critical")
    label: str = Field(description="等级标签")
    count: int = Field(description="数量")
    percentage: float = Field(description="占比百分比")


class AlarmDashboardStats(BaseModel):
    """
    告警仪表盘统计数据（完整统计页面）
    """
    
    overview: AlarmOverviewStats = Field(description="概览统计")
    trend: List[AlarmTrendItem] = Field(description="趋势数据")
    trend_range: str = Field(description="趋势时间范围描述")
    device_top: List[AlarmDeviceTopItem] = Field(description="高频告警设备Top5")
    area_top: List[AlarmAreaTopItem] = Field(description="高频告警区域Top5")
    type_stats: List[AlarmTypeStatsItem] = Field(description="告警类型统计")
    level_stats: List[AlarmLevelStatsItem] = Field(description="告警等级分布")


# 更新前向引用
AlarmStatsResponse.model_rebuild()
AlarmStatsData.model_rebuild()
