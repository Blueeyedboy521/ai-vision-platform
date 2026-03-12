# -*- coding: utf-8 -*-
"""
推送配置管理 API

包含：
- endpoints（通道实例）
- templates（模板）
- policies（路由策略）
- delivery logs（审计）
- test send（测试发送）
"""

from __future__ import annotations

import json
from typing import Optional, List, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.models.notification import (
    NotificationEndpoint,
    NotificationTemplate,
    NotificationPolicy,
    NotificationDeliveryLog,
)
from app.models import Camera, Algorithm
from app.models.base import generate_uuid
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
from app.services.notification_crypto import (
    encrypt_config,
    decrypt_config,
    mask_config,
    merge_update_config,
)
from config.settings import settings
from common.logging import logger


router = APIRouter()

_CATEGORY_CN = {"ai": "业务告警", "system": "系统告警"}
_LEVEL_CN = {"info": "提示", "warning": "一般", "danger": "严重", "critical": "致命"}
_PROVIDER_CN = {"dingtalk_bot": "钉钉", "wecom_bot": "企微"}


async def _get_name_by_id(
    db: AsyncSession,
    model,
    _id: Optional[str],
    name_field: str = "name",
) -> Optional[str]:
    if not _id:
        return None
    result = await db.execute(select(model).where(model.id == _id))
    row = result.scalar_one_or_none()
    return getattr(row, name_field, None) if row else None


async def _get_endpoint_meta(db: AsyncSession, endpoint_id: str) -> tuple[Optional[str], Optional[str]]:
    if not endpoint_id:
        return None, None
    result = await db.execute(select(NotificationEndpoint).where(NotificationEndpoint.id == endpoint_id))
    row = result.scalar_one_or_none()
    if row is None:
        return None, None
    return getattr(row, "provider", None), getattr(row, "name", None)


def _format_time_window(tw: Any) -> Optional[str]:
    if not isinstance(tw, dict):
        return None
    start = str(tw.get("start") or "").strip()
    end = str(tw.get("end") or "").strip()
    if not start or not end:
        return None
    return f"{start}-{end}"


