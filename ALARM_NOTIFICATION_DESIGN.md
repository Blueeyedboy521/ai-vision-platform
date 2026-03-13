# 告警推送体系设计与开发计划（工业企业）

本文档给出 AI 平台在工业企业场景下的「告警推送」整体设计：**通道配置管理**、**模板管理**、**告警路由策略**、**系统告警（如摄像头掉线）接入**，以及推荐的分阶段开发计划。

---

## 1. 设计目标与原则

### 1.1 目标

- **多通道**：钉钉、企微机器人、Webhook、邮件、短信（后续）等。
- **多实例**：同一通道允许配置多个 endpoint（例如不同群、不同密钥、不同责任部门）。
- **可路由**：按区域/设备/算法/告警等级/告警类型等进行分流与多播（一个告警可推多个目标）。
- **可降噪**：节流、去重、聚合（刷屏控制）。
- **可审计**：每次推送都有记录，便于追溯失败与责任归属。
- **可扩展**：新增通道/模板/策略不影响现有链路。

### 1.2 原则（工业企业经验）

- **通道 endpoint 必须支持多个**：不同厂区/车间/班组/值班群常常不同。
- **策略与通道解耦**：策略只负责“匹配条件 → 选择哪些 endpoint”，通道只负责“如何发送”。
- **模板不强绑定 provider**：模板生成“抽象消息”，由 provider 渲染器适配钉钉/企微的 payload。
- **系统告警与业务告警统一策略**：摄像头掉线等系统事件也走同一套路由/模板/审计。
- **先做最小闭环**：先跑通配置 + 路由 + 推送 + 日志，再做聚合/升级/排班等增强。

---

## 2. 核心概念与对象模型

### 2.1 Endpoint（通道实例，允许多个）

Endpoint 表示一个可发送目标（例如某个钉钉群机器人、企微机器人、Webhook 地址）。

建议字段（示例）：

- `id`
- `provider`：`dingtalk_bot` / `wecom_bot` / `webhook` / `email` ...
- `name`：人类可读，如“厂区A-设备维护群”
- `is_enabled`
- `description` 描述
- `config`：加密存储（webhook_url、secret、关键词、代理等）
- `rate_limit`：可选，限制每分钟/每小时发送量

> 结论：**每种通道必须支持多个 endpoint**。工业企业常见“钉钉1/钉钉2 按告警类型或区域分流”。

### 2.2 Template（模板，不强绑定 provider）

模板在业务侧只抽象成两种类型：**文字** 和 **图文**，由通道适配层负责映射到钉钉/企微各自支持的消息类型。

对外暴露的模板类型：

- `type: "text"`：纯文字/markdown，无图片、无跳转链接。
- `type: "rich"`：图文，包含标题 + 文本 + 可选缩略图 + 可选详情链接。

抽象消息结构（模板渲染输出）：

- `title`
- `text`（支持 markdown）
- `image_url`（可选，缩略图）
- `link_url`（可选，跳转告警详情页）

模板管理建议字段：

- `id`、`name`、`is_enabled`
- `type`：`text` / `rich`
- `content`：模板内容（支持变量，例如 `{{camera_name}}`、`{{area_name}}`、`{{level}}`、`{{snapshot_url}}` 等），用于渲染出上面的抽象字段。
- `version` / `updated_at`

实现层面的通道适配（仅在内部说明，不暴露给策略/业务）：

- 钉钉机器人：
  - `type=text` → `text` 或 `markdown` 消息。
  - `type=rich` → 优先用 `link`（`title/text/messageUrl/picUrl`），后续如需多图再扩展 `feedCard`。
- 企微机器人：
  - `type=text` → `text` 或 `markdown`。
  - `type=rich` → 优先用 `news`（单条图文）或 `textcard`，根据具体 UI 需求选择。

模板本身**不绑定 provider**，provider 的差异通过渲染器内部适配实现，业务只需要选择「文字」或「图文」模板即可。

### 2.3 Policy（路由策略）

Policy 负责：**匹配条件 → 输出推送动作**。一个 Policy 可命中多个 Endpoint。

建议字段（示例）：

