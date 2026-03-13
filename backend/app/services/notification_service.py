# -*- coding: utf-8 -*-
"""
通知推送服务（异步消费侧调用）

职责：
- 从 DB 加载 endpoint/template/policy
- policy 匹配 + time_window 判断
- dedup/throttle（MVP：先写 DeliveryLog=skipped，不实现 redis 去重）
- 调用 provider 发送
- 写入 DeliveryLog（系统告警只写 DeliveryLog，不入 alarms）
"""

from __future__ import annotations

from datetime import datetime
import time
import json
from fnmatch import fnmatchcase
from typing import Any, Dict, List, Optional

from common.logging import logger
from app.core.database import get_sync_db_session
from app.core.redis import get_redis
from common.redis.channels import RedisKeys
from app.models import (
    NotificationEndpoint,
    NotificationTemplate,
    NotificationPolicy,
    NotificationDeliveryLog,
)
from app.models.base import generate_uuid
from app.services.notification_crypto import decrypt_config
from app.services.notification_providers import RenderedMessage, get_provider

from config.settings import settings


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def _json_loads_safe(raw: Any) -> Optional[Any]:
    try:
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", errors="ignore")
        return json.loads(raw)
    except Exception:
        return None


def _hgetall_json_dict(redis_client: Any, key: str) -> List[Dict[str, Any]]:
    """
    从 Redis Hash 中读取所有 field/value，将 value 解析为 dict 列表。
    解析失败或非 dict 的条目会被跳过。
    """
    raw = redis_client.hgetall(key) or {}
    out: List[Dict[str, Any]] = []
    for _field, val in raw.items():
        obj = _json_loads_safe(val)
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _hset_many_json(redis_client: Any, key: str, items: List[Dict[str, Any]]) -> None:
    """
    将 items 写入 Redis Hash：field=id, value=json。
    """
    pipe = redis_client.pipeline()
    for it in items or []:
        _id = _to_str((it or {}).get("id")).strip()
        if not _id:
            continue
        pipe.hset(key, _id, json.dumps(it, ensure_ascii=False))
    pipe.execute()


def _now_in_time_window(now: datetime, tw: Optional[Dict[str, Any]]) -> bool:
    if not tw:
        return True
    try:
        start = str(tw.get("start") or "").strip()
        end = str(tw.get("end") or "").strip()
        if not start or not end:
            return True
        sh, sm = [int(x) for x in start.split(":")]
        eh, em = [int(x) for x in end.split(":")]
        s = sh * 60 + sm
        e = eh * 60 + em
        cur = now.hour * 60 + now.minute
        if s <= e:
            return s <= cur <= e
        # 跨天
        return cur >= s or cur <= e
    except Exception:
        return True


def _as_list(v: Any) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _match_any_value(event_val: Any, match_val: Any) -> bool:
    """
    支持：match_val 为单值或 list；event_val 为单值。
    当 match_val 为空/None 表示不限制。
    """
    if match_val is None or match_val == "" or match_val == []:
        return True
    opts = [str(x) for x in _as_list(match_val) if str(x) != ""]
    if not opts:
        return True
    return str(event_val) in opts


def _match_any_pattern(event_val: Any, patterns: Any) -> bool:
    """
    支持通配符：* ?，用于 area_path 等字段。如果pattern是空
    patterns 可为 str 或 list[str]。
    """
    ps = [str(x) for x in _as_list(patterns) if str(x).strip()]
    if not ps:
        return True
    s = str(event_val or "")
    for p in ps:
        if fnmatchcase(s, p):
            return True
    return False


def _build_dedup_value(expr: str, event: Dict[str, Any]) -> str:
    # expr 形如 "category+alarm_type+camera_id+level"
    keys = [k.strip() for k in str(expr or "").split("+") if k.strip()]
    if not keys:
        keys = ["category", "alarm_type", "camera_id", "level"]
    vals = [str(event.get(k) or "") for k in keys]
    return "|".join(vals)


