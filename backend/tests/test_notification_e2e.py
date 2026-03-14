# -*- coding: utf-8 -*-
"""
E2E 测试：入队通知事件 → 同步执行 dispatch_event → 检查日志与最终推送内容。

1. 调用 enqueue_notification_event(event) 将事件写入 Redis 通知流；
2. 在同一进程内直接调用 dispatch_event(event)，模拟 worker 消费；
3. 通过日志确认：dispatch_event 是否被调用、策略匹配、以及【最终推送内容】
   （notification_service 会在 send_sync 前打印 title/text 等）；
4. 若配置了企微等渠道且匹配到策略，会真实推送，并在日志中看到【最终推送内容】。

依赖：
- 请先执行 python -m tests.generate_notification_test_data 生成 alarm_data.json；
- 需要 DB、Redis 可用（dispatch_event 会读策略/模板/渠道并可能真实推送）。

用法（在 backend 目录下）:
  python -m tests.test_notification_e2e
  python -m tests.test_notification_e2e 0    # 使用 alarm_data 第 1 条（默认）
  python -m tests.test_notification_e2e 3    # 使用第 4 条
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# 保证能看到 dispatch_event 与【最终推送内容】日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("app.services.notification_service").setLevel(logging.INFO)

from app.core.redis import get_redis
from app.services.notification_service import enqueue_notification_event, dispatch_event

TESTS_DIR = Path(__file__).resolve().parent
ALARM_JSON = TESTS_DIR / "alarm_data.json"


def load_alarms() -> list:
    with open(ALARM_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def main() -> None:
    if not ALARM_JSON.exists():
        print(f"未找到 {ALARM_JSON.name}，请先执行: python -m tests.generate_notification_test_data")
        sys.exit(1)

    # 确保 Redis 同步客户端已连接（dispatch_event 内会用到 sync_client）
    redis = get_redis()
    try:
        redis.connect_sync()
    except Exception as e:
        print(f"[WARN] 连接 Redis 失败（后续操作可能仍会报错）: {e}")

    alarms = load_alarms()
    index = 0
    if len(sys.argv) > 1:
        try:
            index = int(sys.argv[1])
        except ValueError:
            index = 0
    index = max(0, min(index, len(alarms) - 1))
    event = dict(alarms[index])

    print("=" * 60)
    print(f"使用告警事件索引: {index} (共 {len(alarms)} 条)")
    print(f"事件摘要: alarm_id={event.get('alarm_id')} category={event.get('category')} level={event.get('level')} camera_id={event.get('camera_id')}")
    print("=" * 60)

    # 1) 入队
    print("\n[1] 入队: enqueue_notification_event(event)")
    enqueue_notification_event(event)
    print("    已写入 Redis 通知流。")

    # 2) 同步执行 dispatch_event（模拟 worker 消费）
    print("\n[2] 同步执行: dispatch_event(event)（模拟消费）")
    dispatch_event(event)
    print("    dispatch_event 已返回。")

    print("\n" + "=" * 60)
    print("请查看上方日志确认：")
    print("  - dispatch_event start 是否打印（表示已消费/执行）；")
    print("  - policies / matched_actions 是否匹配到策略；")
    print("  - 【最终推送内容】是否打印（title/text 等即为发给企微等渠道的内容）；")
    print("  - 若配置了企微等且匹配到策略，会真实推送，可在企微侧核对。")
    print("=" * 60)


if __name__ == "__main__":
    main()
