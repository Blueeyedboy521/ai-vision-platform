"""
Camera management endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class CameraBase(BaseModel):
    """Camera base model."""
    name: str
    rtsp_url: str
    area_id: Optional[int] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CameraCreate(CameraBase):
    """Camera creation model."""
    pass


class CameraUpdate(BaseModel):
    """Camera update model."""
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    area_id: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None


class CameraResponse(CameraBase):
    """Camera response model."""
    id: int
    status: str = "offline"  # online, offline, error
    thumbnail_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class CameraListResponse(BaseModel):
    """Camera list response."""
    total: int
    items: List[CameraResponse]


# Mock data
mock_cameras = [
    {
        "id": 1,
        "name": "大厅摄像头-01",
        "rtsp_url": "rtsp://192.168.1.100:554/stream1",
        "area_id": 1,
        "description": "一楼大厅入口",
        "status": "online",
        "thumbnail_url": "/camera-lobby-01.jpg",
    },
    {
        "id": 2,
        "name": "大厅摄像头-02",
        "rtsp_url": "rtsp://192.168.1.101:554/stream1",
        "area_id": 1,
        "description": "一楼大厅出口",
        "status": "online",
        "thumbnail_url": "/camera-lobby-02.jpg",
    },
    {
        "id": 3,
        "name": "办公区摄像头-01",
        "rtsp_url": "rtsp://192.168.1.102:554/stream1",
        "area_id": 2,
        "description": "二楼办公区",
        "status": "offline",
        "thumbnail_url": "/camera-office-01.jpg",
    },
]


@router.get("", response_model=CameraListResponse)
async def list_cameras(
    area_id: Optional[int] = Query(None, description="区域ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get camera list."""
    filtered = mock_cameras
    
    if area_id is not None:
        filtered = [c for c in filtered if c["area_id"] == area_id]
    
    if status is not None:
        filtered = [c for c in filtered if c["status"] == status]
    
    total = len(filtered)
    items = filtered[skip : skip + limit]
    
    return CameraListResponse(
        total=total,
        items=[CameraResponse(**c) for c in items],
    )


@router.post("", response_model=CameraResponse)
async def create_camera(camera: CameraCreate):
    """Create a new camera."""
    new_id = max(c["id"] for c in mock_cameras) + 1 if mock_cameras else 1
    
    new_camera = {
        "id": new_id,
        **camera.model_dump(),
        "status": "offline",
        "thumbnail_url": None,
    }
    mock_cameras.append(new_camera)
    
    return CameraResponse(**new_camera)


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: int):
    """Get camera by ID."""
    for camera in mock_cameras:
        if camera["id"] == camera_id:
            return CameraResponse(**camera)
    
    raise HTTPException(status_code=404, detail="摄像头不存在")


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(camera_id: int, camera_update: CameraUpdate):
    """Update camera."""
    for i, camera in enumerate(mock_cameras):
        if camera["id"] == camera_id:
            update_data = camera_update.model_dump(exclude_unset=True)
            mock_cameras[i].update(update_data)
            return CameraResponse(**mock_cameras[i])
    
    raise HTTPException(status_code=404, detail="摄像头不存在")


@router.delete("/{camera_id}")
async def delete_camera(camera_id: int):
    """Delete camera."""
    for i, camera in enumerate(mock_cameras):
        if camera["id"] == camera_id:
            mock_cameras.pop(i)
            return {"message": "删除成功"}
    
    raise HTTPException(status_code=404, detail="摄像头不存在")


@router.post("/{camera_id}/test")
async def test_camera_connection(camera_id: int):
    """Test camera RTSP connection."""
    for camera in mock_cameras:
        if camera["id"] == camera_id:
            # TODO: Implement actual RTSP connection test
            return {"success": True, "message": "连接成功"}
    
    raise HTTPException(status_code=404, detail="摄像头不存在")
