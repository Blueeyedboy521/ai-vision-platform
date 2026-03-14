# -*- coding: utf-8 -*-
"""
测试通知策略匹配逻辑（尤其是 _match_policy）

依赖已生成的测试数据：请先执行
  python -m tests.generate_notification_test_data
生成 tests/alarm_data.json、tests/policy_data.json 后再运行本脚本。

用法（在 backend 目录下执行）:
  python -m tests.test_notification_policy_match
  或
  PYTHONPATH=. python tests/test_notification_policy_match.py

说明:
  - 仅读取 JSON 并跑 _match_policy，不访问数据库。
  - 策略 8 依赖当前时间（09:00-18:00），运行时间在窗外则该策略对所有事件不匹配。
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# 降低 notification_service 日志噪音，便于查看矩阵
logging.getLogger("app.services.notification_service").setLevel(logging.WARNING)

from app.services.notification_service import _match_policy

TESTS_DIR = Path(__file__).resolve().parent
ALARM_JSON = TESTS_DIR / "alarm_data.json"
POLICY_JSON = TESTS_DIR / "policy_data.json"


def load_json(path: Path) -> list | dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    if not ALARM_JSON.exists():
        print(f"未找到 {ALARM_JSON.name}，请先执行: python -m tests.generate_notification_test_data")
        sys.exit(1)
    if not POLICY_JSON.exists():
        print(f"未找到 {POLICY_JSON.name}，请先执行: python -m tests.generate_notification_test_data")
        sys.exit(1)

    alarms = load_json(ALARM_JSON)
    policies = load_json(POLICY_JSON)
    if not isinstance(alarms, list):
        alarms = [alarms]
    if not isinstance(policies, list):
        policies = [policies]

    events = [dict(e) for e in alarms]
    policy_matches = [p.get("match") or {} for p in policies]
    policy_names = [p.get("name") or f"策略{i+1}" for i, p in enumerate(policies)]
    n_a, n_p = len(events), len(policies)

    print(f"告警事件数: {n_a}, 策略数: {n_p}")
    print("=" * 80)

    result = []
    for i, event in enumerate(events):
        row = []
        for j, match in enumerate(policy_matches):
            ok = _match_policy(event, match)
            row.append(ok)
        result.append(row)

    col_w = 20
    header = "事件\\策略".ljust(14) + "".join(
        (policy_names[j][: col_w - 1].ljust(col_w) for j in range(n_p))
    )
    print(header)
    print("-" * len(header))
    for i in range(n_a):
        event_label = str(events[i].get("alarm_id") or f"event-{i+1}")[:12]
        row_str = event_label.ljust(14) + "".join(
            ("Y" if result[i][j] else ".").ljust(col_w) for j in range(n_p)
        )
        print(row_str)
    print("=" * 80)
    print("图例: Y=匹配, .=不匹配")
    print("(策略8 仅在 09:00-18:00 内匹配)")

    # 关键用例断言
    failed = []
    for i, ev in enumerate(events):
        is_ai = (ev.get("category") or "").strip() == "ai"
        is_system = (ev.get("category") or "").strip() == "system"
        level = (ev.get("level") or "").strip()
        # 策略7(索引6): 仅系统告警
        if is_system and not result[i][6]:
            failed.append(f"event {i+1} (system) 应匹配策略7")
        if is_ai and result[i][6]:
            failed.append(f"event {i+1} (ai) 不应匹配策略7")
        # 策略15(索引14): 仅 AI 全匹配
        if is_ai and not result[i][14]:
            failed.append(f"event {i+1} (ai) 应匹配策略15")
        if is_system and result[i][14]:
            failed.append(f"event {i+1} (system) 不应匹配策略15")
        # 策略1(索引0): AI 且 danger/critical
        if is_ai and level in ("danger", "critical") and not result[i][0]:
            failed.append(f"event {i+1} (ai,{level}) 应匹配策略1")
        if is_ai and level not in ("danger", "critical") and result[i][0]:
            failed.append(f"event {i+1} (ai,{level}) 不应匹配策略1")
    if failed:
        print("\n[FAIL] 断言失败:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    print("\n[OK] 关键用例断言通过")


if __name__ == "__main__":
    main()
