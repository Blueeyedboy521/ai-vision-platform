## 通知 E2E 测试记录（alarm_data 全量 0~14）

本文记录了使用 `tests.test_notification_e2e` 逐条压测 `alarm_data.json` 中 15 条告警的结果，便于你逐条对照策略与企微推送。

- **环境命令前缀**（backend 目录下）：
  - `cd backend`
  - 统一命令：`python -m tests.test_notification_e2e <index>`
- **通用结论**：
  - 所有用例都执行到了 `dispatch_event start`，说明事件已被消费。
  - 日志里都打印了 `policies: [...]`，说明策略快照加载正常。
  - 所有用例的 `is_match: False`，且没有出现「最终推送内容」相关日志，说明 **当前这批 alarm 测试数据没有任何一条真正命中现有策略，因此不会向企微等渠道发消息**。

下面逐条列出关键信息（仅节选关键日志片段，方便你对照）。

---

### 索引 0

- **命令**：`python -m tests.test_notification_e2e 0`
- **告警摘要**：`alarm_id=alarm-001 category=ai level=info camera_id=37d229432677484c82b9c65ca1d0d0ba`（人告警，区域：默认区域/产线1）
- **策略日志节选**：

```text
dispatch_event start: {... 'alarm_id': 'alarm-001', 'level': 'info', 'algorithm_name': '人', ...}
policies: [
  {'id': '92b8a95cec3b4f6fbe6edf932be86582', 'name': '人员入侵', ...},
  {'id': '2c532be1850242e1832c7279bdd3bcea', 'name': '111', ...}
]
...
is_match: False
...
is_match: False
```

- **结果**：
  - **是否消费**：是（有 `dispatch_event start`）。
  - **是否匹配策略**：否（两条策略均 `is_match: False`）。
  - **是否推送 / 最终内容**：无（日志中未出现「最终推送内容」相关日志）。

---

### 索引 1

- **命令**：`python -m tests.test_notification_e2e 1`
- **告警摘要**：`alarm_id=alarm-002 category=ai level=warning camera_id=926001bb83db48bcb62cf3ebf0eb1e72`（手提包告警，区域：默认区域/产线1/5F）
- **策略日志节选**：

```text
dispatch_event start: {... 'alarm_id': 'alarm-002', 'level': 'warning', 'algorithm_name': '手提包', ...}
policies: [
  {'id': '92b8a95cec3b4f6fbe6edf932be86582', 'name': '人员入侵', ...},
  {'id': '2c532be1850242e1832c7279bdd3bcea', 'name': '111', ...}
]
...
ex 匹配 camera_id 命中排除: event_camera=926001bb83db48bcb62cf3ebf0eb1e72, ex_cam_vals=['926001bb83db48bcb62cf3ebf0eb1e72']
is_match: False
```

- **结果**：
  - **是否消费**：是。
  - **是否匹配策略**：否（其中策略 `111` 明确命中排除 camera）。
  - **是否推送 / 最终内容**：无。

---

### 索引 2

- **命令**：`python -m tests.test_notification_e2e 2`
- **告警摘要**：`alarm_id=alarm-003 category=ai level=danger camera_id=6f0aac6f215f4a7e91a9a54b48a23593`（椅子告警，区域：默认区域/产线1/6F）
- **策略日志节选**（关键点同上，不再全文粘贴）：

```text
dispatch_event start: {... 'alarm_id': 'alarm-003', 'level': 'danger', 'algorithm_name': '椅子', ...}
policies: [...]
...
is_match: False
...
is_match: False
```

- **结果**：
  - **是否消费**：是。
  - **是否匹配策略**：否（所有策略 `is_match: False`）。
  - **是否推送 / 最终内容**：无。

---

### 索引 3

- **命令**：`python -m tests.test_notification_e2e 3`
- **告警摘要**：`alarm_id=alarm-004 category=ai level=critical camera_id=3104860e4cf44c52995b554a35ea496e`（电视告警，高炉，默认区域/产线2/车间1）
- **策略日志节选**：

```text
dispatch_event start: {... 'alarm_id': 'alarm-004', 'level': 'critical', 'algorithm_name': '电视', ...}
policies: [
  {'id': '92b8a95cec3b4f6fbe6edf932be86582', 'name': '人员入侵', ...},
  {'id': '2c532be1850242e1832c7279bdd3bcea', 'name': '111', ...}
]
...
is_match: False
...
is_match: False
```

- **结果**：
  - **是否消费**：是。
  - **是否匹配策略**：否。
  - **是否推送 / 最终内容**：无。

---

### 索引 4

- **命令**：`python -m tests.test_notification_e2e 4`
- **告警摘要**：`alarm_id=alarm-005 category=ai level=info camera_id=37d229432677484c82b9c65ca1d0d0ba`（安全帽告警，默认区域/产线1）
- **结果概况**：
  - 日志模式与索引 0 类似：有 `dispatch_event start`、`policies: [...]`，但所有策略 `is_match: False`。
  - **不推送，无最终内容日志。**