- `id`、`name`、`priority`、`is_enabled`
- `match_desc`：匹配条件中文描述（冗余，由后端自动生成，便于前端列表展示/搜索）
- `actions_desc`：动作中文描述（冗余，由后端自动生成，便于前端列表展示/搜索）
 - `match`：
  - `category`：`ai`（业务告警）/ `system`（系统告警）
  - `alarm_config[]`：报警类型配置（支持多选），数组元素结构：
    - `value`：内部标识  
      - 当 `category=ai` 时，存 `algorithm_id`（算法 ID，对应算法管理中的启用算法）；  
      - 当 `category=system` 时，存系统告警 code（如 `camera_offline` / `storage_error` 等）。
    - `label`：人类可读名称（例如 `烟火模型-烟雾检测`、`设备离线`），用于前端展示与中文搜索。
  - `area_config[]`：区域配置（支持多选），数组元素结构：
    - `value`：区域 ID（`areas.id`）；  
    - `label`：名称层级路径，例如 `默认区域 / 车间1 / 产线A`；  
    - `idPath`：ID 层级路径，例如 `/area_root/area_child/area_leaf`，匹配时会根据此路径做 `area_path` 判断（含通配符）。
  - `camera_config[]`（可选，支持多选）：监控设备配置，数组元素结构：
    - `value`：摄像头 ID（`cameras.id`）；  
    - `label`：摄像头名称。
  - `level[]`（支持多选：info/warning/danger/critical）
  - `exclude`（可选，排除条件，结构与上面一致）：
    - `alarm_config[]` / `area_config[]` / `camera_config[]` / `level[]`
  - `time_window`（可选，控制策略生效时间段）：
    - `start: "HH:MM"`，`end: "HH:MM"`。
    - 若 `start <= end`：表示同一天内，例如 `08:00-18:00`。
    - 若 `start > end`：表示跨天时间段，例如 `22:00-06:00`。
    - 不配置 `time_window` 时，视为全天生效。
- `actions[]`（动作数组：一个策略可配置多个 action）
  - `endpoint_ids[]`：多播目标（一个 action 推送到多个 endpoint）
  - `template_id`：可选，该 action 使用的模板
  - `throttle_sec`：可选，节流秒数；同一 dedup_key 在 N 秒内最多推 1 条
  - `dedup_key`：可选，去重维度表达式，例如 `category+alarm_type+camera_id+level`
  - `push_order`：可选，动作执行顺序（小优先）
  - `retry_times`：可选，失败重试次数（不含首次）
  - `retry_interval_sec`：可选，重试间隔（秒）

说明：

- `match` 中不再直接暴露 `alarm_type[]/area_path[]/camera_id[]` 等原始字段，而是通过 `alarm_config/area_config/camera_config` 这三类配置对象统一承载 **id + label (+ idPath)**，方便前后端在匹配和展示之间解耦：
  - 匹配时，后端从 `alarm_config.value/area_config.idPath/camera_config.value` 还原出用于判断的内部 ID 或路径；
  - 展示与搜索时，优先使用 `label` 做人类可读的中文描述。
- `actions` 的标准形态为数组（`list[dict]`），用于表达「同一 match 下，不同模板/不同通道组/不同节流与重试策略」。
- `match_desc/actions_desc` 会在创建/更新策略时由后端自动生成：解析 `alarm_config/area_config/camera_config/endpoint_ids/template_id` 等为名称并拼成可读中文，用于列表展示与关键字搜索（避免前端面对大量 id）。

说明：

- 本阶段 `time_window` 只做“单时间段”，不做班次/周几/节假日。

### 2.4 DeliveryLog（推送审计）

建议独立记录推送结果，便于重试与排障：

- `id`
- `alarm_id`（统一事件标识：业务告警=alarms.id；系统告警=系统侧生成的唯一ID，不入 alarms 表，仅用于追踪/审计）
- `endpoint_id`
- `template_id`
- `status`：success/failed/skipped(throttle)
- `error`（脱敏）
- `request_meta` / `response_meta`（脱敏）
- `created_at`

---

## 3. 告警与系统事件如何接入

### 3.1 业务告警（AI 检测告警）

沿用现有链路：

- Engine 产生告警 → Redis `alarm_queue` → app `AlarmConsumer` 入库与 WebSocket 推送。
- 推送体系只需要在 app 消费到告警后，调用 `NotificationService.dispatch(alarm)` 即可。

### 3.2 系统告警（摄像头掉线/恢复）

建议用统一事件结构（不一定进 `alarms` 表，可按需选择）：

- `category = "system"`
- `alarm_type = "camera_offline"` / `"camera_online"` 等
- `level = warning/danger/critical`
- `camera_id/camera_name/area_name`
- `timestamp`
- `title/description`
- `snapshot_url`：通常为空

落库约定：

- 系统告警 **不入 `alarms` 表**。
- 系统告警只写 `NotificationDeliveryLog`，并以 `alarm_id` 作为该系统事件的唯一标识，便于后续审计与排障。

#### 掉线/恢复判定（边沿触发 + 抖动抑制）

推荐逻辑：

- 监控任务周期性计算 online（你们已有基于快照/心跳的机制）
- 仅当状态发生变化时发事件：
  - `online: True -> False`：camera_offline
  - `online: False -> True`：camera_online（可选）
- 抖动抑制：
  - 连续 N 次失败才判定掉线
  - 连续 M 次成功才判定恢复

---

## 4. 推送引擎执行流程（建议）

