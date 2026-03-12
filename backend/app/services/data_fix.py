# -*- coding: utf-8 -*-
"""
启动期数据修复（幂等）

用于补齐：
- areas.level / areas.hierarchy_path
- alarms.camera_name / alarms.algorithm_name / alarms.area_name(层级路径)

注意：
- 该修复可重复运行，适合作为启动期一次性补丁；
- 若数据库缺少相关字段会捕获异常并记录日志，不影响应用启动（但你仍应执行 DDL）。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Area
from common.logging import logger


async def fix_area_hierarchy(session: AsyncSession) -> int:
    """
    计算并回填所有 Area 的 level/hierarchy_path。
    返回更新的记录数（估算）。
    """
    result = await session.execute(select(Area))
    areas: List[Area] = result.scalars().all()
    if not areas:
        return 0

    by_id: Dict[str, Area] = {a.id: a for a in areas}
    children: Dict[Optional[str], List[Area]] = {}
    for a in areas:
        children.setdefault(a.parent_id, []).append(a)

    updated = 0

    def dfs(node: Area) -> None:
        nonlocal updated
        for ch in children.get(node.id, []):
            before_level = getattr(ch, "level", None)
            before_path = getattr(ch, "hierarchy_path", None)
            ch.compute_hierarchy(node)
            if before_level != ch.level or before_path != ch.hierarchy_path:
                updated += 1
            dfs(ch)

    # roots
    roots = children.get(None, [])
    for r in roots:
        before_level = getattr(r, "level", None)
        before_path = getattr(r, "hierarchy_path", None)
        r.compute_hierarchy(None)
        if before_level != r.level or before_path != r.hierarchy_path:
            updated += 1
        dfs(r)

    await session.commit()
    return updated


async def fix_alarm_denormalized_fields(session: AsyncSession) -> None:
    """
    批量回填 alarms 的冗余字段。
    使用 SQL JOIN 更新（MySQL），失败则仅记录日志（不影响启动）。
    """
    # 1) camera_name
    try:
        await session.execute(
            text(
                """
                UPDATE alarms a
                LEFT JOIN cameras c ON a.camera_id = c.id
                SET a.camera_name = c.name
                WHERE (a.camera_name IS NULL OR a.camera_name = '')
                """
            )
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning(f"[data_fix] 回填 alarms.camera_name 失败(可忽略): {e}")

    # 2) algorithm_name
    try:
        await session.execute(
            text(
                """
                UPDATE alarms a
                LEFT JOIN algorithms ag ON a.algorithm_id = ag.id
                SET a.algorithm_name = ag.name
                WHERE (a.algorithm_name IS NULL OR a.algorithm_name = '')
                """
            )
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning(f"[data_fix] 回填 alarms.algorithm_name 失败(可忽略): {e}")

    # 3) area_id（冗余存储）
    try:
        await session.execute(
            text(
                """
                UPDATE alarms a
                LEFT JOIN cameras c ON a.camera_id = c.id
                SET a.area_id = c.area_id
                WHERE (a.area_id IS NULL OR a.area_id = '')
                """
            )
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning(f"[data_fix] 回填 alarms.area_id 失败(可忽略): {e}")

    # 4) area_name（层级路径）
    try:
        await session.execute(
            text(
                """
                UPDATE alarms a
                LEFT JOIN cameras c ON a.camera_id = c.id
                LEFT JOIN areas ar ON c.area_id = ar.id
                SET a.area_name = COALESCE(ar.hierarchy_path, ar.name)
                WHERE (a.area_name IS NULL OR a.area_name = '' OR a.area_name NOT LIKE '%/%')
                """
            )
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning(f"[data_fix] 回填 alarms.area_name 失败(可忽略): {e}")


async def run_startup_data_fix(session: AsyncSession) -> None:
    """
    启动期数据修复入口（幂等）。
    """
    try:
        updated = await fix_area_hierarchy(session)
        if updated:
            logger.info(f"[data_fix] areas 层级字段已回填/更新: {updated} 条")
    except Exception as e:
        logger.warning(f"[data_fix] 回填 areas 层级字段失败(可忽略): {e}")

    try:
        await fix_alarm_denormalized_fields(session)
        logger.info("[data_fix] alarms 冗余字段回填完成")
    except Exception as e:
        logger.warning(f"[data_fix] 回填 alarms 冗余字段失败(可忽略): {e}")

    # 推送策略 actions 结构升级/兼容（dict -> list[dict]）与描述回填
    try:
        updated = await fix_notification_policies(session)
        if updated:
            logger.info(f"[data_fix] notification_policies 已升级 actions 并回填描述: {updated} 条")
    except Exception as e:
        logger.warning(f"[data_fix] 升级 notification_policies 失败(可忽略): {e}")


async def fix_notification_policies(session: AsyncSession) -> int:
    """
    将 notification_policies.actions 升级为 list[dict]（支持多 action），并回填 match_desc/actions_desc。
    兼容历史数据：若 actions 为 dict，包装为 [dict]；若为 list[dict]，保持不变。
    注意：只做幂等升级，不影响业务逻辑。
    """
    try:
        from app.models import (
            NotificationPolicy,
            NotificationEndpoint,
            NotificationTemplate,
            Camera,
            Algorithm,
        )
    except Exception:
        return 0

    result = await session.execute(select(NotificationPolicy))
    policies = result.scalars().all()
    if not policies:
        return 0

    async def name_by_id(model, _id: Optional[str]) -> Optional[str]:
        if not _id:
            return None
        r = await session.execute(select(model).where(model.id == _id))
        row = r.scalar_one_or_none()
        return getattr(row, "name", None) if row else None

    category_cn = {"ai": "业务告警", "system": "系统告警"}
    level_cn = {"info": "提示", "warning": "一般", "danger": "严重", "critical": "致命"}
    provider_cn = {"dingtalk_bot": "钉钉", "wecom_bot": "企微"}

    def as_list(v: Any) -> list:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [v]

    def format_area_items(paths: Any) -> list[str]:
        items: list[str] = []
        for raw in as_list(paths):
            p = str(raw or "").strip()
            if not p:
                continue
            is_wild = "*" in p or "?" in p
            clean = p.rstrip("*").rstrip("/").strip()
            segs = [s for s in clean.split("/") if s]
            if not segs:
                continue
            name = "".join(segs[-2:]) if len(segs) >= 2 else segs[-1]
            suffix = "（含子区域）" if is_wild else "（仅本区域）"
            items.append(f"{name}{suffix}")
        return items

    def format_tw(tw: Any) -> Optional[str]:
        if not isinstance(tw, dict):
            return None
        s = str(tw.get("start") or "").strip()
        e = str(tw.get("end") or "").strip()
        if not s or not e:
            return None
        return f"{s}-{e}"

    updated = 0
    for p in policies:
        # upgrade actions to list[dict]
        acts = p.actions
        if isinstance(acts, dict):
            p.actions = [acts]
            updated += 1
        elif isinstance(acts, list):
            # ok
            pass
        else:
            p.actions = []
            updated += 1

        m = p.match or {}
        parts: list[str] = []
        cat = str(m.get("category") or "").strip()
        if cat:
            parts.append(category_cn.get(cat, cat))

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
                parts.append("、".join(level_cn.get(x, x) for x in ls))
        elif levels:
            lvl = str(levels).strip()
            if lvl:
                parts.append(level_cn.get(lvl, lvl))

        area_items = format_area_items(m.get("area_path"))
        if area_items:
            parts.append("、".join(area_items))

        cam_ids = m.get("camera_id")
        if isinstance(cam_ids, list):
            names: list[str] = []
            for cid in cam_ids:
                cid_s = str(cid).strip()
                if not cid_s:
                    continue
                cam_name = await name_by_id(Camera, cid_s)
                names.append(cam_name or cid_s)
            if names:
                parts.append("摄像头：" + "、".join(names))
        elif cam_ids:
            cam_id = str(cam_ids).strip()
            if cam_id:
                cam_name = await name_by_id(Camera, cam_id)
                parts.append("摄像头：" + str(cam_name or cam_id))

        algo_ids = m.get("algorithm_id")
        if isinstance(algo_ids, list):
            names: list[str] = []
            for aid in algo_ids:
                aid_s = str(aid).strip()
                if not aid_s:
                    continue
                algo_name = await name_by_id(Algorithm, aid_s)
                names.append(algo_name or aid_s)
            if names:
                parts.append("算法：" + "、".join(names))
        elif algo_ids:
            algo_id = str(algo_ids).strip()
            if algo_id:
                algo_name = await name_by_id(Algorithm, algo_id)
                parts.append("算法：" + str(algo_name or algo_id))

        tw = format_tw(m.get("time_window"))
        parts.append(f"（{tw}）" if tw else "（全天生效）")

        ex = m.get("exclude") if isinstance(m.get("exclude"), dict) else {}
        if ex:
            ex_parts: list[str] = []
            ex_areas = format_area_items(ex.get("area_path"))
            if ex_areas:
                ex_parts.append("区域=" + "、".join(ex_areas))
            for k, label in (("camera_id", "摄像头"), ("algorithm_id", "算法"), ("alarm_type", "类型"), ("level", "等级")):
                vals = [str(x).strip() for x in as_list(ex.get(k)) if str(x).strip()]
                if vals:
                    if k == "level":
                        vals = [level_cn.get(x, x) for x in vals]
                    ex_parts.append(label + "=" + "、".join(vals))
            if ex_parts:
                parts.append("排除：" + "；".join(ex_parts))

        p.match_desc = "-".join([x for x in parts if x]) if parts else "（无匹配条件）"

        act_descs: list[str] = []
        for a in (p.actions or []):
            if not isinstance(a, dict):
                continue
            endpoint_ids = a.get("endpoint_ids") or []
            if not isinstance(endpoint_ids, list):
                endpoint_ids = []
            names: list[str] = []
            providers: list[str] = []
            for eid in endpoint_ids:
                en_row = await session.execute(select(NotificationEndpoint).where(NotificationEndpoint.id == str(eid)))
                en = en_row.scalar_one_or_none()
                if en:
                    names.append(getattr(en, "name", None) or str(eid))
                    providers.append(getattr(en, "provider", None) or "")
                else:
                    names.append(str(eid))
            tid = a.get("template_id")
            tn = await name_by_id(NotificationTemplate, str(tid)) if tid else None
            throttle = int(a.get("throttle_sec") or a.get("throttle") or 0)
            retry_times = int(a.get("retry_times") or 0)
            retry_interval = int(a.get("retry_interval_sec") or 0)

            provider_label = None
            ps = [p for p in providers if p]
            if ps and len(set(ps)) == 1:
                provider_label = provider_cn.get(ps[0], ps[0])

            head = "推"
            if provider_label:
                head += provider_label + "-"
            head += "、".join(names) if names else "-"

            details: list[str] = []
            if tid:
                details.append(str(tn or tid))
            details.append(f"{throttle}秒节流" if throttle > 0 else "不限流")
            if retry_times > 0:
                details.append(f"重试{retry_times}次/{retry_interval}s" if retry_interval > 0 else f"重试{retry_times}次")
            s = head + f"（{'，'.join(details)}）"
            act_descs.append(s)
        p.actions_desc = "；".join(act_descs) if act_descs else "（无动作）"

    await session.commit()
    return updated