async def _build_policy_desc(
    db: AsyncSession,
    match: Dict[str, Any],
    actions: Any,
) -> tuple[str, str]:
    m = match or {}

    def _as_list(v: Any) -> list:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [v]

    def _format_area_items(paths: Any) -> list[str]:
        items: list[str] = []
        for raw in _as_list(paths):
            p = str(raw or "").strip()
            if not p:
                continue
            is_wild = "*" in p or "?" in p
            # 去掉末尾通配符，取有意义的段
            clean = p.rstrip("*").rstrip("/").strip()
            segs = [s for s in clean.split("/") if s]
            if not segs:
                continue
            # 更偏业务的展示：尽量显示最后两段（如 冲压车间产线2）
            name = "".join(segs[-2:]) if len(segs) >= 2 else segs[-1]
            suffix = "（含子区域）" if is_wild else "（仅本区域）"
            items.append(f"{name}{suffix}")
        return items

    parts: list[str] = []
    cat = str(m.get("category") or "").strip()
    if cat:
        parts.append(_CATEGORY_CN.get(cat, cat))
    alarm_types = m.get("alarm_type")
    if isinstance(alarm_types, list):
        ats = [str(x).strip() for x in alarm_types if str(x).strip()]
        if ats:
            parts.append("、".join(ats))
    elif alarm_types:
        parts.append(str(alarm_types).strip())

    levels = m.get("level")
    if isinstance(levels, list):
        ls = [str(x).strip() for x in levels if str(x).strip()]
        if ls:
            parts.append("、".join(_LEVEL_CN.get(x, x) for x in ls))
    elif levels:
        lvl = str(levels).strip()
        if lvl:
            parts.append(_LEVEL_CN.get(lvl, lvl))

    area_paths = m.get("area_path")
    area_items = _format_area_items(area_paths)
    if area_items:
        parts.append("、".join(area_items))

    cam_ids = m.get("camera_id")
    if isinstance(cam_ids, list):
        names: list[str] = []
        for cid in cam_ids:
            cid_s = str(cid).strip()
            if not cid_s:
                continue
            n = await _get_name_by_id(db, Camera, cid_s)
            names.append(n or cid_s)
        if names:
            parts.append("摄像头：" + "、".join(names))
    elif cam_ids:
        cam_id = str(cam_ids).strip()
        cam_name = await _get_name_by_id(db, Camera, cam_id)
        if cam_id:
            parts.append("摄像头：" + str(cam_name or cam_id))

    algo_ids = m.get("algorithm_id")
    if isinstance(algo_ids, list):
        names = []
        for aid in algo_ids:
            aid_s = str(aid).strip()
            if not aid_s:
                continue
            n = await _get_name_by_id(db, Algorithm, aid_s)
            names.append(n or aid_s)
        if names:
            parts.append("算法：" + "、".join(names))
    elif algo_ids:
        algo_id = str(algo_ids).strip()
        algo_name = await _get_name_by_id(db, Algorithm, algo_id)
        if algo_id:
            parts.append("算法：" + str(algo_name or algo_id))

    tw = _format_time_window(m.get("time_window"))
    parts.append(f"（{tw}）" if tw else "（全天生效）")

    # exclude 描述（可选）
    ex = m.get("exclude") if isinstance(m.get("exclude"), dict) else {}
    if ex:
        ex_parts: list[str] = []
        ex_areas = _format_area_items(ex.get("area_path"))
        if ex_areas:
            ex_parts.append("区域=" + "、".join(ex_areas))
        for k, label in (("camera_id", "摄像头"), ("algorithm_id", "算法"), ("alarm_type", "类型"), ("level", "等级")):
            vals = [str(x).strip() for x in _as_list(ex.get(k)) if str(x).strip()]
            if vals:
                if k == "level":
                    vals = [_LEVEL_CN.get(x, x) for x in vals]
                ex_parts.append(label + "=" + "、".join(vals))
        if ex_parts:
            parts.append("排除：" + "；".join(ex_parts))

    match_desc = "-".join([p for p in parts if p]) if parts else "（无匹配条件）"

    acts: list[dict] = []
    if isinstance(actions, list):
        acts = [a for a in actions if isinstance(a, dict)]
    elif isinstance(actions, dict):
        acts = [actions]

    act_descs: list[str] = []
    for a in acts:
        endpoint_ids = a.get("endpoint_ids") or []
        if not isinstance(endpoint_ids, list):
            endpoint_ids = []
        # 解析 endpoint 名称与 provider
        ep_names: list[str] = []
        providers: list[str] = []
        for eid in endpoint_ids:
            pid, nm = await _get_endpoint_meta(db, str(eid))
            if pid:
                providers.append(str(pid))
            ep_names.append(nm or str(eid))
        tmpl_id = a.get("template_id")
        tmpl_name = await _get_name_by_id(db, NotificationTemplate, str(tmpl_id)) if tmpl_id else None
        throttle = int(a.get("throttle_sec") or a.get("throttle") or 0)
        retry_times = int(a.get("retry_times") or 0)
        retry_interval = int(a.get("retry_interval_sec") or 0)

        provider_cn = None
        if providers and len(set(providers)) == 1:
            provider_cn = _PROVIDER_CN.get(providers[0], providers[0])

        head = "推"
        if provider_cn:
            head += provider_cn + "-"
        head += "、".join(ep_names) if ep_names else "-"

        details: list[str] = []
        if tmpl_id:
            details.append(str(tmpl_name or tmpl_id))
        if throttle > 0:
            details.append(f"{throttle}秒节流")
        else:
            details.append("不限流")
        if retry_times > 0:
            if retry_interval > 0:
                details.append(f"重试{retry_times}次/{retry_interval}s")
            else:
                details.append(f"重试{retry_times}次")

        s = head + f"（{'，'.join(details)}）"
        act_descs.append(s)

    actions_desc = "；".join(act_descs) if act_descs else "（无动作）"
    return match_desc, actions_desc


@router.get("/endpoints", summary="获取推送通道列表")
async def list_endpoints(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationEndpoint).order_by(NotificationEndpoint.created_at.desc()))
    rows = result.scalars().all()
    data = []
    for r in rows:
        try:
            cfg = decrypt_config(r.encrypted_config)
        except Exception:
            cfg = {}
        data.append(
            {
                "id": r.id,
                "name": r.name,
                "provider": r.provider,
                "is_enabled": r.is_enabled,
                "config_masked": mask_config(r.provider, cfg),
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
        )
    return success_response(data)


@router.post("/endpoints", summary="创建推送通道")
async def create_endpoint(
    payload: NotificationEndpointCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cfg = payload.config or {}
    enc = encrypt_config(cfg)
    hint = json.dumps(mask_config(payload.provider, cfg), ensure_ascii=False)
    row = NotificationEndpoint(
        id=generate_uuid(),
        name=payload.name,
        provider=payload.provider,
        is_enabled=payload.is_enabled,
        encrypted_config=enc,
        config_hint=hint,
    )
    db.add(row)
    await db.commit()
    return success_response({"id": row.id})


@router.put("/endpoints/{endpoint_id}", summary="更新推送通道")
async def update_endpoint(
    endpoint_id: str,
    payload: NotificationEndpointUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationEndpoint).where(NotificationEndpoint.id == endpoint_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="通道不存在")

    if payload.name is not None:
        row.name = payload.name
    if payload.is_enabled is not None:
        row.is_enabled = payload.is_enabled

    if payload.config is not None:
        old = {}
        try:
            old = decrypt_config(row.encrypted_config)
        except Exception:
            old = {}
        merged = merge_update_config(row.provider, old, payload.config)
        row.encrypted_config = encrypt_config(merged)
        row.config_hint = json.dumps(mask_config(row.provider, merged), ensure_ascii=False)

    await db.commit()
    return success_response({"updated": True})


@router.get("/templates", summary="获取推送模板列表")
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationTemplate).order_by(NotificationTemplate.created_at.desc()))
    rows = result.scalars().all()
    data = [
        {
            "id": r.id,
            "name": r.name,
            "type": r.type,
            "is_enabled": r.is_enabled,
            "content": r.content,
        }
        for r in rows
    ]
    return success_response(data)


