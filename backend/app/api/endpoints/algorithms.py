"""
Algorithm management endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class AlgorithmBase(BaseModel):
    """Algorithm base model."""
    name: str
    code: str
    category: str  # detection, classification, segmentation
    description: Optional[str] = None
    model_path: Optional[str] = None


class AlgorithmCreate(AlgorithmBase):
    """Algorithm creation model."""
    pass


class AlgorithmUpdate(BaseModel):
    """Algorithm update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    config: Optional[dict] = None


class AlgorithmResponse(AlgorithmBase):
    """Algorithm response model."""
    id: int
    is_enabled: bool = True
    config: dict = {}
    usage_count: int = 0
    
    class Config:
        from_attributes = True


class AlgorithmListResponse(BaseModel):
    """Algorithm list response."""
    total: int
    items: List[AlgorithmResponse]


# Mock data
mock_algorithms = [
    {
        "id": 1,
        "name": "人员入侵检测",
        "code": "person_intrusion",
        "category": "detection",
        "description": "检测指定区域内的人员入侵行为",
        "is_enabled": True,
        "config": {"confidence_threshold": 0.5, "alert_cooldown": 30},
        "usage_count": 5,
    },
    {
        "id": 2,
        "name": "烟火检测",
        "code": "fire_smoke",
        "category": "detection",
        "description": "检测画面中的烟雾和火焰",
        "is_enabled": True,
        "config": {"confidence_threshold": 0.6},
        "usage_count": 3,
    },
    {
        "id": 3,
        "name": "安全帽检测",
        "code": "helmet_detection",
        "category": "detection",
        "description": "检测人员是否佩戴安全帽",
        "is_enabled": True,
        "config": {"confidence_threshold": 0.5},
        "usage_count": 2,
    },
    {
        "id": 4,
        "name": "人员聚集检测",
        "code": "crowd_detection",
        "category": "detection",
        "description": "检测区域内人员聚集情况",
        "is_enabled": False,
        "config": {"min_count": 5, "confidence_threshold": 0.5},
        "usage_count": 0,
    },
    {
        "id": 5,
        "name": "离岗检测",
        "code": "absence_detection",
        "category": "detection",
        "description": "检测指定岗位人员离岗情况",
        "is_enabled": True,
        "config": {"absence_threshold": 300},
        "usage_count": 1,
    },
]


@router.get("", response_model=AlgorithmListResponse)
async def list_algorithms(
    category: Optional[str] = Query(None, description="算法类别筛选"),
    is_enabled: Optional[bool] = Query(None, description="是否启用筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get algorithm list."""
    filtered = mock_algorithms
    
    if category is not None:
        filtered = [a for a in filtered if a["category"] == category]
    
    if is_enabled is not None:
        filtered = [a for a in filtered if a["is_enabled"] == is_enabled]
    
    total = len(filtered)
    items = filtered[skip : skip + limit]
    
    return AlgorithmListResponse(
        total=total,
        items=[AlgorithmResponse(**a) for a in items],
    )


@router.get("/{algorithm_id}", response_model=AlgorithmResponse)
async def get_algorithm(algorithm_id: int):
    """Get algorithm by ID."""
    for algo in mock_algorithms:
        if algo["id"] == algorithm_id:
            return AlgorithmResponse(**algo)
    
    raise HTTPException(status_code=404, detail="算法不存在")


@router.put("/{algorithm_id}", response_model=AlgorithmResponse)
async def update_algorithm(algorithm_id: int, algorithm_update: AlgorithmUpdate):
    """Update algorithm."""
    for i, algo in enumerate(mock_algorithms):
        if algo["id"] == algorithm_id:
            update_data = algorithm_update.model_dump(exclude_unset=True)
            mock_algorithms[i].update(update_data)
            return AlgorithmResponse(**mock_algorithms[i])
    
    raise HTTPException(status_code=404, detail="算法不存在")


@router.post("/{algorithm_id}/enable")
async def enable_algorithm(algorithm_id: int):
    """Enable algorithm."""
    for i, algo in enumerate(mock_algorithms):
        if algo["id"] == algorithm_id:
            mock_algorithms[i]["is_enabled"] = True
            return {"message": "算法已启用"}
    
    raise HTTPException(status_code=404, detail="算法不存在")


@router.post("/{algorithm_id}/disable")
async def disable_algorithm(algorithm_id: int):
    """Disable algorithm."""
    for i, algo in enumerate(mock_algorithms):
        if algo["id"] == algorithm_id:
            mock_algorithms[i]["is_enabled"] = False
            return {"message": "算法已禁用"}
    
    raise HTTPException(status_code=404, detail="算法不存在")
