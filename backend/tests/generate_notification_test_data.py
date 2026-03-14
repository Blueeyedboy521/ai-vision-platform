# -*- coding: utf-8 -*-
"""
从数据库读取区域、摄像头、算法，生成通知测试用 alarm_data.json 与 policy_data.json。

约束：
- 所有数据来自数据库，不伪造。
- 摄像头与区域一一对应：摄像头 A 属于区域 A，则告警事件里该摄像头的 area_id_path/area_name_path
  必须来自该摄像头在 DB 中的所属区域，不得用其他区域替代。
- 策略中的 area_config/camera_config/alarm_config 仅使用 DB 中存在的区域/摄像头/算法 id 与路径。

用法（在 backend 目录下）:
  python -m tests.generate_notification_test_data
  或
  PYTHONPATH=. python tests/generate_notification_test_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.core.database import get_sync_db_session
from app.models import Area, Camera, Algorithm, NotificationEndpoint, NotificationTemplate

TESTS_DIR = Path(__file__).resolve().parent
ALARM_JSON = TESTS_DIR / "alarm_data.json"
POLICY_JSON = TESTS_DIR / "policy_data.json"
TARGET_COUNT = 15

LEVELS = ["info", "warning", "danger", "critical"]
SYSTEM_ALARM_TYPES = ["offline", "stream_failed", "heartbeat_timeout"]


def load_areas(session) -> list[dict]:
    """区域列表：id, name, id_path, hierarchy_path, parent_id（均来自 DB）。"""
    rows = session.query(Area).order_by(Area.sort_order, Area.created_at).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "id_path": (getattr(a, "id_path", None) or "").strip(),
            "hierarchy_path": (getattr(a, "hierarchy_path", None) or a.name or "").strip(),
            "parent_id": getattr(a, "parent_id", None),
        }
        for a in rows
    ]


def load_cameras_with_area(session) -> list[dict]:
    """
    摄像头列表：每条摄像头的区域路径来自该摄像头在 DB 中的 area_id 对应区域，保证对应关系真实。
    """
    cameras = []
    for c in session.query(Camera).order_by(Camera.created_at).all():
        area_id = getattr(c, "area_id", None)
        area_id_path = None
        area_name_path = None
        if area_id:
            area = session.query(Area).filter(Area.id == area_id).first()
            if area:
                area_id_path = (getattr(area, "id_path", None) or "").strip() or None
                area_name_path = (getattr(area, "hierarchy_path", None) or area.name or "").strip() or None
        cameras.append({
            "id": c.id,
            "name": c.name,
            "area_id": area_id,
            "area_id_path": area_id_path,
            "area_name_path": area_name_path,
        })
    return cameras


def load_algorithms(session) -> list[dict]:
    """算法列表：id, name, code（来自 DB）。"""
    rows = session.query(Algorithm).order_by(Algorithm.created_at).all()
    return [
        {"id": a.id, "name": a.name, "code": (getattr(a, "code", None) or a.id)}
        for a in rows
    ]


def load_endpoints(session) -> list[str]:
    """通知渠道 id 列表（来自 DB）。"""
    rows = session.query(NotificationEndpoint).filter(NotificationEndpoint.is_enabled == True).order_by(NotificationEndpoint.created_at).all()
    return [r.id for r in rows]


def load_templates(session) -> list[str]:
    """通知模板 id 列表（来自 DB）。"""
    rows = session.query(NotificationTemplate).filter(NotificationTemplate.is_enabled == True).order_by(NotificationTemplate.created_at).all()
    return [r.id for r in rows]


def build_alarm_events(areas: list, cameras: list, algorithms: list) -> list:
    """
    组装 15 条告警事件。
    - 每条事件绑定一个真实摄像头；该事件的 area_id_path/area_name_path 仅使用该摄像头的所属区域（DB 关系），不混用其他区域。
    - 算法从 algorithms 中轮转选取，保证是 DB 中的算法。
    """
    if not cameras:
        raise ValueError("数据库无摄像头，无法生成告警数据")
    if not algorithms:
        raise ValueError("数据库无算法，无法生成告警数据")

    events = []
    for i in range(TARGET_COUNT):
        cam = cameras[i % len(cameras)]
        algo = algorithms[i % len(algorithms)]
        level = LEVELS[i % len(LEVELS)]
        is_system = i >= 10
        category = "system" if is_system else "ai"

        if is_system:
            alarm_type = SYSTEM_ALARM_TYPES[i % len(SYSTEM_ALARM_TYPES)]
            # 最后一条可做成“无摄像头”的系统告警，其余用真实摄像头
            if i == TARGET_COUNT - 1:
                event = {
                    "category": category,
                    "alarm_id": f"alarm-{i+1:03d}",
                    "alarm_type": alarm_type,
                    "level": level,
                    "camera_id": None,
                    "camera_name": None,
                    "area_id_path": None,
                    "area_name_path": None,
                    "area_name": None,
                    "algorithm_id": None,
                    "algorithm_name": None,
                    "title": "系统告警",
                    "text": alarm_type,
                }
            else:
                event = {
                    "category": category,
                    "alarm_id": f"alarm-{i+1:03d}",
                    "alarm_type": alarm_type,
                    "level": level,
                    "camera_id": cam["id"],
                    "camera_name": cam["name"],
                    "area_id_path": cam.get("area_id_path"),
                    "area_name_path": cam.get("area_name_path"),
                    "area_name": cam.get("area_name_path"),
                    "algorithm_id": None,
                    "algorithm_name": None,
                    "title": "系统告警",
                    "text": alarm_type,
                }
        else:
            event = {
                "category": category,
                "alarm_id": f"alarm-{i+1:03d}",
                "alarm_type": algo["id"],
                "level": level,
                "camera_id": cam["id"],
                "camera_name": cam["name"],
                "area_id_path": cam.get("area_id_path"),
                "area_name_path": cam.get("area_name_path"),
                "area_name": cam.get("area_name_path"),
                "algorithm_id": algo["id"],
                "algorithm_name": algo["name"],
                "title": (algo["name"] or "告警") + "告警",
                "text": "检测告警",
            }
        events.append(event)
    return events


def build_policies(
    areas: list,
    cameras: list,
    algorithms: list,
    endpoint_ids: list[str],
    template_id: str | None,
) -> list:
    """
    组装 15 条策略。仅使用 DB 中的区域/摄像头/算法；area_id_path 仅用精确路径，不含通配符；根节点不参与。
    endpoint_ids、template_id 来自 DB 的渠道与模板。
    """
    if not cameras:
        raise ValueError("数据库无摄像头，无法生成策略数据")
    if not algorithms:
        raise ValueError("数据库无算法，无法生成策略数据")

    # 仅非根区域（root 不允许选择）
    areas_non_root = [a for a in areas if a.get("parent_id") is not None]
    if not areas_non_root:
        raise ValueError("数据库无非根区域，无法生成策略的 area_config（根节点不允许选择）")

    a0, a1 = areas_non_root[0], areas_non_root[1 % len(areas_non_root)]
    c0 = cameras[0]
    algo0 = algorithms[0]

    id_path0 = a0.get("id_path") or ""
    id_path1 = a1.get("id_path") or ""

    act = {"endpoint_ids": endpoint_ids[:] if endpoint_ids else [], "template_id": template_id, "push_order": 1}

    def tw_all_day():
        return {"start": "00:00", "end": "23:59"}

    policies = [
        {
            "name": "策略1-仅AI且危险级",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": ["danger", "critical"],
                "alarm_config": [],
                "area_config": [],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略2-某区域精确",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [],
                "area_config": [{"value": a0["id"], "label": a0["name"], "area_id_path": id_path0}],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略3-精确区域路径",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [],
                "area_config": [{"value": a0["id"], "label": a0["name"], "area_id_path": id_path0}],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略4-排除某区域",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [],
                "area_config": [],
                "camera_config": [],
                "exclude": {"area_config": [{"value": a0["id"], "label": a0["name"], "area_id_path": id_path0}]},
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略5-仅某摄像头",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [],
                "area_config": [],
                "camera_config": [{"value": c0["id"], "label": c0["name"]}],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略6-仅某算法",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [{"value": algo0["id"], "label": algo0["name"]}],
                "area_config": [],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略7-仅系统告警",
            "priority": 100,
            "match": {
                "category": "system",
                "level": [],
                "alarm_config": [],
                "area_config": [],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略8-工作时间9-18点",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [],
                "area_config": [],
                "camera_config": [],
                "time_window": {"start": "09:00", "end": "18:00"},
            },
            "actions": [{**act}],
        },
        {
            "name": "策略9-排除某摄像头",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [],
                "area_config": [],
                "camera_config": [],
                "exclude": {"camera_config": [{"value": c0["id"], "label": c0["name"]}]},
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略10-排除warning等级",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": ["danger", "critical", "info"],
                "alarm_config": [],
                "area_config": [],
                "camera_config": [],
                "exclude": {"level": ["warning"]},
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略11-另一区域精确",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [],
                "area_config": [{"value": a1["id"], "label": a1["name"], "area_id_path": id_path1}],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略12-两区域精确",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [],
                "area_config": [
                    {"value": a0["id"], "label": a0["name"], "area_id_path": id_path0},
                    {"value": a1["id"], "label": a1["name"], "area_id_path": id_path1},
                ],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略13-系统+流异常",
            "priority": 100,
            "match": {
                "category": "system",
                "level": [],
                "alarm_config": [{"value": "stream_failed", "label": "流异常"}],
                "area_config": [],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略14-多条件:区域+等级+算法",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": ["danger", "critical"],
                "alarm_config": [{"value": algo0["id"], "label": algo0["name"]}],
                "area_config": [{"value": a0["id"], "label": a0["name"], "area_id_path": id_path0}],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
        {
            "name": "策略15-无限制(全匹配)",
            "priority": 100,
            "match": {
                "category": "ai",
                "level": [],
                "alarm_config": [],
                "area_config": [],
                "camera_config": [],
                "time_window": tw_all_day(),
            },
            "actions": [{**act}],
        },
    ]
    return policies


def main() -> None:
    with get_sync_db_session() as session:
        areas = load_areas(session)
        cameras = load_cameras_with_area(session)
        algorithms = load_algorithms(session)
        endpoint_ids = load_endpoints(session)
        template_ids = load_templates(session)

    print(f"数据库: 区域 {len(areas)} 个, 摄像头 {len(cameras)} 个, 算法 {len(algorithms)} 个, 渠道 {len(endpoint_ids)} 个, 模板 {len(template_ids)} 个")
    if not cameras:
        print("错误: 至少需要 1 个摄像头")
        sys.exit(1)
    if not algorithms:
        print("错误: 至少需要 1 个算法")
        sys.exit(1)
    template_id = template_ids[0] if template_ids else None
    if not template_ids:
        print("提示: 未查询到启用模板，策略 actions 中 template_id 为空")

    events = build_alarm_events(areas, cameras, algorithms)
    policies = build_policies(areas, cameras, algorithms, endpoint_ids, template_id)

    with open(ALARM_JSON, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    with open(POLICY_JSON, "w", encoding="utf-8") as f:
        json.dump(policies, f, ensure_ascii=False, indent=2)

    print(f"已写入: {ALARM_JSON.name} ({len(events)} 条), {POLICY_JSON.name} ({len(policies)} 条)")
    print("告警事件中摄像头与区域均按 DB 对应关系生成，未混用其他区域。")


if __name__ == "__main__":
    main()
