# -*- coding: utf-8 -*-
"""
推送配置管理 Controller

职责：
- 定义 FastAPI 路由与入参 / 权限校验
- 调用 notification_config_service 完成具体业务逻辑
- 使用通用的 success_response / page_response 进行返回包装
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.common import success_response, page_response
from app.schemas.notification import (
    NotificationEndpointCreate,
    NotificationEndpointUpdate,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationPolicyCreate,
    NotificationPolicyUpdate,
    NotificationTestSendRequest,
)
from app.services.notification_config_service import (
    list_endpoints,
    create_endpoint,
    update_endpoint,
    delete_endpoint,
    list_templates,
    create_template,
    update_template,
    delete_template,
    list_policies,
    get_policy,
    create_policy,
    update_policy,
    delete_policy,
    list_delivery_logs,
    build_test_event,
)
from app.services.notification_service import enqueue_notification_event


router = APIRouter()


@router.get("/endpoints", summary="获取推送通道列表")
async def list_endpoints_api(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await list_endpoints(db)
    return success_response(data)


@router.post("/endpoints", summary="创建推送通道")
async def create_endpoint_api(
    payload: NotificationEndpointCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    endpoint_id = await create_endpoint(db, payload)
    return success_response({"id": endpoint_id})


@router.put("/endpoints/{endpoint_id}", summary="更新推送通道")
async def update_endpoint_api(
    endpoint_id: str,
    payload: NotificationEndpointUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await update_endpoint(db, endpoint_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="通道不存在")
    return success_response({"updated": True})


@router.delete("/endpoints/{endpoint_id}", summary="删除推送通道")
async def delete_endpoint_api(
    endpoint_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_endpoint(db, endpoint_id)
    if not ok:
        raise HTTPException(status_code=404, detail="通道不存在")
    return success_response({"deleted": True})


@router.get("/templates", summary="获取推送模板列表")
async def list_templates_api(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await list_templates(db)
    return success_response(data)


@router.post("/templates", summary="创建推送模板")
async def create_template_api(
    payload: NotificationTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template_id = await create_template(db, payload)
    return success_response({"id": template_id})


@router.put("/templates/{template_id}", summary="更新推送模板")
async def update_template_api(
    template_id: str,
    payload: NotificationTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await update_template(db, template_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="模板不存在")
    return success_response({"updated": True})


@router.delete("/templates/{template_id}", summary="删除推送模板")
async def delete_template_api(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_template(db, template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="模板不存在")
    return success_response({"deleted": True})


@router.get("/policies", summary="获取推送策略列表")
async def list_policies_api(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await list_policies(db)
    return success_response(data)


@router.get("/policies/{policy_id}", summary="获取推送策略详情")
async def get_policy_api(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_policy(db, policy_id)
    if data is None:
        raise HTTPException(status_code=404, detail="策略不存在")
    return success_response(data)


@router.post("/policies", summary="创建推送策略")
async def create_policy_api(
    payload: NotificationPolicyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policy_id = await create_policy(db, payload)
    return success_response({"id": policy_id})


@router.put("/policies/{policy_id}", summary="更新推送策略")
async def update_policy_api(
    policy_id: str,
    payload: NotificationPolicyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await update_policy(db, policy_id, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="策略不存在")
    return success_response({"updated": True})


@router.delete("/policies/{policy_id}", summary="删除推送策略")
async def delete_policy_api(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_policy(db, policy_id)
    if not ok:
        raise HTTPException(status_code=404, detail="策略不存在")
    return success_response({"deleted": True})


@router.get("/delivery-logs", summary="获取推送审计日志（分页）")
async def list_delivery_logs_api(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_delivery_logs(db, page, page_size)
    return page_response(items, page, page_size, total)


@router.post("/test-send", summary="测试发送（入队异步推送）")
async def test_send_api(
    payload: NotificationTestSendRequest,
    current_user: User = Depends(get_current_user),
):
    event = build_test_event(payload)
    enqueue_notification_event(event)
    return success_response({"queued": True})