def enqueue_notification_event(event: Dict[str, Any]) -> None:
    """
    统一写入通知事件到 Redis Stream（同步，供各处调用）。
    """
    try:
        redis_wrapper = get_redis()
        payload = json.dumps(event, ensure_ascii=False)
        # stream entry: {"data": "<json>"}
        redis_wrapper.sync_client.xadd(
            RedisKeys.NOTIFICATION_EVENTS_STREAM,
            {"data": payload},
        )
    except Exception as e:
        logger.error(f"写入通知事件流失败: {e}")



def _match_policy(event: Dict[str, Any], policy_match: Dict[str, Any]) -> bool:
    if not policy_match:
        return False

    m = policy_match or {}

    def _cfg_values(cfg_list: Any) -> List[str]:
        vals: List[str] = []
        for x in _as_list(cfg_list):
            if not isinstance(x, dict):
                continue
            v = _to_str(x.get("value")).strip()
            if v:
                vals.append(v)
        return vals

    def _area_patterns(cfg_list: Any) -> List[str]:
        ps: List[str] = []
        for x in _as_list(cfg_list):
            if not isinstance(x, dict):
                continue
            p = _to_str(x.get("idPath") or x.get("label")).strip()
            if p:
                ps.append(p)
        return ps

    # 1) category（单值，必需一致）
    cat = _to_str(m.get("category")).strip()
    if cat and cat != _to_str(event.get("category")).strip():
        return False
    # 2) exclude（先判定，命中任一排除条件则直接不匹配）
    ex = m.get("exclude") if isinstance(m.get("exclude"), dict) else {}
    if ex:
        # 2.1 区域排除：只有配置了 area_config 才参与排除判断
        ex_area_patterns = _area_patterns(ex.get("area_config"))
        if ex_area_patterns:
            if _match_any_pattern(event.get("area_path"), ex_area_patterns):
                logger.info(
                    f"ex 匹配 area_path 命中排除: event_area={event.get('area_path')}, ex_area_patterns={ex_area_patterns}"
                )
                return False
        logger.info(
            f"ex 匹配 area_path 完成: event_area={event.get('area_path')}, ex_area_cfg={ex.get('area_config')}"
        )

        # 2.2 设备排除：只有配置了 camera_config 才参与排除判断
        ex_cam_vals = _cfg_values(ex.get("camera_config"))
        if ex_cam_vals and _match_any_value(event.get("camera_id"), ex_cam_vals):
            logger.info(
                f"ex 匹配 camera_id 命中排除: event_camera={event.get('camera_id')}, ex_cam_vals={ex_cam_vals}"
            )
            return False
        logger.info(
            f"ex 匹配 camera_id 完成: event_camera={event.get('camera_id')}, ex_camera_cfg={ex.get('camera_config')}"
        )

        # 2.3 等级排除：只有配置了 level 才参与排除判断
        ex_levels = ex.get("level")
        if ex_levels and _match_any_value(event.get("level"), ex_levels):
            logger.info(
                f"ex 匹配 level 命中排除: event_level={event.get('level')}, ex_levels={ex_levels}"
            )
            return False
        logger.info(
            f"ex 匹配 level 完成: event_level={event.get('level')}, ex_levels={ex.get('level')}"
        )

        # alarm exclude（ai 用 algorithm_id；system 用 alarm_type）
        ex_alarm_vals = _cfg_values(ex.get("alarm_config"))
        if ex_alarm_vals:
            if (cat or _to_str(event.get("category"))).strip() == "ai":
                if _match_any_value(event.get("algorithm_id"), ex_alarm_vals):
                    return False
            else:
                if _match_any_value(event.get("alarm_type"), ex_alarm_vals):
                    return False
        logger.info(
            f"ex 匹配 alarm_config 完成: event_alarm_type={event.get('alarm_type')}, "
            f"event_algo={event.get('algorithm_id')}, ex_alarm_cfg={ex.get('alarm_config')}"
        )
    # 3) alarm_config（支持多选；ai 用 algorithm_id；system 用 alarm_type）
    alarm_vals = _cfg_values(m.get("alarm_config"))
    if alarm_vals:
        if (cat or _to_str(event.get("category"))).strip() == "ai":
            if not _match_any_value(event.get("algorithm_id"), alarm_vals):
                return False
        else:
            if not _match_any_value(event.get("alarm_type"), alarm_vals):
                return False
    logger.info(f"alarm_config匹配完成")
    # 4) level（支持多选）
    if not _match_any_value(event.get("level"), m.get("level")):
        return False
    logger.info(f"匹配level: {event.get('level')},level_config: {m.get('level')}, m: {m}")
    # 5) camera_config（支持多选）
    cam_vals = _cfg_values(m.get("camera_config"))
    if cam_vals:
        if not _match_any_value(event.get("camera_id"), cam_vals):
            return False
    logger.info(f"匹配camera_id: {event.get('camera_id')},camera_config: {m.get('camera_config')}, m: {m}")
    # 6) area_config（通配符匹配）
    if not _match_any_pattern(event.get("area_path"), _area_patterns(m.get("area_config"))):
        return False
    logger.info(f"匹配area_path: {event.get('area_path')},area_config: {m.get('area_config')}, m: {m}")
    # 7) time_window
    if not _now_in_time_window(datetime.now(), m.get("time_window")):
        return False
    logger.info(f"匹配time_window: {datetime.now()},time_window: {m.get('time_window')}, m: {m}")
    return True


