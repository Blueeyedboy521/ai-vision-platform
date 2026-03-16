# -*- coding: utf-8 -*-
"""
模型 API Controller：
- 只负责路由、参数与权限校验
- 具体业务逻辑委托给 model_service
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_admin
from app.models import User
from app.schemas.model import ModelCreate, ModelUpdate
from app.schemas.common import success_response, page_response
from app.services.model_service import (
  list_models,
  get_model_detail,
  create_model_with_algorithms,
  update_model_data,
  delete_model_data,
)


router = APIRouter()


@router.get("", summary="获取模型列表")
async def get_models(
  page: int = Query(1, ge=1, description="页码"),
  page_size: int = Query(20, ge=1, le=100, description="每页数量"),
  keyword: Optional[str] = Query(None, description="关键词"),
  is_enabled: Optional[bool] = Query(None, description="是否启用"),
  current_user: User = Depends(get_current_user),
  db: AsyncSession = Depends(get_db),
):
  data, total = await list_models(db, page, page_size, keyword, is_enabled)
  return page_response(data, page, page_size, total)


@router.get("/{model_id}", summary="获取模型详情")
async def get_model(
  model_id: str,
  current_user: User = Depends(get_current_user),
  db: AsyncSession = Depends(get_db),
):
  detail = await get_model_detail(db, model_id)
  if detail is None:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="模型不存在",
    )
  return success_response(detail)


@router.post("", summary="创建模型")
async def create_model(
  model_data: ModelCreate,
  current_user: User = Depends(get_current_admin),
  db: AsyncSession = Depends(get_db),
):
  try:
    model_id, algo_count = await create_model_with_algorithms(db, model_data, current_user)
  except ValueError as e:
    if str(e) == "MODEL_CODE_EXISTS":
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="模型编码已存在",
      )
    raise
  return success_response({"id": model_id}, "创建成功")


@router.put("/{model_id}", summary="更新模型")
async def update_model(
  model_id: str,
  model_data: ModelUpdate,
  current_user: User = Depends(get_current_admin),
  db: AsyncSession = Depends(get_db),
):
  ok = await update_model_data(db, model_id, model_data, current_user)
  if not ok:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="模型不存在",
    )
  return success_response(None, "更新成功")


@router.delete("/{model_id}", summary="删除模型")
async def delete_model(
  model_id: str,
  current_user: User = Depends(get_current_admin),
  db: AsyncSession = Depends(get_db),
):
  ok, reason = await delete_model_data(db, model_id)
  if not ok:
    if reason == "NOT_FOUND":
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="模型不存在",
      )
    if reason == "HAS_ALGORITHMS":
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="存在关联的算法，无法删除",
      )
  return success_response(None, "删除成功")

