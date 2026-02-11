"""
Area management endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class AreaBase(BaseModel):
    """Area base model."""
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None


class AreaCreate(AreaBase):
    """Area creation model."""
    pass


class AreaUpdate(BaseModel):
    """Area update model."""
    name: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None


class AreaResponse(AreaBase):
    """Area response model."""
    id: int
    camera_count: int = 0
    children: List["AreaResponse"] = []
    
    class Config:
        from_attributes = True


# Mock data
mock_areas = [
    {"id": 1, "name": "一楼", "parent_id": None, "description": "一楼区域", "camera_count": 2},
    {"id": 2, "name": "二楼", "parent_id": None, "description": "二楼区域", "camera_count": 1},
    {"id": 3, "name": "大厅", "parent_id": 1, "description": "一楼大厅", "camera_count": 2},
    {"id": 4, "name": "办公区", "parent_id": 2, "description": "二楼办公区", "camera_count": 1},
]


def build_tree(areas: List[dict], parent_id: Optional[int] = None) -> List[dict]:
    """Build area tree structure."""
    result = []
    for area in areas:
        if area["parent_id"] == parent_id:
            children = build_tree(areas, area["id"])
            area_copy = area.copy()
            area_copy["children"] = children
            result.append(area_copy)
    return result


@router.get("", response_model=List[AreaResponse])
async def list_areas(flat: bool = False):
    """Get area list (tree structure by default)."""
    if flat:
        return [AreaResponse(**a, children=[]) for a in mock_areas]
    
    tree = build_tree(mock_areas)
    return [AreaResponse(**a) for a in tree]


@router.post("", response_model=AreaResponse)
async def create_area(area: AreaCreate):
    """Create a new area."""
    new_id = max(a["id"] for a in mock_areas) + 1 if mock_areas else 1
    
    new_area = {
        "id": new_id,
        **area.model_dump(),
        "camera_count": 0,
    }
    mock_areas.append(new_area)
    
    return AreaResponse(**new_area, children=[])


@router.get("/{area_id}", response_model=AreaResponse)
async def get_area(area_id: int):
    """Get area by ID."""
    for area in mock_areas:
        if area["id"] == area_id:
            children = build_tree(mock_areas, area_id)
            return AreaResponse(**area, children=children)
    
    raise HTTPException(status_code=404, detail="区域不存在")


@router.put("/{area_id}", response_model=AreaResponse)
async def update_area(area_id: int, area_update: AreaUpdate):
    """Update area."""
    for i, area in enumerate(mock_areas):
        if area["id"] == area_id:
            update_data = area_update.model_dump(exclude_unset=True)
            mock_areas[i].update(update_data)
            return AreaResponse(**mock_areas[i], children=[])
    
    raise HTTPException(status_code=404, detail="区域不存在")


@router.delete("/{area_id}")
async def delete_area(area_id: int):
    """Delete area."""
    # Check if area has children
    for area in mock_areas:
        if area["parent_id"] == area_id:
            raise HTTPException(status_code=400, detail="该区域下有子区域，无法删除")
    
    for i, area in enumerate(mock_areas):
        if area["id"] == area_id:
            mock_areas.pop(i)
            return {"message": "删除成功"}
    
    raise HTTPException(status_code=404, detail="区域不存在")
