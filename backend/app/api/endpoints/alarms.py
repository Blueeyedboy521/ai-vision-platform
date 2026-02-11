"""
Alarm management endpoints.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class AlarmBase(BaseModel):
    """Alarm base model."""
    camera_id: int
    algorithm_id: int
    level: str  # info, warning, danger
    title: str
    description: Optional[str] = None


class AlarmResponse(AlarmBase):
    """Alarm response model."""
    id: int
    camera_name: str
    algorithm_name: str
    status: str = "pending"  # pending, confirmed, resolved, ignored
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlarmListResponse(BaseModel):
    """Alarm list response."""
    total: int
    items: List[AlarmResponse]


class AlarmStats(BaseModel):
    """Alarm statistics."""
    total: int
    pending: int
    confirmed: int
    resolved: int
    today_count: int
    danger_count: int
    warning_count: int


# Mock data
mock_alarms = [
    {
        "id": 1,
        "camera_id": 1,
        "camera_name": "大厅摄像头-01",
        "algorithm_id": 1,
        "algorithm_name": "人员入侵检测",
        "level": "danger",
        "title": "检测到人员入侵",
        "description": "在禁入区域检测到人员活动",
        "status": "pending",
        "image_url": "/alarm-001.jpg",
        "created_at": datetime.now(),
    },
    {
        "id": 2,
        "camera_id": 2,
        "camera_name": "大厅摄像头-02",
        "algorithm_id": 2,
        "algorithm_name": "烟火检测",
        "level": "warning",
        "title": "检测到烟雾",
        "description": "画面中检测到疑似烟雾",
        "status": "confirmed",
        "image_url": "/alarm-002.jpg",
        "created_at": datetime.now(),
    },
]


@router.get("", response_model=AlarmListResponse)
async def list_alarms(
    camera_id: Optional[int] = Query(None, description="摄像头ID筛选"),
    level: Optional[str] = Query(None, description="告警级别筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get alarm list."""
    filtered = mock_alarms
    
    if camera_id is not None:
        filtered = [a for a in filtered if a["camera_id"] == camera_id]
    
    if level is not None:
        filtered = [a for a in filtered if a["level"] == level]
    
    if status is not None:
        filtered = [a for a in filtered if a["status"] == status]
    
    total = len(filtered)
    items = filtered[skip : skip + limit]
    
    return AlarmListResponse(
        total=total,
        items=[AlarmResponse(**a) for a in items],
    )


@router.get("/stats", response_model=AlarmStats)
async def get_alarm_stats():
    """Get alarm statistics."""
    return AlarmStats(
        total=len(mock_alarms),
        pending=len([a for a in mock_alarms if a["status"] == "pending"]),
        confirmed=len([a for a in mock_alarms if a["status"] == "confirmed"]),
        resolved=len([a for a in mock_alarms if a["status"] == "resolved"]),
        today_count=len(mock_alarms),
        danger_count=len([a for a in mock_alarms if a["level"] == "danger"]),
        warning_count=len([a for a in mock_alarms if a["level"] == "warning"]),
    )


@router.get("/{alarm_id}", response_model=AlarmResponse)
async def get_alarm(alarm_id: int):
    """Get alarm by ID."""
    for alarm in mock_alarms:
        if alarm["id"] == alarm_id:
            return AlarmResponse(**alarm)
    
    raise HTTPException(status_code=404, detail="告警不存在")


@router.put("/{alarm_id}/status")
async def update_alarm_status(alarm_id: int, status: str):
    """Update alarm status."""
    valid_statuses = ["pending", "confirmed", "resolved", "ignored"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效的状态，可选值: {valid_statuses}")
    
    for i, alarm in enumerate(mock_alarms):
        if alarm["id"] == alarm_id:
            mock_alarms[i]["status"] = status
            if status == "resolved":
                mock_alarms[i]["resolved_at"] = datetime.now()
            return {"message": "状态更新成功"}
    
    raise HTTPException(status_code=404, detail="告警不存在")


@router.delete("/{alarm_id}")
async def delete_alarm(alarm_id: int):
    """Delete alarm."""
    for i, alarm in enumerate(mock_alarms):
        if alarm["id"] == alarm_id:
            mock_alarms.pop(i)
            return {"message": "删除成功"}
    
    raise HTTPException(status_code=404, detail="告警不存在")