def _render_text_with_vars(tpl: str, event: Dict[str, Any]) -> str:
    s = _to_str(tpl)
    for k, v in (event or {}).items():
        s = s.replace("{{" + _to_str(k) + "}}", "" if v is None else _to_str(v))
    return s


def _render_message_from_template(
    template_obj: Optional[Dict[str, Any]], event: Dict[str, Any]
) -> RenderedMessage:
    """
    输入 template dict（来自 Redis/DB 快照），渲染为抽象消息。
    template_obj 为空时回退 event.title/text。
    """
    content = (template_obj or {}).get("content") or {}
    title_tpl = _to_str(content.get("title") or event.get("title") or "告警通知")
    text_tpl = _to_str(content.get("text") or event.get("text") or "")
    image_tpl = content.get("image_url") or event.get("image_url")
    link_tpl = content.get("link_url") or event.get("link_url")

    return RenderedMessage(
        title=_render_text_with_vars(title_tpl, event),
        text=_render_text_with_vars(text_tpl, event),
        image_url=_render_text_with_vars(_to_str(image_tpl), event)
        if isinstance(image_tpl, str)
        else image_tpl,
        link_url=_render_text_with_vars(_to_str(link_tpl), event)
        if isinstance(link_tpl, str)
        else link_tpl,
    )


