# -*- coding: utf-8 -*-
"""
文件存储 Controller：
- 负责 HTTP 路由、权限校验与入参解析
- 具体存储逻辑委托给 file_service
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends

from app.api.deps import get_current_user, get_current_user_optional
from app.models import User
from app.schemas.common import success_response
from app.services.file_service import (
  upload_temp_file_bytes,
  delete_temp_file_by_key,
  get_temp_file_url,
  get_file_url,
  build_preview_response,
  delete_file_by_key,
)


router = APIRouter()


@router.post("/temp", summary="上传临时文件")
async def upload_temp_file(
  file: UploadFile = File(...),
  category: str = Query(
    "misc",
    description="业务类别: model/avatar/snapshot/video 等，用于归类临时文件",
  ),
  current_user: User = Depends(get_current_user),
):
  data = await file.read()
  key, url = await upload_temp_file_bytes(
    data=data,
    filename=file.filename or "unnamed.bin",
    category=category,
    user_id=str(current_user.id) if getattr(current_user, "id", None) else None,
  )
  return success_response({"key": key, "url": url})


@router.delete("/temp", summary="删除临时文件")
async def delete_temp_file(
  key: str = Query(..., description="临时文件 key，前端从 upload_temp_file 返回中获得"),
  current_user: User = Depends(get_current_user),
):
  delete_temp_file_by_key(key)
  return success_response({"deleted": True})


@router.get("/temp", summary="获取临时文件访问地址")
async def download_temp_file(
  key: str = Query(..., description="临时文件 key"),
  current_user: User = Depends(get_current_user),
):
  url = get_temp_file_url(key)
  return success_response({"key": key, "url": url})


@router.get("", summary="获取正式文件访问地址")
async def download_file(
  key: str = Query(..., description="正式文件 key，比如 models/...、avatars/... 等"),
  current_user: User = Depends(get_current_user),
):
  url = get_file_url(key)
  return success_response({"key": key, "url": url})


@router.get("/preview", summary="正式文件预览（不暴露存储真实地址）")
async def preview_file(
  filepath: str = Query(..., description="正式文件 key，比如 alarm/...、models/... 等"),
  variant: str = Query("origin", description="图片变体: origin/thumb（默认 origin）"),
  token: Optional[str] = Query(None, description="可选：通过 query 传递 access token（用于图片/视频标签预览）"),
  current_user: Optional[User] = Depends(get_current_user_optional),
):
  resp = await build_preview_response(
    filepath=filepath,
    variant=variant,
    token=token,
    has_header_user=current_user is not None,
  )
  return resp


@router.delete("", summary="删除正式文件")
async def delete_file(
  key: str = Query(..., description="正式文件 key，比如 models/...、avatars/... 等"),
  current_user: User = Depends(get_current_user),
):
  delete_file_by_key(key)
  return success_response({"deleted": True})