---

### 索引 5

- **命令**：`python -m tests.test_notification_e2e 5`
- **告警摘要**：`alarm_id=alarm-006 category=ai level=warning camera_id=926001bb83db48bcb62cf3ebf0eb1e72`（未戴安全帽告警，5F-1）
- **策略日志节选**：

```text
dispatch_event start: {... 'alarm_id': 'alarm-006', 'algorithm_name': '未戴安全帽', ...}
policies: [... '人员入侵', '111' ...]
...
ex 匹配 camera_id 命中排除: event_camera=926001bb83db48bcb62cf3ebf0eb1e72, ex_cam_vals=['926001bb83db48bcb62cf3ebf0eb1e72']
is_match: False
```

- **结果**：
  - **是否消费**：是。
  - **是否匹配策略**：否（命中排除摄像头）。
  - **是否推送 / 最终内容**：无。

---

### 索引 6

- **命令**：`python -m tests.test_notification_e2e 6`
- **告警摘要**：`alarm_id=alarm-007 category=ai level=danger camera_id=6f0aac6f215f4a7e91a9a54b48a23593`（椅子告警，6F-1）
- **结果概况**：
  - 同样有 `dispatch_event start` 与 `policies: [...]`。
  - 所有策略 `is_match: False`，**未推送，无最终内容日志。**

---

### 索引 7

- **命令**：`python -m tests.test_notification_e2e 7`
- **告警摘要**：`alarm_id=alarm-008 category=ai level=critical camera_id=3104860e4cf44c52995b554a35ea496e`（手提包告警，高炉）
- **策略日志节选**：

```text
dispatch_event start: {... 'alarm_id': 'alarm-008', 'algorithm_name': '手提包', 'level': 'critical', ...}
policies: [... '人员入侵', '111' ...]
...
is_match: False
...
is_match: False
```

- **结果**：
  - **是否消费**：是。
  - **是否匹配策略**：否。
  - **是否推送 / 最终内容**：无。

---

### 索引 8

- **命令**：`python -m tests.test_notification_e2e 8`
- **告警摘要**：`alarm_id=alarm-009 category=ai level=info camera_id=37d229432677484c82b9c65ca1d0d0ba`（安全帽告警，LTDS 根区域）
- **结果概况**：
  - 同样只看到 `dispatch_event start` + `policies: [...]` + 多次 `is_match: False`。
  - **没有任何策略命中，也没有最终推送内容日志。**

---

### 索引 9

- **命令**：`python -m tests.test_notification_e2e 9`
- **告警摘要**：`alarm_id=alarm-010 category=ai level=warning camera_id=926001bb83db48bcb62cf3ebf0eb1e72`（电视告警，5F-1）
- **策略日志节选**：

```text
dispatch_event start: {... 'alarm_id': 'alarm-010', 'algorithm_name': '电视', ...}
policies: [...]
...
ex 匹配 camera_id 命中排除: event_camera=926001bb83db48bcb62cf3ebf0eb1e72, ex_cam_vals=['926001bb83db48bcb62cf3ebf0eb1e72']
is_match: False
```

- **结果**：
  - **是否消费**：是。
  - **是否匹配策略**：否（摄像头被排除）。
  - **是否推送 / 最终内容**：无。

---

### 索引 10 ~ 14

这几条分别覆盖了不同组合的 algorithm / level / camera / area，但从各自日志来看，模式完全一致：

- 均有 `dispatch_event start` 与 `policies: [...]`。
- 每条策略循环中最终都是 `is_match: False`。
- 日志中**完全没有出现**：
  - `matched_actions: [...]`
  - 「最终推送内容」/ `provider.send_sync` 前的那条日志。

因此可以统一结论：

- **所有 alarm_data[10~14] 也都没有命中现有任何通知策略。**

---

## 总体结论 & 建议排查方向

1. **接口链路没问题**：  
   - Redis 连接 OK（每次都有 “Redis 同步连接已建立”）。  
   - `enqueue_notification_event` 正常写入 stream。  
   - `dispatch_event` 被正常调用并能拉到策略快照。

2. **根因在于「策略匹配条件」**：  
   - 当前 `alarm_data.json` 的 15 条事件，按你现在 DB 里的策略配置（至少有 `人员入侵`、`111` 等），**都无法满足策略的 category/area/camera/level/alarm_type 条件**（部分还命中排除列表），所以不会走到推送。

3. **下一步建议**：
   - 选定你真实想要测试的某一条策略（例如企微告警的那条），把这条策略的 `match` 条件抄出来（category、alarm_config、area_config、camera_config、level、exclude 等），  
   - 然后我们可以专门构造或调整一条 `alarm_data`，**确保它 100% 满足这条策略的条件且不命中排除**，再用 `test_notification_e2e` 跑一次；  
   - 一旦有策略命中，你会在日志中看到：
     - `matched_actions: [...]` 非空；
     - 「最终推送内容」日志（包含 title/text 等），同时企微就应该能收到消息。