def _load_policies_by_category(
    *, session: Any, redis_client: Any, category: str
) -> List[Dict[str, Any]]:
    """
    获取策略列表：
    - 优先从 Redis Hash 读取（按类别拆分）
    - Redis 不存在/为空时，从 DB 读取后回写 Redis
    返回：已启用策略的 dict 列表，按 priority 升序。
    """
    cat = (category or "ai").lower().strip() or "ai"
    if cat == "system":
        key = RedisKeys.NOTIFICATION_POLICIES_SYSTEM_SNAPSHOT
    else:
        key = RedisKeys.NOTIFICATION_POLICIES_AI_SNAPSHOT

    try:
        cached = _hgetall_json_dict(redis_client, key)
        cached = [p for p in cached if isinstance(p, dict) and p.get("is_enabled", True)]
        if cached:
            cached.sort(key=lambda p: int(p.get("priority") or 100))
            return cached
    except Exception as e:
        logger.warning(f"从 Redis 读取策略失败，将回退 DB: {e}")

    db_rows: List[NotificationPolicy] = (
        session.query(NotificationPolicy)
        .filter(NotificationPolicy.is_enabled == True)  # noqa: E712
        .order_by(NotificationPolicy.priority.asc())
        .all()
    )
    result: List[Dict[str, Any]] = []
    for p in db_rows:
        m = p.match or {}
        if (m.get("category") or "ai").lower() != cat:
            continue
        result.append(
            {
                "id": p.id,
                "name": p.name,
                "priority": p.priority,
                "is_enabled": p.is_enabled,
                "match": p.match or {},
                "actions": p.actions or [],
                "match_desc": p.match_desc,
                "actions_desc": p.actions_desc,
            }
        )

    try:
        _hset_many_json(redis_client, key, result)
    except Exception as e:
        logger.warning(f"回写策略到 Redis 失败(可忽略): {e}")
    return result

