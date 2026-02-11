"""
System management endpoints.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class SystemInfo(BaseModel):
    """System information."""
    version: str
    uptime: int  # seconds
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    camera_count: int
    online_camera_count: int
    algorithm_count: int
    today_alarm_count: int


class OperationLog(BaseModel):
    """Operation log model."""
    id: int
    user: str
    action: str
    resource: str
    resource_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: str
    created_at: datetime


class OperationLogListResponse(BaseModel):
    """Operation log list response."""
    total: int
    items: List[OperationLog]


# Mock data
mock_logs = [
    {
        "id": 1,
        "user": "admin",
        "action": "create",
        "resource": "camera",
        "resource_id": 1,
        "detail": "创建摄像头：大厅摄像头-01",
        "ip_address": "192.168.1.100",
        "created_at": datetime.now(),
    },
    {
        "id": 2,
        "user": "admin",
        "action": "update",
        "resource": "algorithm",
        "resource_id": 1,
        "detail": "更新算法配置：人员入侵检测",
        "ip_address": "192.168.1.100",
        "created_at": datetime.now(),
    },
]


@router.get("/info", response_model=SystemInfo)
async def get_system_info():
    """Get system information."""
    return SystemInfo(
        version="0.1.0",
        uptime=3600,
        cpu_usage=25.5,
        memory_usage=45.2,
        disk_usage=60.8,
        camera_count=3,
        online_camera_count=2,
        algorithm_count=5,
        today_alarm_count=10,
    )


@router.get("/logs", response_model=OperationLogListResponse)
async def list_operation_logs(
    user: Optional[str] = Query(None, description="用户筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    resource: Optional[str] = Query(None, description="资源类型筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get operation logs."""
    filtered = mock_logs
    
    if user is not None:
        filtered = [log for log in filtered if log["user"] == user]
    
    if action is not None:
        filtered = [log for log in filtered if log["action"] == action]
    
    if resource is not None:
        filtered = [log for log in filtered if log["resource"] == resource]
    
    total = len(filtered)
    items = filtered[skip : skip + limit]
    
    return OperationLogListResponse(
        total=total,
        items=[OperationLog(**log) for log in items],
    )


@router.get("/settings")
async def get_system_settings():
    """Get system settings."""
    return {
        "site_name": "AI Vision Platform",
        "retention_days": 30,
        "max_cameras": 100,
        "alarm_sound_enabled": True,
        "email_notification_enabled": False,
    }


@router.put("/settings")
async def update_system_settings(settings: dict):
    """Update system settings."""
    # TODO: Implement settings update
    return {"message": "设置已更新"}