### 4.1 dispatch_event（Worker 消费侧）执行步骤

> 目标：**高内聚、低耦合**，且尽量减少 DB 全表读取；配置数据优先走 Redis 快照缓存。

#### 事件入队与消费机制（Redis Stream）

- **生产者**（AlarmConsumer / live_heartbeat_monitor 等）：调用 `enqueue_notification_event(event)`  
  - 通过 `XADD notification:events:stream * data "<json>"` 写入事件流。
- **消费者**（NotificationWorkerPool）：使用 Consumer Group 监听  
  - `XREADGROUP GROUP notification_workers <consumer> BLOCK 1000 COUNT 1 STREAMS notification:events:stream >`
  - 成功处理后 `XACK` 确认。

1. 输入：`event`（业务告警或系统事件，统一结构）
2. 获取策略列表 `policies`（按类别拆分）：
   - 调用 `_load_policies_by_category(category)`（与 `dispatch_event` 平级函数）
   - **先查 Redis Hash**：
     - AI 告警：`notification:policies:ai`
     - 系统告警：`notification:policies:system`
   - 若 Redis 不存在/为空：**读取 DB**（按 `match.category` 过滤该类别的启用策略）并 **回写 Redis Hash**（field=id,value=json）
3. 循环 `policies`，判断是否匹配 `_match_policy(event, policy.match)`：
   - 匹配则将该策略的 `actions[]` 展开写入 `matched_actions`（并附带 `_policy_id`）
4. 对 `matched_actions` 排序：
   - `push_order` 越小越先执行
5. 循环执行 `matched_actions`（不考虑历史 actions 兼容形态）：
   1) **限流/去重**（action 级）：
      - 若同时配置 `dedup_key` 与 `throttle_sec>0`，则计算 `dedup_value`
      - 在 Redis 写入节流键：`SET notif:throttle:{policy_id}:{dedup_value} 1 NX EX {throttle_sec}`
      - 若写入失败（key 已存在）则表示仍在窗口期：**直接跳过该 action，不做任何推送动作**
   2) **获取模板**：
      - **按需单条获取**（在 action 循环里）：
        - 先 Redis：`HGET notification:templates:snapshot {template_id}`
        - 缓存 miss 再 DB 查一条，并 `HSET` 回写 Redis
      - 模板禁用或不存在则回退使用 `event.title/event.text`
   3) **渲染抽象消息**：
      - 调用 `_render_text_with_vars()` 做 `{{var}}` 变量替换
      - 输出抽象消息：`title/text/image_url/link_url`
   4) **循环 endpoint_ids 推送**：
      - endpoint 同样 **按需单条获取**（在 endpoint_ids 循环里）：
        - 先 Redis：`HGET notification:endpoints:snapshot {endpoint_id}`
        - 缓存 miss 再 DB 查一条，并 `HSET` 回写 Redis
      - 根据 endpoint.provider 获取 provider 实现并发送（必要时解密 endpoint.encrypted_config）
      - 本阶段**不做重试**：每个 endpoint 只发送一次（失败记录到 DeliveryLog）
   5) **审计**：
      - 写 `NotificationDeliveryLog`（success/failed，失败原因截断）

---

## 5. 开发计划（分阶段）

### Phase A（最小闭环，1~2 周）

- **Endpoint 管理**（增删改查 + 启用/禁用 + 连通性测试）
- **Template 管理**（增删改查 + 预览渲染）
- **Policy 管理**（按区域/算法/等级/类别匹配 + 多 endpoint 多播）
- **推送执行**（先支持：钉钉机器人 + 企微机器人）
- **DeliveryLog 审计**（至少能查失败原因）

交付标准：

- 能做到“某区域 critical 告警推到钉钉A，warning 推到企微B”
- 能做到“系统告警 camera_offline 推到运维群”

### Phase B（降噪与可靠性，1~2 周）

- **策略级 throttle**（同类告警 N 秒内最多一条）
- **聚合推送**（1 分钟内合并摘要，避免刷屏）
- **失败重试**（指数退避 + 最大次数 + 死信记录）
- **provider 降级**（卡片不支持时降级为文本/markdown）

### Phase C（升级与协同，按需）

- **升级策略**：未确认超时 → 推更高层级 endpoint
- **值班/排班**：扩展 time_window（周几/节假日/班次表）
- **订阅制**：用户级订阅（个人通知）

---

## 6. 决策点（评审时需要确认）

1. 系统告警是否入 `alarms` 表统一查询，还是单独 `system_events` / 仅记录 DeliveryLog？
2. Policy 匹配“多策略同时命中”的合并规则：合并 endpoint 去重？是否允许覆盖模板？
3. 推送执行是同步还是异步（建议异步 worker）？
4. Endpoint 的 config 加密方案（KMS/环境变量密钥/数据库加密字段）？