def _load_template_by_id(
    *, session: Any, redis_client: Any, template_id: str
) -> Optional[Dict[str, Any]]:
    """
    按需读取单个模板：
    - 先 Redis HGET(notification:templates:snapshot, id)
    - 缓存 miss 再 DB 读一条并 HSET 回写
    """
    tid = _to_str(template_id).strip()
    if not tid:
        return None
    key = RedisKeys.NOTIFICATION_TEMPLATES_SNAPSHOT
    try:
        raw = redis_client.hget(key, tid)
        obj = _json_loads_safe(raw)
        if isinstance(obj, dict):
            return obj
    except Exception as e:
        logger.warning(f"从 Redis 读取模板失败，将回退 DB: {tid}, {e}")

    row: Optional[NotificationTemplate] = (
        session.query(NotificationTemplate).filter(NotificationTemplate.id == tid).first()
    )
    if not row:
        return None
    obj = {
        "id": row.id,
        "name": row.name,
        "type": row.type,
        "is_enabled": row.is_enabled,
        "content": row.content or {},
    }
    try:
        redis_client.hset(key, tid, json.dumps(obj, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"回写模板到 Redis 失败(可忽略): {tid}, {e}")
    return obj


def _load_endpoint_by_id(
    *, session: Any, redis_client: Any, endpoint_id: str
) -> Optional[Dict[str, Any]]:
    """
    按需读取单个 endpoint：
    - 先 Redis HGET(notification:endpoints:snapshot, id)
    - 缓存 miss 再 DB 读一条并 HSET 回写
    """
    eid = _to_str(endpoint_id).strip()
    if not eid:
        return None
    key = RedisKeys.NOTIFICATION_ENDPOINTS_SNAPSHOT
    try:
        raw = redis_client.hget(key, eid)
        obj = _json_loads_safe(raw)
        if isinstance(obj, dict):
            return obj
    except Exception as e:
        logger.warning(f"从 Redis 读取 endpoint 失败，将回退 DB: {eid}, {e}")

    row: Optional[NotificationEndpoint] = (
        session.query(NotificationEndpoint).filter(NotificationEndpoint.id == eid).first()
    )
    if not row:
        return None
    obj = {
        "id": row.id,
        "name": row.name,
        "provider": row.provider,
        "is_enabled": row.is_enabled,
        "encrypted_config": row.encrypted_config,
    }
    try:
        redis_client.hset(key, eid, json.dumps(obj, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"回写 endpoint 到 Redis 失败(可忽略): {eid}, {e}")
    return obj


def dispatch_event(event: Dict[str, Any]) -> None:
    """
    入口：被 NotificationWorker 调用（同步）
    """
    logger.info(f"dispatch_event start: {event}")
    with get_sync_db_session() as session:
        redis_client = get_redis().sync_client
        # 1) 获取 policies（先 Redis，后 DB，DB 兜底后回写 Redis）
        category = _to_str(event.get("category") or "ai")
        policies = _load_policies_by_category(
            session=session, redis_client=redis_client, category=category
        )
        logger.info(f"policies: {policies}")
        # 2) 循环 policies，匹配后收集 matched_actions
        matched_actions: List[Dict[str, Any]] = []
        for p in policies:
            policy_match = p.get("match") or {}
            is_match = _match_policy(event, policy_match)
            logger.info(f"is_match: {is_match}")
            if is_match:
                raw_actions = p.get("actions") or []
                if not isinstance(raw_actions, list):
                    continue
                for a in raw_actions:
                    if not isinstance(a, dict):
                        continue
                    act = dict(a)
                    act["_policy_id"] = p.get("id")
                    matched_actions.append(act)

        if not matched_actions:
            return
        logger.info(f"matched_actions: {matched_actions}")
        # 3) matched_actions 排序
        matched_actions.sort(key=lambda a: int(a.get("push_order") or 100))
        # 5) 循环 matched_actions：限流 → 渲染 → 推送 → 记录 DeliveryLog
        for act in matched_actions:
            endpoint_ids = act.get("endpoint_ids") or []
            if not isinstance(endpoint_ids, list):
                endpoint_ids = []

            # 5.1 限流（dedup_key + throttle_sec）
            throttle_sec = int(act.get("throttle_sec") or 0)
            dedup_expr = _to_str(act.get("dedup_key")).strip()
            if throttle_sec > 0 and dedup_expr:
                dedup_val = _build_dedup_value(dedup_expr, event)
                k = f"notif:throttle:{act.get('_policy_id')}:{dedup_val}"
                # key 存在=仍在节流窗口内，直接跳过（不做动作）
                if not redis_client.set(k, "1", nx=True, ex=throttle_sec):
                    continue

            # 5.2 获取模板（按需：先 Redis HGET，miss 再 DB 并回写）
            template_id = _to_str(act.get("template_id")).strip()
            template_obj = (
                _load_template_by_id(
                    session=session, redis_client=redis_client, template_id=template_id
                )
                if template_id
                else None
            )
            if template_obj and not template_obj.get("is_enabled", True):
                template_obj = None

            # 5.3 渲染消息（封装变量替换）
            msg = _render_message_from_template(template_obj, event)

            for eid in endpoint_ids:
                # 5.4 渠道按需获取（按 endpoint_id 单条读取）
                endpoint_obj = _load_endpoint_by_id(
                    session=session, redis_client=redis_client, endpoint_id=_to_str(eid)
                )
                if not endpoint_obj or not endpoint_obj.get("is_enabled", True):
                    continue

                delivery = NotificationDeliveryLog(
                    id=generate_uuid(),
                    alarm_id=event.get("alarm_id"),
                    category=str(event.get("category") or "ai"),
                    alarm_type=str(event.get("alarm_type") or ""),
                    level=str(event.get("level") or "info"),
                    endpoint_id=_to_str(endpoint_obj.get("id")),
                    provider=_to_str(endpoint_obj.get("provider")),
                    template_id=template_id or None,
                    status="failed",
                    error=None,
                    request_meta={"attempts": 1},
                    response_meta=None,
                )

                try:
                    cfg = decrypt_config(_to_str(endpoint_obj.get("encrypted_config")))
                    provider = get_provider(_to_str(endpoint_obj.get("provider")))
                    logger.info(f"provider: {provider}")
                    provider.send_sync(cfg, msg)
                    delivery.status = "success"
                    delivery.error = None
                    delivery.response_meta = {"attempt": 1}
                except NotImplementedError as e:
                    delivery.status = "failed"
                    delivery.error = str(e)
                    delivery.response_meta = {"attempt": 1}
                except Exception as e:
                    delivery.status = "failed"
                    delivery.error = str(e)[:1000]
                    delivery.response_meta = {"attempt": 1}

                session.add(delivery)

        session.commit()

