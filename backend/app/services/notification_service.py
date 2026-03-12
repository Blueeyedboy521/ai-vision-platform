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
from fnmatch import fnmatchcase
from typing import Any, Dict, List, Optional

from common.logging import logger
from app.core.database import get_sync_db_session
from app.models import (
    NotificationEndpoint,
    NotificationTemplate,
    NotificationPolicy,
    NotificationDeliveryLog,
)
from app.models.base import generate_uuid
from app.services.notification_crypto import decrypt_config
from app.services.notification_providers import RenderedMessage, get_provider
import redis

from config.settings import settings


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
    支持通配符：* ?，用于 area_path 等字段。
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


def _match_policy(event: Dict[str, Any], policy_match: Dict[str, Any]) -> bool:
    if not policy_match:
        return False
    m = policy_match or {}

    # exclude（先判定，命中任一排除条件则直接不匹配）
    ex = m.get("exclude") if isinstance(m.get("exclude"), dict) else {}
    if ex:
        if not _match_any_pattern(event.get("area_path"), ex.get("area_path")):
            pass
        else:
            return False
        for k in ("camera_id", "algorithm_id", "alarm_type", "level"):
            exv = ex.get(k)
            if exv is None or exv == "" or exv == []:
                continue
            if _match_any_value(event.get(k), exv):
                return False

    # category（单值）
    cat = m.get("category")
    if cat and str(cat) != str(event.get("category")):
        return False

    # alarm_type / level / camera_id / algorithm_id（支持多选）
    if not _match_any_value(event.get("alarm_type"), m.get("alarm_type")):
        return False
    if not _match_any_value(event.get("level"), m.get("level")):
        return False
    if not _match_any_value(event.get("camera_id"), m.get("camera_id")):
        return False

    # algorithm_id 仅在 ai 类别有意义
    if str(event.get("category") or "") == "ai":
        if not _match_any_value(event.get("algorithm_id"), m.get("algorithm_id")):
            return False

    # area_path（通配符匹配）
    if not _match_any_pattern(event.get("area_path"), m.get("area_path")):
        return False

    # time_window
    if not _now_in_time_window(datetime.now(), m.get("time_window")):
        return False

    return True


def _render_template(template: NotificationTemplate, event: Dict[str, Any]) -> RenderedMessage:
    # MVP：简单变量替换，后续可换 jinja2
    content = template.content or {}
    title_tpl = str(content.get("title") or event.get("title") or "告警通知")
    text_tpl = str(content.get("text") or event.get("text") or "")
    image_tpl = content.get("image_url") or event.get("image_url")
    link_tpl = content.get("link_url") or event.get("link_url")

    def repl(s: str) -> str:
        for k, v in (event or {}).items():
            s = s.replace("{{" + str(k) + "}}", "" if v is None else str(v))
        return s

    return RenderedMessage(
        title=repl(title_tpl),
        text=repl(text_tpl),
        image_url=repl(str(image_tpl)) if isinstance(image_tpl, str) else image_tpl,
        link_url=repl(str(link_tpl)) if isinstance(link_tpl, str) else link_tpl,
    )