@router.post("/templates", summary="创建推送模板")
async def create_template(
    payload: NotificationTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = NotificationTemplate(
        id=generate_uuid(),
        name=payload.name,
        type=payload.type,
        is_enabled=payload.is_enabled,
        content=payload.content or {},
    )
    db.add(row)
    await db.commit()
    return success_response({"id": row.id})


@router.put("/templates/{template_id}", summary="更新推送模板")
async def update_template(
    template_id: str,
    payload: NotificationTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationTemplate).where(NotificationTemplate.id == template_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="模板不存在")
    if payload.name is not None:
        row.name = payload.name
    if payload.is_enabled is not None:
        row.is_enabled = payload.is_enabled
    if payload.content is not None:
        row.content = payload.content
    await db.commit()
    return success_response({"updated": True})


@router.get("/policies", summary="获取推送策略列表")
async def list_policies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationPolicy).order_by(NotificationPolicy.priority.asc()))
    rows = result.scalars().all()
    data = [
        {
            "id": r.id,
            "name": r.name,
            "priority": r.priority,
            "is_enabled": r.is_enabled,
            "match": r.match,
            "actions": r.actions,
            "match_desc": r.match_desc,
            "actions_desc": r.actions_desc,
        }
        for r in rows
    ]
    return success_response(data)


@router.post("/policies", summary="创建推送策略")
async def create_policy(
    payload: NotificationPolicyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actions = payload.actions or []
    # 兼容：旧形态为 dict 时包装成 list
    if isinstance(actions, dict):
        actions = [actions]
    match_desc, actions_desc = await _build_policy_desc(db, payload.match or {}, actions)
    row = NotificationPolicy(
        id=generate_uuid(),
        name=payload.name,
        priority=payload.priority,
        is_enabled=payload.is_enabled,
        match=payload.match or {},
        actions=actions,
        match_desc=match_desc,
        actions_desc=actions_desc,
    )
    db.add(row)
    await db.commit()
    return success_response({"id": row.id})


@router.put("/policies/{policy_id}", summary="更新推送策略")
async def update_policy(
    policy_id: str,
    payload: NotificationPolicyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationPolicy).where(NotificationPolicy.id == policy_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="策略不存在")
    if payload.name is not None:
        row.name = payload.name
    if payload.priority is not None:
        row.priority = payload.priority
    if payload.is_enabled is not None:
        row.is_enabled = payload.is_enabled
    if payload.match is not None:
        row.match = payload.match
    if payload.actions is not None:
        actions = payload.actions
        if isinstance(actions, dict):
            actions = [actions]
        row.actions = actions

    # 任何 match/actions 变更后，都重算描述（也允许仅改 name/priority 时保留原描述）
    if payload.match is not None or payload.actions is not None:
        match_desc, actions_desc = await _build_policy_desc(db, row.match or {}, row.actions or {})
        row.match_desc = match_desc
        row.actions_desc = actions_desc
    await db.commit()
    return success_response({"updated": True})


@router.get("/delivery-logs", summary="获取推送审计日志（分页）")
async def list_delivery_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(NotificationDeliveryLog).order_by(NotificationDeliveryLog.created_at.desc())
    total_res = await db.execute(select(func.count(NotificationDeliveryLog.id)))
    total = total_res.scalar() or 0
    res = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    rows = res.scalars().all()
    items = [
        {
            "id": r.id,
            "alarm_id": r.alarm_id,
            "category": r.category,
            "alarm_type": r.alarm_type,
            "level": r.level,
            "endpoint_id": r.endpoint_id,
            "provider": r.provider,
            "template_id": r.template_id,
            "status": r.status,
            "error": r.error,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return page_response(items, page, page_size, total)


@router.post("/test-send", summary="测试发送（入队异步推送）")
async def test_send(
    payload: NotificationTestSendRequest,
    current_user: User = Depends(get_current_user),
):
    import redis as _redis

    r = _redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        event = {
            "category": payload.category,
            "alarm_id": f"test_{generate_uuid()}",
            "alarm_type": payload.alarm_type,
            "level": payload.level,
            "camera_id": None,
            "camera_name": None,
            "area_name": None,
            "algorithm_id": None,
            "algorithm_name": None,
            "title": payload.title,
            "text": payload.text,
            "image_url": payload.image_url,
            "link_url": payload.link_url,
            # 让策略能精确命中：携带指定 endpoint/template（MVP：policy 里可直接写固定 endpoint_ids/template_id）
        }
        r.rpush(settings.NOTIFICATION_QUEUE_NAME, json.dumps(event, ensure_ascii=False))
    finally:
        r.close()
    return success_response({"queued": True})