def dispatch_event(event: Dict[str, Any]) -> None:
    """
    入口：被 NotificationWorker 调用（同步）
    """
    with get_sync_db_session() as session:
        endpoints = session.query(NotificationEndpoint).filter(NotificationEndpoint.is_enabled == True).all()  # noqa: E712
        templates = {
            t.id: t
            for t in session.query(NotificationTemplate).filter(NotificationTemplate.is_enabled == True).all()  # noqa: E712
        }
        policies = (
            session.query(NotificationPolicy)
            .filter(NotificationPolicy.is_enabled == True)  # noqa: E712
            .order_by(NotificationPolicy.priority.asc())
            .all()
        )

        matched_actions: List[Dict[str, Any]] = []
        for p in policies:
            if _match_policy(event, p.match or {}):
                raw_actions = p.actions or {}
                # 兼容两种结构：
                # 1) actions 为 dict：旧形态（单个 action）
                # 2) actions 为 list[dict]：新形态（多个 action）
                if isinstance(raw_actions, list):
                    for a in raw_actions:
                        if isinstance(a, dict):
                            act = dict(a)
                            act["_policy_id"] = p.id
                            matched_actions.append(act)
                elif isinstance(raw_actions, dict):
                    act = dict(raw_actions)
                    act["_policy_id"] = p.id
                    matched_actions.append(act)

        if not matched_actions:
            return

        endpoint_map = {e.id: e for e in endpoints}
        rds = redis.from_url(settings.REDIS_URL, decode_responses=True)

        try:
            # action 执行顺序：push_order（小优先），再按插入顺序
            matched_actions.sort(key=lambda a: int(a.get("push_order") or 100))

            for act in matched_actions:
                endpoint_ids = act.get("endpoint_ids") or []
                if not isinstance(endpoint_ids, list):
                    endpoint_ids = []

                throttle_sec = int(act.get("throttle_sec") or 0)
                dedup_expr = str(act.get("dedup_key") or "").strip()
                if throttle_sec > 0:
                    dedup_val = _build_dedup_value(dedup_expr, event)
                    # action 级节流：同一 dedup_key 在 N 秒内最多推送一次
                    k = f"notif:throttle:{act.get('_policy_id')}:{dedup_val}"
                    if not rds.set(k, "1", nx=True, ex=throttle_sec):
                        # 记录 skipped（每个 endpoint 都记一条，便于审计）
                        for eid in endpoint_ids:
                            endpoint = endpoint_map.get(eid)
                            if not endpoint:
                                continue
                            delivery = NotificationDeliveryLog(
                                id=generate_uuid(),
                                alarm_id=event.get("alarm_id"),
                                category=str(event.get("category") or "ai"),
                                alarm_type=str(event.get("alarm_type") or ""),
                                level=str(event.get("level") or "info"),
                                endpoint_id=endpoint.id,
                                provider=endpoint.provider,
                                template_id=str(act.get("template_id") or "") or None,
                                status="skipped",
                                error=f"throttle({throttle_sec}s)",
                                request_meta={"dedup_key": dedup_expr, "dedup_value": dedup_val},
                                response_meta=None,
                            )
                            session.add(delivery)
                        continue

                template_id = act.get("template_id")
                template = templates.get(template_id) if template_id else None
                if template is None:
                    msg = RenderedMessage(
                        title=str(event.get("title") or "告警通知"),
                        text=str(event.get("text") or ""),
                        image_url=event.get("image_url"),
                        link_url=event.get("link_url"),
                    )
                else:
                    msg = _render_template(template, event)

                retry_times = int(act.get("retry_times") or 0)
                retry_interval = int(act.get("retry_interval_sec") or 1)
                total_attempts = 1 + max(0, retry_times)

                for eid in endpoint_ids:
                    endpoint = endpoint_map.get(eid)
                    if not endpoint or not endpoint.is_enabled:
                        continue

                    delivery = NotificationDeliveryLog(
                        id=generate_uuid(),
                        alarm_id=event.get("alarm_id"),
                        category=str(event.get("category") or "ai"),
                        alarm_type=str(event.get("alarm_type") or ""),
                        level=str(event.get("level") or "info"),
                        endpoint_id=endpoint.id,
                        provider=endpoint.provider,
                        template_id=template.id if template else None,
                        status="failed",
                        error=None,
                        request_meta={"attempts": total_attempts},
                        response_meta=None,
                    )

                    last_err: Optional[str] = None
                    for attempt in range(1, total_attempts + 1):
                        try:
                            cfg = decrypt_config(endpoint.encrypted_config)
                            provider = get_provider(endpoint.provider)
                            provider.send_sync(cfg, msg)
                            delivery.status = "success"
                            delivery.error = None
                            delivery.response_meta = {"attempt": attempt}
                            last_err = None
                            break
                        except NotImplementedError as e:
                            last_err = str(e)
                            break
                        except Exception as e:
                            last_err = str(e)[:1000]
                            if attempt < total_attempts:
                                time.sleep(max(0, retry_interval))

                    if last_err:
                        delivery.status = "failed"
                        delivery.error = last_err
                        delivery.response_meta = {"attempt": total_attempts}

                    session.add(delivery)

            session.commit()
        finally:
            try:
                rds.close()
            except Exception:
                pass

