# AI 视觉平台 - 后端架构设计

## 一、技术选型

### 1.1 整体技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Web 框架 | FastAPI | 异步支持好，自动生成 API 文档 |
| 流媒体服务器 | ZLMediaKit | 国产开源，支持 GB28181，性能优秀 |
| 数据库 | MySQL 8.0 | 业务数据存储 |
| 缓存/消息 | Redis | Pub/Sub、队列、Token 黑名单 |
| AI 推理 | YOLO (Ultralytics) | 目标检测、分类 |
| 视频处理 | OpenCV + FFmpeg | 拉流、解码、编码 |
| 前端框架 | Vue 3 + TypeScript | SPA 应用 |
| UI 组件 | Naive UI | 后台管理界面 |
| 视频播放 | flv.js | HTTP-FLV 播放 |

### 1.2 流媒体服务器选型对比

| 特性 | MediaMTX | ZLMediaKit | SRS |
|------|----------|------------|-----|
| 语言 | Go | C++ | C++ |
| 协议支持 | RTSP/RTMP/HLS/WebRTC | RTSP/RTMP/HLS/WebRTC/GB28181 | RTMP/HLS/WebRTC/SRT |
| 性能 | 中等 | 高 | 高 |
| 权限控制 | Hook 回调 | Hook 回调 + API | Hook 回调 |
| 部署难度 | 最简单（单二进制） | 中等 | 中等 |
| 文档 | 英文，简洁 | 中文，详细 | 中文，完善 |

**推荐 ZLMediaKit**，理由：
- 国产开源，中文文档完善
- 支持 GB28181 国标对接
- 性能优秀，单机可支持数千路
- 权限控制完善，支持多种 Hook 回调

---

## 二、后端整体结构

```
backend/
│
├── app/                              # FastAPI 业务 API 层
│   ├── main.py                       # API 入口
│   ├── api/                          # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py                   # 依赖注入 (认证、数据库会话)
│   │   └── endpoints/                # 各业务端点
│   │       ├── auth.py               # 认证 (登录、刷新Token、登出)
│   │       ├── cameras.py            # 摄像头管理
│   │       ├── areas.py              # 区域管理
│   │       ├── models.py             # 模型管理
│   │       ├── algorithms.py         # 算法管理
│   │       ├── alarms.py             # 告警管理
│   │       ├── system.py             # 系统管理
│   │       └── media_hooks.py        # 【新增】ZLMediaKit Hook 回调处理
│   │
│   ├── models/                       # SQLAlchemy ORM 模型
│   │   ├── __init__.py
│   │   ├── base.py                   # 基类 (AuditMixin, generate_uuid)
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── area.py
│   │   ├── model.py
│   │   ├── algorithm.py
│   │   ├── camera_algorithm.py
│   │   └── alarm.py
│   │
│   ├── schemas/                      # Pydantic 请求/响应模式
│   │   ├── __init__.py
│   │   ├── common.py                 # 通用响应结构
│   │   ├── auth.py
│   │   ├── camera.py
│   │   ├── area.py
│   │   ├── model.py
│   │   ├── algorithm.py
│   │   └── alarm.py
│   │
│   ├── core/                         # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py                 # 配置类 (Settings)
│   │   ├── database.py               # 数据库连接
│   │   ├── security.py               # JWT、密码加密
│   │   └── redis.py                  # Redis 连接池
│   │
│   ├── services/                     # 业务逻辑服务
│   │   ├── __init__.py
│   │   ├── auth_service.py           # Token 刷新、黑名单管理
│   │   ├── camera_service.py
│   │   ├── stream_service.py         # 流媒体管理 (调用 ZLMediaKit)
│   │   ├── alarm_service.py
│   │   └── config_publisher.py       # 配置变更发布 (通知 Engine)
│   │
│   ├── websocket/                    # WebSocket 处理
│   │   ├── __init__.py
│   │   ├── manager.py                # 连接管理器
│   │   └── handlers.py               # 订阅 Redis 并转发
│   │
│   └── consumer/                     # 异步消费者 (FastAPI 内线程池)
│       ├── __init__.py
│       ├── worker_pool.py            # 线程池管理 (启动/停止)
│       ├── alarm_consumer.py         # 告警消费 Worker (存库)
│       └── notification_sender.py    # 消息发送器 (钉钉、邮件、短信)
│
├── engine/                           # 视频处理引擎 (核心)
│   ├── main.py                       # 引擎入口
│   ├── scheduler.py                  # 主调度器
│   │
│   ├── inference/                    # 推理服务
│   │   ├── __init__.py
│   │   ├── service.py                # InferenceService 进程主类
│   │   ├── worker.py                 # InferenceWorker 线程
│   │   ├── model_loader.py           # 模型加载器 (支持 YOLO/ONNX/TensorRT)
│   │   └── model_registry.py         # 模型注册表
│   │
│   ├── pipeline/                     # 流处理管道
│   │   ├── __init__.py
│   │   ├── pipeline.py               # Pipeline 进程主类
│   │   ├── stream_reader.py          # 拉流线程 (RTSP 解码)，按 fps 墙钟节流取帧
│   │   ├── stream_writer.py          # 推流线程：FFmpeg 子进程推 RTMP，按 fps 墙钟节流发帧
│   │   └── result_handler.py         # 结果处理线程
│   │
│   ├── queue/                        # 队列抽象层
│   │   ├── __init__.py
│   │   ├── interface.py              # 队列接口定义
│   │   ├── memory_queue.py           # 内存队列 (multiprocessing.Queue)
│   │   └── redis_queue.py            # Redis 队列 (分布式部署用)
│   │
│   └── utils/                        # 工具类
│       ├── __init__.py
│       ├── dedup.py                  # 去重过滤 (时间窗口 + IoU)
│       ├── region.py                 # 区域检测 (点是否在多边形内)
│       └── frame_utils.py            # 帧处理工具
│
├── common/                           # 公共模块 (app 和 engine 共用)
│   ├── __init__.py
│   │
│   ├── redis/                        # Redis 操作封装
│   │   ├── __init__.py
│   │   ├── client.py                 # Redis 客户端单例
│   │   ├── pubsub.py                 # Pub/Sub 封装
│   │   └── channels.py               # Channel 名称常量定义
│   │
│   ├── media/                        # 流媒体服务 (ZLMediaKit)
│   │   ├── __init__.py
│   │   ├── zlm_client.py             # ZLMediaKit API 客户端
│   │   ├── stream_manager.py         # 流管理 (申请端口、添加/删除流)
│   │   └── hooks.py                  # Hook 鉴权回调数据结构
│   │
│   ├── storage/                      # 文件存储
│   │   ├── __init__.py
│   │   ├── interface.py              # 存储接口
│   │   ├── local_storage.py          # 本地文件存储
│   │   └── oss_storage.py            # 对象存储 (MinIO/阿里云 OSS)
│   │
│   ├── notification/                 # 消息推送
│   │   ├── __init__.py
│   │   ├── interface.py              # 推送接口
│   │   ├── dingtalk.py               # 钉钉机器人
│   │   ├── wechat.py                 # 企业微信
│   │   ├── email_sender.py           # 邮件
│   │   └── webhook.py                # 通用 Webhook
│   │
│   └── logging/                      # 日志配置
│       ├── __init__.py
│       └── logger.py                 # Loguru 配置
│
├── config/                           # 配置文件
│   ├── settings.py                   # 全局配置 (Pydantic Settings)
│   └── logging.yaml                  # 日志配置文件
│
├── scripts/                          # 运维脚本
│   ├── init_db.py                    # 初始化数据库
│   ├── migrate.py                    # 数据库迁移
│   └── test_camera.py                # 测试摄像头连接
│
├── tests/                            # 测试代码
│   ├── test_api/
│   ├── test_engine/
│   └── conftest.py
│
├── models/                           # AI 模型文件目录
│   └── .gitkeep
│
├── logs/                             # 日志目录
│   └── .gitkeep
│
├── data/                             # 数据目录
│   ├── alarms/                       # 告警截图
│   └── videos/                       # 视频片段
│
├── requirements.txt                  # Python 依赖
├── Dockerfile                        # Docker 构建
├── docker-compose.yml                # Docker Compose
└── README.md                         # 说明文档
```

---

## 三、Redis 使用与约定

### 3.1 Pub/Sub 频道

- **检测结果推送**
  - `detections:{camera_id}`：Engine 推送单路摄像头实时检测框，FastAPI 订阅并转发到 WebSocket。
- **告警推送**
  - `alarms:realtime`：告警消费者发布实时告警，WebSocket 处理器订阅并推送给前端。
- **配置更新（FastAPI → Engine）**
  - `engine:config_update`：Engine 配置更新总线，消息结构：
    - `action`: 配置动作类型（字符串）
    - `data`: 具体内容（字典）
    - `timestamp`: ISO 时间
  - `action` 取值与 `ConfigAction` 枚举一致：
    - 摄像头：`camera_add` / `camera_update` / `camera_delete` / `camera_start` / `camera_stop`
    - 模型：`model_add` / `model_update` / `model_delete`
    - 算法：`algorithm_add` / `algorithm_update` / `algorithm_delete`
    - 摄像头-算法绑定：`camera_algorithm_add` / `camera_algorithm_update` / `camera_algorithm_delete`
- **系统状态**
  - `engine:heartbeat`：引擎心跳（预留）
  - `pipeline:status:{camera_id}`：单路 Pipeline 状态（预留）

### 3.2 Redis Key 设计

统一由 `common.redis.RedisKeys` 管理，避免硬编码：

- **告警队列**
  - `alarm_queue`：Engine 写入告警消息，AlarmConsumer 从队列消费并入库 / 推送。
- **Token 黑名单 / 用户缓存**
  - `token:blacklist:{token_hash}`：JWT 黑名单。
  - `user:cache:{user_id}`：用户信息缓存。
- **摄像头配置（FastAPI → Engine）**
  - `camera:config:{camera_id}`：摄像头基础配置，包含 RTSP 地址、帧率、启用状态等。
- **模型配置（FastAPI → Engine）**
  - `model:config:{model_id}`：单个模型配置快照，例如：
    - `id`, `code`, `name`, `model_type`, `model_path`, `classes`, `is_enabled` 等。
- **算法配置（FastAPI → Engine）**
  - `algorithm:config:{algorithm_id}`：单个算法能力配置快照，例如：
    - `id`, `code`, `name`, `model_id`, `target_classes`, `default_confidence`, `alert_config`, `is_enabled` 等。
- **摄像头-算法绑定配置（FastAPI → Engine）**
  - `camera:algorithm:config:{camera_id}:{algorithm_id}`：某摄像头与某算法的一条配置：
    - `camera_id`, `algorithm_id`, `model_id`, `confidence`（生效置信度）, `alert_config`（生效告警配置）, `regions`, `is_enabled`。
- **告警去重**
  - `alarm:dedup:{camera_id}:{algorithm_id}`：按摄像头 + 算法维度的去重 Key。
- **摄像头直播心跳**
  - `camera:live:heartbeat:{camera_id}`：前端播放直播流时每 60 秒上报一次心跳，便于后台任务判断超时并通知 Engine 关闭无观众的推流或 Pipeline。

整体约定：

- **DB 是主数据源**：所有摄像头、模型、算法与绑定配置均以 MySQL 为准。
- **Redis 存快照 + 事件**：
  - FastAPI 在增删改配置成功后，写/删对应 Redis Key。
  - 同时通过 `engine:config_update` 发布一条事件，让 Engine 感知变更。
- **Engine 仅依赖 Redis**：
  - 启动时从各类 `config:*` Key 拉取快照。
  - 运行过程中订阅 `engine:config_update`，根据事件类型到 Redis 读取最新配置并更新内存（当前版本先以日志为主，后续可在此基础上实现真正的热更新）。
- **应用启动全量同步**：FastAPI 启动时通过 `app.services.bootstrap_sync.sync_configs_to_redis_and_streams()` 将当前 DB 中的模型、算法、摄像头及摄像头-算法绑定全量写入 Redis，并调用 `stream_manager.register_stream` 为每个摄像头注册流，保证 Engine 冷启动即可从 Redis 读到完整配置；摄像头增/改/删时 API 同步写/删 `camera:config:{camera_id}`。

### 3.3 摄像头启用状态与直播控制

这一小节总结「摄像头 / 算法启用状态」以及「直播心跳」是如何在 **前端 → FastAPI → Redis → Engine** 之间协同工作的，方便后续扩展代码时快速对齐设计。

#### 3.3.1 启用状态的传递路径

- **数据库字段**
  - 摄像头表 `cameras`：字段 `is_enabled` 表示该摄像头当前是否启用。
  - 摄像头-算法绑定表 `camera_algorithms`：字段 `is_enabled` 表示该条绑定（某摄像头使用某算法）是否生效。
- **FastAPI 写 Redis（应用启动 + 增删改时）**
  - `bootstrap_sync` 在启动阶段会把 DB 中所有启用/未启用的摄像头、算法及绑定写入 Redis：
    - `camera:config:{camera_id}` 中包含：`id`, `name`, `rtsp_url`, `fps`, `is_enabled`。
    - `camera:algorithm:config:{camera_id}:{algorithm_id}` 中包含：`camera_id`, `algorithm_id`, `model_id`, `confidence`, `alert_config`, `regions`, `is_enabled`。
  - 后续通过 `cameras.py` / `algorithms.py` 里的增删改接口更新配置时，也会同步写/删上述 Key，保证 Redis 中的状态与 DB 一致。
- **Engine 加载配置时的过滤逻辑**
  - `Scheduler._load_config()` 在从 Redis 扫描配置时，统一按 `is_enabled` 做过滤：
    - 加载摄像头基础配置：
      - 仅当 `cfg.get("is_enabled", True)` 为真时，才创建 `CameraConfig` 放入 `self.cameras`；禁用摄像头不会被 Engine 管理，不会启动 Pipeline。
    - 加载摄像头-算法绑定配置：
      - 仅当绑定配置 `is_enabled=True` 时，才将该算法信息附加到 `self.cameras[camera_id].algorithms` 中；禁用的绑定不会参与推理。
- **前端行为约束**
  - 在前端「摄像头编辑」中勾选/取消“启用”会改写 `cameras.is_enabled`，进而影响：
    - 是否允许通过 `/cameras/{id}/start` 启动该摄像头；
    - Engine 在下一次刷新 Redis 快照后是否还会为该摄像头创建/维持 Pipeline。

#### 3.3.2 摄像头启动/停止命令与 Engine 协同

- **启动摄像头 `/cameras/{id}/start`**
  - FastAPI 侧：
    - 先从 DB 查询摄像头：
      - 若不存在：返回 `404`。
      - 若 `is_enabled=False`：返回 `400`，提示「摄像头未启用，请先在编辑页启用后再播放」。
    - 若合法，则执行两步：
      1. 将 `camera_id` 加入集合 `cameras:live:started`（`RedisKeys.CAMERAS_LIVE_STARTED`），表示该摄像头当前存在至少一个直播会话。
      2. 通过 `ConfigPublisher.publish_camera_start(camera_id)` 向频道 `engine:config_update` 发布 `camera_start` 事件。
  - Engine 侧（`Scheduler._handle_config_event`）：
    - 收到 `camera_start` 后，将 `camera_id` 记录为「点播中」（`live_started`），并调用 `_reconcile_camera_pipeline(camera_id)`。
    - `_reconcile_camera_pipeline` 会结合「点播状态 + 启用算法」决定是否启动 Pipeline，以及启动模式（见下方 *Pipeline 三种模式*）。
- **停止摄像头 `/cameras/{id}/stop`**
  - FastAPI 侧：
    - 从 DB 检查摄像头存在性。
    - 从集合 `cameras:live:started` 中移除该 `camera_id`。
    - 通过 `ConfigPublisher.publish_camera_stop(camera_id)` 发布 `camera_stop` 事件。
  - Engine 侧：
    - 收到 `camera_stop` 后，将 `camera_id` 从「点播中」移除，并调用 `_reconcile_camera_pipeline(camera_id)`：
      - 若该摄像头 **没有启用算法**：停止 Pipeline（不再拉/推流）。
      - 若该摄像头 **有启用算法**：切换为 `inference_only`（保留拉流+推理，但**停止推流**），避免无人观看时仍推流浪费资源。

##### 3.3.2.1 Pipeline 三种模式（按点播与算法自动切换）

Engine 启动/切换 Pipeline 时，会把 `mode` 传入 `Pipeline.run()`，在 Pipeline 进程内按模式启动不同线程：

- **`live_only`（仅点播转推）**
  - 启动：`StreamReader` + `StreamWriter`
  - 不启动：推理请求（`request_queue=None`）、`ResultHandler`
  - 适用：摄像头**无启用算法**，但前端正在点播，需要实时画面
- **`inference_only`（后台推理，不推流）**
  - 启动：`StreamReader` + `ResultHandler`（以及推理请求）
  - 不启动：`StreamWriter`
  - 适用：摄像头**有启用算法**，但当前无人点播；仍需后台推理/告警/事件推送
- **`full`（点播 + 推理）**
  - 启动：`StreamReader` + `StreamWriter` + `ResultHandler`
  - 适用：摄像头**有启用算法**，且前端正在点播

##### 3.3.2.2 Engine 启动时的“是否启动 Pipeline”规则

`Scheduler._load_config()` 会从 Redis 读取：

- 摄像头基础配置：`camera:config:{camera_id}`
- 启用的摄像头-算法配置：`camera:algorithm:config:{camera_id}:{algorithm_id}`（仅 `is_enabled=True` 的绑定会进入 `CameraConfig.algorithms`）
- 点播集合：`cameras:live:started`（`RedisKeys.CAMERAS_LIVE_STARTED`）

随后在 `Scheduler._start_pipelines()` 中按规则启动：

- **无启用算法 + 未点播**：不启动 Pipeline
- **无启用算法 + 点播中**：启动 `live_only`
- **有启用算法 + 未点播**：启动 `inference_only`
- **有启用算法 + 点播中**：启动 `full`

#### 3.3.3 直播心跳与自动关闭推流

为避免「浏览器已经关闭但 Engine 仍在推流」浪费资源，系统通过 Redis Key + 后台任务实现直播心跳检测与自动关流：

- **前端心跳上报**
  - 播放页面在开始播放后，每隔 ~60 秒调用：
    - `POST /cameras/{camera_id}/live-heartbeat`
  - FastAPI 侧实现：
    - 写入 `camera:live:heartbeat:{camera_id}`（`RedisKeys.camera_live_heartbeat`），Value 为当前时间戳，TTL 设置为 `LIVE_HEARTBEAT_TIMEOUT_SEC`（目前为 90 秒）。
- **“已启动直播”集合**
  - 当 `POST /cameras/{id}/start` 成功时，将 `camera_id` 加入集合：
    - `cameras:live:started`（`RedisKeys.CAMERAS_LIVE_STARTED`）。
  - 当 `POST /cameras/{id}/stop` 被调用时，或心跳检测认为超时时，会把 `camera_id` 从该集合中移除。
- **后台心跳检测任务 `live_heartbeat_monitor`**
  - 位置：`app/services/live_heartbeat_monitor.py`。
  - 启动：
    - 在 `app.main` 的 `lifespan` 中，通过 `start_live_heartbeat_monitor()` 创建一个后台 `asyncio` 任务，按固定间隔（`CHECK_INTERVAL_SEC`，当前为 45 秒）执行一次检测。
  - 检测流程（伪代码）：

    ```python
    members = SMEMBERS("cameras:live:started")
    for camera_id in members:
        key = f"camera:live:heartbeat:{camera_id}"
        if EXISTS(key):
            continue  # 心跳正常
        # 心跳已过期：从集合移除并通知 Engine 停止
        SREM("cameras:live:started", camera_id)
        publish_camera_stop(camera_id)  # 触发 Engine 关闭该路 Pipeline
    ```

  - 关闭：
    - 在 `lifespan` 的关闭阶段调用 `stop_live_heartbeat_monitor()`，通过 `task.cancel()` 方式让循环优雅结束。

综合以上三小节，**前端启用开关 + 播放心跳** 最终会在 Engine 侧转化为「是否启动 Pipeline」以及「以何种模式运行（full / live_only / inference_only）」，从而精确控制 **拉流 / 推流 / 推理** 的资源开销。新同事只要沿用这套 Redis Key 与事件约定，即可扩展更多控制能力（例如：按用户级别限流、并发路数控制、无人观看自动停推流、仍保留后台推理等）。

---

## 四、存储设计（本地 / MinIO / S3）

### 4.1 存储接口与实现

- 抽象接口：`common.storage.StorageInterface`
  - 基础文件操作：`save_file` / `save_image` / `get_file` / `delete_file` / `exists` / `get_url`
  - 上传/下载能力：`upload_file(path, upload_path)` / `download_file(path, download_path)`
  - 业务辅助方法：`generate_alarm_path` / `generate_video_path` 等，用于统一告警截图、视频片段等路径规则。
- 实现：
  - `LocalStorage`：本地磁盘目录（用于开发环境）。
  - `MinIOStorage`：基于 MinIO 的 S3 协议实现。
- 工厂方法：`common.storage.get_storage()` 根据配置返回对应实现。

### 4.2 目录规划（正式文件）

所有正式文件在存储根（本地目录或 MinIO bucket）下按业务划分子目录：

- `models/`：AI 模型文件
  - 例如：`models/{model_id}/{filename}.onnx`
- `alarms/`：告警截图（由 `generate_alarm_path` 生成）
  - 例如：`alarms/2026/02/11/camera_001_1739260800000.jpg`
- `videos/`：告警视频片段（由 `generate_video_path` 生成）
  - 例如：`videos/2026/02/11/camera_001_1739260800000.mp4`
- `avatars/`：用户头像
  - 例如：`avatars/{user_id}/avatar.jpg`
- 其他业务文件可继续在根下扩展：`reports/`、`exports/` 等。

### 4.3 临时文件与正式文件

为避免前端上传但最终取消保存导致存储浪费，存储分为：

- **临时文件**：
  - 路径统一加前缀 `tmp/`：
    - `tmp/{category}/{user_prefix}/{filename}`
    - 示例：`tmp/model/user_123456/model.onnx`
  - 前端在“选择文件但还没点击业务保存”时，调用统一的文件上传 API，将文件写入 `tmp/` 下。
  - 可以通过定时任务或后台脚本清理过期的临时文件。
- **正式文件**：
  - 路径不包含 `tmp/`，直接放在业务目录，如：
    - `models/{model_id}/{filename}`
    - `avatars/{user_id}/avatar.jpg`
  - 一旦对应业务对象（模型 / 用户等）在数据库中创建成功，即视为正式文件。

### 4.4 文件 API 设计

统一的文件 API（`app/api/endpoints/files.py`，前缀 `/api/v1/files`）：

- **上传临时文件**
  - `POST /files/temp`
  - 入参：
    - `file`: multipart 上传文件
    - `category`: 业务分类（如 `model` / `avatar` / `snapshot` / `video` 等）
  - 行为：
    - 使用 `get_storage()` 选择当前存储实现。
    - 将文件写入 `tmp/{category}/{user_prefix}/{filename}`。
  - 返回：
    - `key`: 存储 key（例如 `tmp/model/user_xxx/model.onnx`）
    - `url`: 存储实现返回的访问 URL（MinIO 下为 HTTP 地址，本地存储为 `/static/...` 相对路径）。

- **临时文件删除 / 下载**
  - `DELETE /files/temp?key=...`：删除临时文件。
  - `GET /files/temp?key=...`：直接下载临时文件内容（调试/预览用途）。

- **正式文件下载 / 删除**
  - `GET /files?key=...`：下载正式文件（`models/...`、`avatars/...` 等）。
  - `DELETE /files?key=...`：删除正式文件（通常通过业务逻辑间接调用）。

以上接口统一封装了 storage 访问逻辑，业务侧只关心 key，而不关心底层是本地还是 MinIO。

### 4.5 模型文件上架流程

模型上架时，前后端配合采用“**先临时，后转正**”的策略：

1. **前端选择模型文件时**：
   - 先调用 `POST /files/temp` 上传模型文件到 `tmp/model/...`。
   - 表单中只暂存返回的 `key`（临时路径）和预览 URL，不直接写入模型表。
2. **点击“保存上架”时**：
   - 前端将临时文件 `key` 一并提交给模型创建接口 `/models`，写入 `ModelCreate.model_path` 字段。
3. **后端创建模型（`create_model`）时**：
   - 模型记录插入成功后，检查 `model.model_path` 是否以 `tmp/` 开头：
     - 如果是，则视为临时路径：
       - 调用 `storage.get_file(temp_key)` 读取临时文件。
       - 生成正式路径：`models/{model_id}/{filename}`。
       - 调用 `storage.save_file(..., final_key)` 写入正式存储。
       - 更新 `model.model_path = final_key` 并提交事务。
       - 删除临时文件：`storage.delete_file(temp_key)`。
     - 如果不是（例如手工指定了已存在的 models/ 路径），则直接使用原值。
4. **后续使用**：
   - 前端通过模型详情中的 `model_path` 字段（或后端包装好的 URL）展示 / 下载模型文件。

这样可以保证：

- 上传中断或取消时，只占用 `tmp/` 空间，可由后台任务定期清理。
- 模型一旦上架成功，文件转存到 `models/{model_id}/...`，路径与业务 ID 绑定，便于管理与备份。

---

## 三、两大独立服务

后端由**两个独立服务**组成，可以分别启动：

```
┌─────────────────────────────────────────────────────────────────────┐
│                       AI 视觉平台后端                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌───────────────────────┐       ┌───────────────────────┐        │
│   │   FastAPI 服务         │       │   视频处理引擎         │        │
│   │   (业务 API)           │       │   (Engine)            │        │
│   │                       │       │                       │        │
│   │   • HTTP/REST 接口    │       │   • 视频拉流/推流      │        │
│   │   • WebSocket 推送    │       │   • AI 推理           │        │
│   │   • 数据库读写        │       │   • 告警生成          │        │
│   │   • 用户认证          │       │   • 去重过滤          │        │
│   │                       │       │                       │        │
│   │   端口: 8000          │       │   无端口 (内部进程)    │        │
│   └───────────────────────┘       └───────────────────────┘        │
│            │                                  │                    │
│            │                                  │                    │
│            └──────────┬───────────────────────┘                    │
│                       │                                            │
│                       ▼                                            │
│              ┌─────────────────┐                                   │
│              │    数据库       │                                   │
│              │    (MySQL)      │                                   │
│              └─────────────────┘                                   │
│                                                                     │
│   通信方式:                                                         │
│   • Engine 写入告警到数据库                                         │
│   • Engine 通过 WebSocket 推送实时检测结果到前端                     │
│   • FastAPI 读取数据库展示数据                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、FastAPI 服务启动流程

FastAPI 服务提供业务 API，相对简单：

```
先启动虚拟环境
D:\workspace\python\ai-vision-platform>D:/software/Anaconda3/Scripts/activate

(base) D:\workspace\python\ai-vision-platform>conda activate base
启动命令: uvicorn app.main:app --host 0.0.0.0 --port 8000

启动流程:
┌─────────────────────────────────────────────────────────────────────┐
│  1. 加载配置                                                        │
│     └── 读取 config/settings.py 和环境变量                          │
│                                                                     │
│  2. 初始化数据库                                                    │
│     ├── 创建数据库连接池                                            │
│     ├── 创建表结构 (如果不存在)                                      │
│     └── 插入默认数据 (管理员账号、默认区域等)                         │
│                                                                     │
│  3. 注册路由                                                        │
│     ├── /api/v1/auth         认证相关                               │
│     ├── /api/v1/cameras      摄像头管理                             │
│     ├── /api/v1/areas        区域管理                               │
│     ├── /api/v1/models       模型管理                               │
│     ├── /api/v1/algorithms   算法管理                               │
│     ├── /api/v1/alarms       告警管理                               │
│     ├── /api/v1/system       系统管理                               │
│     └── /api/v1/media/hook   ZLMediaKit Hook 回调                   │
│                                                                     │
│  4. 启动 WebSocket 服务                                             │
│     └── /ws/detections/{id}  实时检测框推送                         │
│     └── /ws/alarms           实时告警推送                           │
│                                                                     │
│  5. 启动 AlarmWorkerPool (后台线程池)                               │
│     ├── 创建 N 个 Worker 线程 (默认 4 个)                           │
│     └── 每个 Worker 阻塞消费 Redis alarm_queue                      │
│                                                                     │
│  6. 开始监听请求                                                    │
│     └── 等待 HTTP 请求                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 五、视频处理引擎启动流程 (核心)

视频处理引擎是系统核心，采用**多进程 + 多线程**架构：

```
启动命令: python engine/main.py
# 用这个
python -m engine.main

启动流程:
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  阶段 1: 主进程初始化 (Scheduler)                              │ │
│  └───────────────────────────────────────────────────────────────┘ │
│      │                                                             │
│      ├── 1.1 加载全局配置                                          │
│      │       ├── 数据库连接配置                                    │
│      │       ├── Redis 配置 (如果分布式部署)                       │
│      │       ├── 流媒体服务器配置                                  │
│      │       └── 模型文件路径配置                                  │
│      │                                                             │
│      ├── 1.2 从数据库读取运行时配置                                │
│      │       ├── 所有启用的摄像头列表                              │
│      │       ├── 每个摄像头配置的算法列表                          │
│      │       ├── 每个算法关联的模型信息                            │
│      │       └── 每个模型的性能参数 (显存、推理时间)                │
│      │                                                             │
│      ├── 1.3 计算 Worker 数量                                      │
│      │       ├── 统计每个模型被多少摄像头使用                       │
│      │       ├── 根据摄像头数、帧率、跳帧计算 fps 需求             │
│      │       ├── 根据模型推理时间计算单 Worker 能力                │
│      │       └── 计算每个模型需要的 Worker 数 (向上取整 +20%余量)  │
│      │                                                             │
│      └── 1.4 创建所有队列                                          │
│              ├── 为每个模型创建一个请求队列                         │
│              │   例: yolo_safety_queue, fire_queue                 │
│              └── 为每个摄像头创建一个结果队列                       │
│                  例: result_queue_cam_001, result_queue_cam_002    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  阶段 2: 启动 InferenceService 进程                            │ │
│  └───────────────────────────────────────────────────────────────┘ │
│      │                                                             │
│      ├── 2.1 创建 InferenceService 子进程                          │
│      │       └── 传入: 模型配置列表、各模型队列、Worker 数量       │
│      │                                                             │
│      └── 2.2 InferenceService 内部启动                             │
│              │                                                     │
│              ├── 遍历每个模型配置                                  │
│              │   └── 启动 N 个 InferenceWorker 线程               │
│              │       每个 Worker:                                  │
│              │       ├── 通过 `common.storage.get_storage()` 从统一存储中下载模型文件到本地临时目录 │
│              │       ├── 加载自己的模型实例                        │
│              │       ├── 绑定到对应模型的请求队列                  │
│              │       └── 进入循环: 取帧 → 推理 → 分发结果，并每 ~10 秒输出一次存活/性能日志 │
│              │                                                     │
│              └── 所有 Worker 就绪后，打印日志:                     │
│                  "InferenceService 启动完成: YOLO 3 Workers, Fire 2 Workers"
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  阶段 3: 启动 Pipeline 进程池                                  │ │
│  └───────────────────────────────────────────────────────────────┘ │
│      │                                                             │
│      ├── 3.1 遍历每个启用的摄像头                                  │
│      │       └── 为每个摄像头创建一个 Pipeline 子进程              │
│      │           传入: 摄像头配置、关联的队列引用                  │
│      │                                                             │
│      └── 3.2 每个 Pipeline 内部启动                                │
│              │                                                     │
│              ├── 启动 Thread 1: StreamReader (拉流线程)            │
│              │   ├── 连接 RTSP 流                                  │
│              │   ├── 循环读取帧                                    │
│              │   ├── 帧 → 推流队列 (给 StreamWriter)               │
│              │   └── 帧 → 模型请求队列 (按跳帧策略)                │
│              │                                                     │
│              ├── 启动 Thread 2: StreamWriter (推流线程)            │
│              │   ├── 从推流队列取帧                                │
│              │   └── 编码推送到流媒体服务器                        │
│              │                                                     │
│              └── 启动 Thread 3: ResultHandler (结果处理线程)       │
│                  ├── 从结果队列取推理结果                          │
│                  ├── 去重过滤                                      │
│                  ├── 生成告警 (写库、WebSocket)                    │
│                  └── 触发消息推送                                  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  阶段 4: 健康监控循环                                          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│      │                                                             │
│      └── 主进程进入监控循环                                        │
│          ├── 定期检查各子进程状态                                  │
│          ├── 检查队列积压情况                                      │
│          ├── 子进程异常退出时自动重启                              │
│          ├── 响应配置变更 (新增/删除摄像头)                        │
│          └── 优雅关闭: 收到 SIGTERM 时依次停止各子进程             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 六、进程/线程关系图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         视频处理引擎进程结构                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Main Process (主进程/调度器)                                              │
│   │                                                                         │
│   ├── 职责: 配置加载、进程管理、健康监控                                     │
│   │                                                                         │
│   ├── InferenceService Process (推理服务进程，1个)                          │
│   │   │                                                                     │
│   │   ├── 职责: 管理所有推理 Worker                                        │
│   │   │                                                                     │
│   │   ├── YOLO 模型组                                                      │
│   │   │   ├── Worker-1 (线程) ← 独立模型实例                               │
│   │   │   ├── Worker-2 (线程) ← 独立模型实例                               │
│   │   │   └── Worker-N (线程) ← 独立模型实例                               │
│   │   │                                                                     │
│   │   ├── Fire 模型组                                                      │
│   │   │   ├── Worker-1 (线程) ← 独立模型实例                               │
│   │   │   └── Worker-N (线程) ← 独立模型实例                               │
│   │   │                                                                     │
│   │   └── ... 其他模型组                                                   │
│   │                                                                         │
│   ├── Pipeline Process - cam_001 (进程)                                    │
│   │   ├── StreamReader  (线程) - 拉流                                      │
│   │   ├── StreamWriter  (线程) - 推流                                      │
│   │   └── ResultHandler (线程) - 结果处理                                  │
│   │                                                                         │
│   ├── Pipeline Process - cam_002 (进程)                                    │
│   │   ├── StreamReader  (线程)                                             │
│   │   ├── StreamWriter  (线程)                                             │
│   │   └── ResultHandler (线程)                                             │
│   │                                                                         │
│   └── Pipeline Process - cam_N (进程)                                      │
│       ├── StreamReader  (线程)                                             │
│       ├── StreamWriter  (线程)                                             │
│       └── ResultHandler (线程)                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

进程总数: 1 (主) + 1 (推理服务) + N (摄像头数)
线程总数: 推理 Worker 数 + N × 3 (每摄像头3个线程)
```

---

## 七、数据流向

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据流向图                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   摄像头 RTSP 流                                                            │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────────┐                                                          │
│   │ StreamReader│  (Pipeline 内，拉流线程)                                  │
│   └─────┬───────┘                                                          │
│         │                                                                   │
│         ├──────────────────────┐                                           │
│         │                      │                                           │
│         ▼                      ▼                                           │
│   ┌───────────┐          ┌───────────────┐                                 │
│   │ 推流队列   │          │ 模型请求队列   │ (每模型一个)                    │
│   │ (本地)    │          │ (跨进程)       │                                │
│   └─────┬─────┘          └───────┬───────┘                                 │
│         │                        │                                          │
│         ▼                        ▼                                          │
│   ┌─────────────┐          ┌───────────────┐                               │
│   │ StreamWriter│          │ InferenceWorker│ (N个并行)                     │
│   │  (推流线程) │          │   (推理线程)   │                               │
│   └─────┬───────┘          └───────┬───────┘                               │
│         │                          │                                        │
│         ▼                          ▼                                        │
│   ┌───────────────┐          ┌───────────────┐                             │
│   │ ZLMediaKit    │          │ 结果队列       │ (每摄像头一个)              │
│   │ (流媒体服务器) │          │ (跨进程)       │                             │
│   └───────┬───────┘          └───────┬───────┘                             │
│           │                          │                                      │
│           ▼                          ▼                                      │
│   ┌───────────────┐          ┌───────────────┐                             │
│   │ 前端 flv.js   │          │ ResultHandler │ (结果处理线程)              │
│   │ (视频播放)    │          │               │                             │
│   └───────────────┘          └───────┬───────┘                             │
│                                      │                                      │
│                                      ├──────────────────┐                   │
│                                      │                  │                   │
│                                      ▼                  ▼                   │
│                              ┌───────────────┐  ┌───────────────┐          │
│                              │ 数据库        │  │ WebSocket     │          │
│                              │ (告警存储)    │  │ (实时推送)    │          │
│                              └───────────────┘  └───────┬───────┘          │
│                                                         │                   │
│                                                         ▼                   │
│                                                  ┌───────────────┐         │
│                                                  │ 前端告警列表   │         │
│                                                  │ + 画框叠加     │         │
│                                                  └───────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 八、关键设计决策

### 7.1 为什么是多进程 + 多线程混合?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  为什么 InferenceService 和 Pipeline 是独立进程?                            │
│                                                                             │
│  ├── Python GIL 限制: 多线程无法利用多核 CPU                                │
│  ├── 进程隔离: 一个 Pipeline 崩溃不影响其他                                 │
│  ├── 资源隔离: 每个进程独立的内存空间                                       │
│  └── 扩展性: 可以分布到不同机器                                             │
│                                                                             │
│  为什么 InferenceService 内部是多线程?                                      │
│                                                                             │
│  ├── GPU 推理不受 GIL 影响 (在 C++ 层执行)                                  │
│  ├── 多线程共享 GPU 显存更高效                                              │
│  └── 避免进程间传递大帧数据的开销                                           │
│                                                                             │
│  为什么 Pipeline 内部是多线程?                                              │
│                                                                             │
│  ├── I/O 密集型操作 (网络拉流/推流) 不受 GIL 影响                           │
│  ├── 三个线程职责独立，互不阻塞                                             │
│  └── 同进程内数据共享更简单                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 为什么每个 Worker 独立加载模型?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  方案对比:                                                                  │
│                                                                             │
│  方案A: 多 Worker 共享一个模型实例                                          │
│  ├── 优点: 显存占用少                                                       │
│  └── 缺点:                                                                  │
│      ├── 深度学习框架的模型推理不保证线程安全                               │
│      ├── 需要加锁，失去并行优势                                             │
│      └── 调试困难                                                           │
│                                                                             │
│  方案B: 每个 Worker 独立加载模型实例 ✓ (采用)                               │
│  ├── 优点:                                                                  │
│  │   ├── 线程安全，无需担心共享问题                                         │
│  │   ├── 真正并行，无锁竞争                                                 │
│  │   ├── 代码简单，易于调试                                                 │
│  │   └── Worker 数已按需计算，显存可控                                      │
│  └── 缺点: 显存占用稍高 (但可控)                                            │
│                                                                             │
│  显存对比 (16路摄像头):                                                     │
│  ├── 方案A: 2 模型 × 1 实例 = ~1GB                                         │
│  ├── 方案B: 2 模型 × 3 Worker = ~2.5GB                                     │
│  └── 可接受: 现代 GPU 显存充足 (RTX 3080 = 10GB)                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 为什么按模型维护队列而非按算法?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  场景: 一个摄像头配置了 人员入侵 + 安全帽检测                               │
│        两个算法都使用 yolo_safety 模型                                      │
│                                                                             │
│  方案A: 按算法维护队列                                                      │
│  ├── person_intrusion_queue ← 帧                                           │
│  ├── helmet_detection_queue ← 同一帧                                       │
│  └── 问题: 同一帧被推理两次，浪费算力                                       │
│                                                                             │
│  方案B: 按模型维护队列 ✓ (采用)                                             │
│  ├── yolo_safety_queue ← 帧 (只发一次)                                     │
│  ├── 推理一次，结果按算法配置过滤分发                                       │
│  └── 优势: 同模型多算法共享推理结果，节省算力                               │
│                                                                             │
│  推理结果分发逻辑:                                                          │
│  ├── 模型返回: [{person, 0.9}, {no_helmet, 0.7}, {helmet, 0.8}]            │
│  ├── 人员入侵算法: 只取 person → [{person, 0.9}]                           │
│  └── 安全帽算法: 只取 no_helmet → [{no_helmet, 0.7}]                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 九、启动顺序依赖

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              启动顺序                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. 外部依赖 (需要先启动)                                                  │
│      ├── MySQL 数据库                                                       │
│      ├── Redis (如果分布式部署)                                             │
│      └── ZLMediaKit 流媒体服务器                                            │
│                                                                             │
│   2. FastAPI 服务 (可独立启动)                                              │
│      └── uvicorn app.main:app --port 8000                                  │
│                                                                             │
│   3. 视频处理引擎 (依赖数据库配置)                                          │
│      └── python engine/main.py                                             │
│          │                                                                  │
│          └── 内部启动顺序:                                                  │
│              ├── 3.1 主调度器初始化                                         │
│              ├── 3.2 读取数据库配置                                         │
│              ├── 3.3 创建队列                                               │
│              ├── 3.4 启动 InferenceService                                 │
│              │       └── 等待所有 Worker 模型加载完成                       │
│              ├── 3.5 启动所有 Pipeline                                     │
│              │       └── 每个 Pipeline 启动三个线程                        │
│              └── 3.6 进入监控循环                                          │
│                                                                             │
│   启动状态检查:                                                             │
│   ├── InferenceService: 所有 Worker 打印 "模型加载完成"                    │
│   ├── Pipeline: 每个摄像头打印 "连接成功" 或 "连接失败"                    │
│   └── 主调度器: 打印 "引擎启动完成: X 路摄像头, Y 个 Worker"               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 十、配置热更新流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           配置热更新 (待实现)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   场景: 用户在前端新增一个摄像头                                            │
│                                                                             │
│   方式1: 重启引擎 (简单，初期采用)                                          │
│   ├── 前端调用 API 写入数据库                                               │
│   ├── 手动重启引擎进程                                                      │
│   └── 引擎重新读取配置，启动新的 Pipeline                                   │
│                                                                             │
│   方式2: 热更新 (复杂，后期优化)                                            │
│   ├── 前端调用 API 写入数据库                                               │
│   ├── API 通知主调度器 (通过信号或消息)                                     │
│   ├── 主调度器动态创建新的 Pipeline 进程                                    │
│   ├── 如果涉及新模型，需要热加载 Worker                                     │
│   └── 更新队列映射关系                                                      │
│                                                                             │
│   建议: 初期采用方式1，系统稳定后再实现热更新                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 十一、异常处理策略

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              异常处理策略                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Pipeline 异常:                                                            │
│   ├── RTSP 连接失败 → 重试 N 次，间隔递增                                   │
│   ├── 解码失败 → 跳过当前帧，继续下一帧                                     │
│   ├── 推流失败 → 重连流媒体服务器                                           │
│   └── 进程崩溃 → 主调度器检测并自动重启                                     │
│                                                                             │
│   InferenceService 异常:                                                    │
│   ├── 模型加载失败 → 记录错误，该模型不启动                                 │
│   ├── 推理异常 → 捕获错误，跳过当前帧                                       │
│   ├── Worker 崩溃 → 自动重启该 Worker                                       │
│   └── 整个进程崩溃 → 主调度器重启 InferenceService                          │
│                                                                             │
│   队列异常:                                                                  │
│   ├── 队列满 → 丢弃最旧帧，保证实时性                                       │
│   ├── 队列空 → Worker 阻塞等待                                              │
│   └── 队列断开 (Redis) → 重连                                               │
│                                                                             │
│   优雅关闭:                                                                  │
│   ├── 收到 SIGTERM/SIGINT                                                  │
│   ├── 通知所有 Pipeline 停止拉流                                            │
│   ├── 等待队列清空                                                          │
│   ├── 停止 InferenceService                                                │
│   └── 主进程退出                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 十二、跨进程通信设计

### 11.1 通信场景分析

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           跨进程通信场景                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   场景1: 推理请求                                                           │
│   Pipeline (拉流线程) ──帧数据──► InferenceService (Worker)                │
│   特点: 高频、大数据量 (图像帧)                                             │
│   方案: multiprocessing.Queue (共享内存，零拷贝)                            │
│                                                                             │
│   场景2: 推理结果返回                                                       │
│   InferenceService (Worker) ──结果──► Pipeline (ResultHandler)             │
│   特点: 高频、数据量小 (检测框坐标)                                         │
│   方案: multiprocessing.Queue                                              │
│                                                                             │
│   场景3: 实时绘框推送                                                       │
│   Pipeline (ResultHandler) ──检测框──► FastAPI ──WebSocket──► 前端         │
│   特点: 实时性要求极高、多前端订阅                                          │
│   方案: Redis Pub/Sub                                                      │
│                                                                             │
│   场景4: 告警存储/消息推送                                                  │
│   Pipeline (ResultHandler) ──告警──► 异步处理服务                          │
│   特点: 可异步、需要持久化                                                  │
│   方案: Redis List 队列 + 消费者线程池                                      │
│                                                                             │
│   场景5: 配置热更新                                                         │
│   FastAPI ──配置变更──► Engine (Scheduler)                                 │
│   特点: 低频、需要可靠送达                                                  │
│   方案: Redis Pub/Sub                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 队列归属设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           队列创建与归属                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   所有队列由主调度器 (Scheduler) 统一创建，然后分发给各子进程                │
│                                                                             │
│   Scheduler (主进程)                                                        │
│   │                                                                         │
│   ├── 创建: yolo_safety_queue (模型请求队列)                               │
│   ├── 创建: fire_queue (模型请求队列)                                      │
│   ├── 创建: result_queue_cam_001 (摄像头结果队列)                          │
│   ├── 创建: result_queue_cam_002 (摄像头结果队列)                          │
│   │                                                                         │
│   ├── 启动 InferenceService，传入:                                         │
│   │   ├── 所有模型请求队列 (Worker 从这里取帧)                             │
│   │   └── 所有结果队列 (Worker 往这里写结果)                               │
│   │                                                                         │
│   └── 启动 Pipeline-cam_001，传入:                                         │
│       ├── 相关模型请求队列 (拉流线程往这里写帧)                            │
│       └── result_queue_cam_001 (ResultHandler 从这里读结果)                │
│                                                                             │
│   数据流向:                                                                 │
│   Pipeline.StreamReader ──写入──► model_queue ──读取──► InferenceWorker   │
│   InferenceWorker ──写入──► result_queue ──读取──► Pipeline.ResultHandler │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.3 ResultHandler 三动作设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ResultHandler 处理流程                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ResultHandler (Pipeline 内的线程)                                         │
│   │                                                                         │
│   │  ┌─────────────────────────────────────────────────────────────┐       │
│   │  │  从 result_queue 取数据                                      │       │
│   │  │  ↓                                                          │       │
│   │  │  数据清洗 (去重过滤)                                         │       │
│   │  │  ↓                                                          │       │
│   │  │  分发三个动作                                                │       │
│   │  └─────────────────────────────────────────────────────────────┘       │
│   │                                                                         │
│   ├──────────────────────────────────────────────────────────────────────  │
│   │                                                                         │
│   │  动作1: WebSocket 实时推送 (绘框)                                       │
│   │  ┌─────────────────────────────────────────────────────────────┐       │
│   │  │  要求: 延迟 < 50ms，多前端同时查看同一路流                   │       │
│   │  │                                                              │       │
│   │  │  方案: Redis Pub/Sub                                         │       │
│   │  │                                                              │       │
│   │  │  ResultHandler:                                              │       │
│   │  │  redis.publish(f"detections:{camera_id}", json_data)        │       │
│   │  │                                                              │       │
│   │  │  FastAPI WebSocket Handler:                                  │       │
│   │  │  async for msg in redis.subscribe(f"detections:{camera_id}"):│       │
│   │  │      await websocket.send(msg)                               │       │
│   │  │                                                              │       │
│   │  │  优势:                                                       │       │
│   │  │  ├── 解耦: Engine 不关心有多少前端连接                       │       │
│   │  │  ├── 多订阅: N 个前端看同一路流，只 publish 一次            │       │
│   │  │  ├── 实时: Redis Pub/Sub 延迟 < 1ms                         │       │
│   │  │  └── 分布式: FastAPI 可以多实例部署                         │       │
│   │  └─────────────────────────────────────────────────────────────┘       │
│   │                                                                         │
│   │  动作2 + 动作3: 告警存储 + 消息推送 (异步)                             │
│   │  ┌─────────────────────────────────────────────────────────────┐       │
│   │  │  要求: 不阻塞主流程，允许 100ms~1s 延迟                     │       │
│   │  │                                                              │       │
│   │  │  方案: Redis List 队列 + 独立消费者                          │       │
│   │  │                                                              │       │
│   │  │  ResultHandler:                                              │       │
│   │  │  redis.rpush("alarm_queue", json_data)  # 非阻塞，立即返回  │       │
│   │  │                                                              │       │
│   │  │  AlarmConsumer (FastAPI 内线程池, N 个 Worker):              │       │
│   │  │  def worker():                                               │       │
│   │  │      while True:                                             │       │
│   │  │          alarm = redis.blpop("alarm_queue")                  │       │
│   │  │          save_to_db(alarm)       # 存储落库                  │       │
│   │  │          send_notification(alarm)# 钉钉/邮件/短信            │       │
│   │  │                                                              │       │
│   │  │  优势:                                                       │       │
│   │  │  ├── 异步: 不阻塞 ResultHandler 主流程                       │       │
│   │  │  ├── 削峰: 高峰期消息堆积，消费者慢慢处理                   │       │
│   │  │  ├── 可靠: Redis List 持久化，进程重启不丢失                │       │
│   │  │  └── 解耦: 存储逻辑独立，易于维护                           │       │
│   │  └─────────────────────────────────────────────────────────────┘       │
│   │                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.4 告警数据结构设计 (关键：不包含原始帧数据)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      告警数据大小分析                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   原始帧数据大小:                                                           │
│   ├── 1080P 帧 (1920×1080×3) = 约 6MB/帧                                   │
│   ├── 25 FPS × 16 路 × 6MB = 2.4 GB/秒 ❌ 绝对不能放入 Redis              │
│   └── 会导致: 内存爆掉、网络堵塞、Redis 崩溃                               │
│                                                                             │
│   正确做法: 只传输元数据 + 截图路径                                         │
│   ├── 元数据 (JSON) ≈ 500 Bytes ~ 2 KB                                     │
│   └── 截图保存到磁盘/对象存储，只传文件路径                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 11.4.1 实时绘框数据 (WebSocket Pub/Sub)

```python
# 推送到 Redis Pub/Sub 的数据结构 (仅用于前端画框叠加)
# 频道: detections:{camera_id}
{
    "camera_id": "abc123...",
    "timestamp": 1739276400.123,       # Unix 时间戳 (毫秒精度)
    "frame_id": 12345,                  # 帧序号 (用于前端对齐视频帧)
    
    "detections": [                     # 检测框列表
        {
            "algorithm_id": "def456...",
            "algorithm_name": "人员入侵",
            "class_name": "person",
            "confidence": 0.92,
            "bbox": [100, 200, 300, 400],    # [x1, y1, x2, y2] 像素坐标
            "is_alert": true                  # 是否触发告警
        },
        {
            "algorithm_id": "ghi789...",
            "algorithm_name": "安全帽检测",
            "class_name": "no_helmet",
            "confidence": 0.88,
            "bbox": [500, 100, 650, 300],
            "is_alert": true
        }
    ]
}

# 数据大小: 约 500 Bytes ~ 2 KB (取决于检测框数量)
# 每秒数据量: 16路 × 25帧 × 1KB = 400 KB/秒 ✓ 完全可接受
```

#### 11.4.2 告警存储数据 (Redis List 异步队列)

```python
# 推送到 Redis List 的数据结构 (用于存库和消息推送)
# 队列: alarm_queue
{
    "alarm_id": "xyz789...",            # 预生成的告警 ID
    "camera_id": "abc123...",
    "camera_name": "东门摄像头",
    "algorithm_id": "def456...",
    "algorithm_name": "人员入侵",
    "alert_level": "high",
    
    "timestamp": 1739276400.123,
    "detection": {
        "class_name": "person",
        "confidence": 0.92,
        "bbox": [100, 200, 300, 400]
    },
    
    # ✅ 关键: 截图保存到磁盘/对象存储，只传路径
    "snapshot_path": "/data/alarms/2026/02/11/abc123_1739276400123.jpg",
    
    # 可选: 视频片段路径 (前后 5 秒)
    "video_clip_path": "/data/alarms/2026/02/11/abc123_1739276400123.mp4"
}

# 数据大小: 约 500 Bytes ~ 1 KB
# 每秒最大告警数: 假设 100 条告警/秒 × 1KB = 100 KB/秒 ✓ 完全可接受
```

#### 11.4.3 截图保存流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ResultHandler 截图保存流程                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   从 result_queue 取到推理结果                                               │
│   │                                                                         │
│   │  result = {                                                             │
│   │      "camera_id": "...",                                                │
│   │      "frame": numpy.ndarray,     # 原始帧数据 (6MB)                    │
│   │      "detections": [...]                                                │
│   │  }                                                                      │
│   │                                                                         │
│   ├── 去重过滤                                                              │
│   │   └── 通过 IoU + 时间窗口判断是否重复告警                               │
│   │                                                                         │
│   ├── 动作1: 实时绘框推送 (不含帧数据)                                     │
│   │   │                                                                     │
│   │   │  detection_msg = {                                                  │
│   │   │      "camera_id": result["camera_id"],                              │
│   │   │      "timestamp": time.time(),                                      │
│   │   │      "detections": result["detections"]  # 只有坐标，无帧数据      │
│   │   │  }                                                                  │
│   │   └── redis.publish(f"detections:{camera_id}", json.dumps(detection_msg))│
│   │                                                                         │
│   ├── 动作2+3: 告警存储 (需要先保存截图)                                   │
│   │   │                                                                     │
│   │   │  # Step1: 在帧上绘制检测框                                          │
│   │   │  annotated_frame = draw_boxes(result["frame"], result["detections"])│
│   │   │                                                                     │
│   │   │  # Step2: 保存截图到磁盘 (异步 I/O 或线程池)                        │
│   │   │  snapshot_path = storage.save_image(annotated_frame)                │
│   │   │                                                                     │
│   │   │  # Step3: 构造告警消息 (只含路径)                                   │
│   │   │  alarm_msg = {                                                      │
│   │   │      "alarm_id": generate_uuid(),                                   │
│   │   │      "camera_id": result["camera_id"],                              │
│   │   │      "detections": result["detections"],                            │
│   │   │      "snapshot_path": snapshot_path    # ✓ 只有路径，不是图片数据  │
│   │   │  }                                                                  │
│   │   └── redis.rpush("alarm_queue", json.dumps(alarm_msg))                │
│   │                                                                         │
│   └── 原始 frame 数据在本次处理完成后丢弃，不进入任何队列                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 11.4.4 存储方案选择

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      截图/视频存储方案                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   方案A: 本地磁盘 (推荐初期使用)                                            │
│   ├── 路径: /data/alarms/{year}/{month}/{day}/{camera_id}_{timestamp}.jpg  │
│   ├── 优点: 简单、无依赖、读写快                                            │
│   ├── 缺点: 单机容量有限、备份复杂                                          │
│   └── 适用: 中小规模部署                                                    │
│                                                                             │
│   方案B: MinIO 对象存储 (推荐生产使用)                                      │
│   ├── 兼容 S3 API                                                           │
│   ├── 优点: 分布式、高可用、易扩展                                          │
│   ├── 缺点: 需要额外部署                                                    │
│   └── 适用: 大规模生产环境                                                  │
│                                                                             │
│   方案C: 云对象存储 (阿里云 OSS / 腾讯云 COS)                               │
│   ├── 优点: 无需运维、按需付费、CDN 加速                                    │
│   └── 适用: 云上部署、多地域访问                                            │
│                                                                             │
│   设计策略: 抽象存储接口，支持动态切换                                       │
│   │                                                                         │
│   │  class StorageInterface:                                                │
│   │      def save_image(self, image: np.ndarray, path: str) -> str          │
│   │      def save_video(self, frames: List, path: str) -> str               │
│   │      def get_url(self, path: str) -> str                                │
│   │                                                                         │
│   │  # 实现类                                                               │
│   │  class LocalStorage(StorageInterface): ...                              │
│   │  class MinIOStorage(StorageInterface): ...                              │
│   │  class OSSStorage(StorageInterface): ...                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 11.4.5 内存和带宽估算

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      资源占用估算 (16 路摄像头)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Redis 内存占用:                                                           │
│                                                                             │
│   实时绘框 (Pub/Sub):                                                       │
│   ├── 消息大小: 1 KB                                                        │
│   ├── 消息保留: 0 (Pub/Sub 不存储，发完即弃)                               │
│   └── Redis 内存: ≈ 0                                                       │
│                                                                             │
│   告警队列 (List):                                                          │
│   ├── 消息大小: 1 KB                                                        │
│   ├── 最大堆积: 假设 10000 条未处理 (极端情况)                             │
│   └── Redis 内存: 10000 × 1 KB = 10 MB                                      │
│                                                                             │
│   Redis 总内存: < 50 MB ✓ 完全可控                                          │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────────│
│                                                                             │
│   磁盘存储:                                                                 │
│                                                                             │
│   告警截图 (JPEG):                                                          │
│   ├── 单张大小: 100 KB (1080P JPEG 压缩后)                                 │
│   ├── 告警频率: 假设每路每分钟 1 次告警                                    │
│   ├── 每日存储: 16路 × 60分钟 × 24小时 × 100KB = 2.3 GB/天                 │
│   └── 每月存储: 约 70 GB (需要定期清理或归档)                              │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────────│
│                                                                             │
│   网络带宽:                                                                 │
│                                                                             │
│   Redis Pub/Sub 推送:                                                       │
│   ├── 16 路 × 25 帧/秒 × 1 KB = 400 KB/秒 = 3.2 Mbps                       │
│   └── 完全可接受 ✓                                                          │
│                                                                             │
│   告警队列写入:                                                             │
│   ├── 假设 100 条/秒 × 1 KB = 100 KB/秒 = 0.8 Mbps                         │
│   └── 完全可接受 ✓                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.5 AlarmConsumer 线程池设计 (内置于 FastAPI)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AlarmConsumer 线程池架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   FastAPI 启动时                                                            │
│   │                                                                         │
│   │  @app.on_event("startup")                                               │
│   │  async def startup():                                                   │
│   │      # 启动告警消费线程池                                               │
│   │      alarm_worker_pool.start(num_workers=4)                            │
│   │                                                                         │
│   │  @app.on_event("shutdown")                                              │
│   │  async def shutdown():                                                  │
│   │      # 优雅停止                                                         │
│   │      alarm_worker_pool.stop()                                          │
│   │                                                                         │
│   线程池结构:                                                               │
│   │                                                                         │
│   │  ┌─────────────────────────────────────────────────────────────┐       │
│   │  │                   WorkerPool                                 │       │
│   │  │                                                             │       │
│   │  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │       │
│   │  │   │ Worker-1 │ │ Worker-2 │ │ Worker-3 │ │ Worker-4 │      │       │
│   │  │   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │       │
│   │  │        │            │            │            │             │       │
│   │  │        └────────────┴─────┬──────┴────────────┘             │       │
│   │  │                           │                                 │       │
│   │  │                           ▼                                 │       │
│   │  │               redis.blpop("alarm_queue")                    │       │
│   │  │               (阻塞等待，竞争消费)                          │       │
│   │  │                                                             │       │
│   │  └─────────────────────────────────────────────────────────────┘       │
│   │                                                                         │
│   优势:                                                                     │
│   ├── 无需单独进程: 减少部署复杂度                                          │
│   ├── 共享连接池: 复用 FastAPI 的数据库连接                                 │
│   ├── 弹性伸缩: 可动态调整 Worker 数量                                      │
│   └── 优雅停止: FastAPI 关闭时等待任务完成                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```python
# app/consumer/worker_pool.py

import threading
import redis
import json
from typing import Callable, List
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings
from common.logging.logger import logger

class AlarmWorkerPool:
    """告警消费线程池"""
    
    def __init__(self):
        self.workers: List[threading.Thread] = []
        self.running = False
        self.redis_client = None
        
    def start(self, num_workers: int = 4):
        """启动 Worker 线程池"""
        self.running = True
        self.redis_client = redis.from_url(settings.REDIS_URL)
        
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"AlarmWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            
        logger.info(f"AlarmWorkerPool started with {num_workers} workers")
        
    def stop(self, timeout: float = 5.0):
        """停止线程池 (优雅退出)"""
        self.running = False
        
        # 发送退出信号 (向队列推入 None)
        for _ in self.workers:
            self.redis_client.rpush("alarm_queue", json.dumps({"__stop__": True}))
        
        # 等待所有 Worker 退出
        for worker in self.workers:
            worker.join(timeout=timeout)
            
        logger.info("AlarmWorkerPool stopped")
        
    def _worker_loop(self):
        """Worker 主循环"""
        from app.consumer.alarm_consumer import process_alarm
        
        while self.running:
            try:
                # 阻塞等待消息，超时 1 秒 (允许检查 running 状态)
                result = self.redis_client.blpop("alarm_queue", timeout=1)
                
                if result is None:
                    continue  # 超时，继续循环
                    
                _, data = result
                alarm_data = json.loads(data)
                
                # 检查退出信号
                if alarm_data.get("__stop__"):
                    break
                    
                # 处理告警
                process_alarm(alarm_data)
                
            except Exception as e:
                logger.error(f"AlarmWorker error: {e}")


# 单例
alarm_worker_pool = AlarmWorkerPool()
```

```python
# app/consumer/alarm_consumer.py

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.alarm import Alarm
from common.notification.dingtalk import send_dingtalk
from common.notification.email_sender import send_email
from common.redis.client import redis_client
from common.logging.logger import logger


def process_alarm(alarm_data: dict):
    """
    处理单条告警
    
    1. 存储到数据库
    2. 发送通知 (钉钉/邮件/短信)
    3. 推送实时告警事件给前端
    """
    try:
        # 1. 存储到数据库
        save_alarm_to_db(alarm_data)
        
        # 2. 发送通知 (根据告警级别)
        if alarm_data.get("alert_level") in ["high", "critical"]:
            send_notifications(alarm_data)
        
        # 3. 推送实时告警给前端 (刷新告警列表)
        redis_client.publish("alarms:realtime", json.dumps({
            "type": "new_alarm",
            "alarm_id": alarm_data.get("alarm_id"),
            "camera_id": alarm_data.get("camera_id"),
            "alert_level": alarm_data.get("alert_level")
        }))
        
    except Exception as e:
        logger.error(f"Process alarm failed: {e}, data: {alarm_data}")


def save_alarm_to_db(alarm_data: dict):
    """存储告警到数据库"""
    db: Session = SessionLocal()
    try:
        alarm = Alarm(
            id=alarm_data.get("alarm_id"),
            camera_id=alarm_data.get("camera_id"),
            algorithm_id=alarm_data.get("algorithm_id"),
            alarm_type=alarm_data.get("alarm_type", "detection"),
            level=alarm_data.get("alert_level", "medium"),
            snapshot_url=alarm_data.get("snapshot_path"),
            detection_data=alarm_data.get("detection"),
            status="unconfirmed"
        )
        db.add(alarm)
        db.commit()
    finally:
        db.close()


def send_notifications(alarm_data: dict):
    """发送告警通知"""
    # 钉钉
    send_dingtalk(
        title=f"【{alarm_data.get('alert_level')}】{alarm_data.get('algorithm_name')}",
        content=f"摄像头: {alarm_data.get('camera_name')}\n时间: {alarm_data.get('timestamp')}"
    )
    
    # 邮件 (可选)
    # send_email(...)
```

```python
# app/main.py (启动时初始化)

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.consumer.worker_pool import alarm_worker_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    alarm_worker_pool.start(num_workers=4)
    yield
    # 关闭时
    alarm_worker_pool.stop()

app = FastAPI(lifespan=lifespan)
```

---

## 十三、配置热更新设计

### 12.1 热更新通信方式选择

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        热更新通信方式对比                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   方案A: 进程间信号 (Signal)                                                │
│   ├── 优点: 无依赖，轻量                                                    │
│   ├── 缺点:                                                                 │
│   │   ├── 需要知道目标进程 PID                                              │
│   │   ├── 只能传递信号类型，无法携带数据                                    │
│   │   └── 不支持分布式部署                                                  │
│   └── 不推荐                                                                │
│                                                                             │
│   方案B: Redis Pub/Sub ✓ (推荐)                                             │
│   ├── 优点:                                                                 │
│   │   ├── 解耦: 发布者不关心订阅者是谁                                      │
│   │   ├── 可携带数据: 可以传递完整的配置变更信息                            │
│   │   ├── 分布式: 支持多机部署                                              │
│   │   ├── 已有依赖: 系统已用 Redis 做实时推送                               │
│   │   └── 可靠: 支持重连                                                    │
│   ├── 缺点:                                                                 │
│   │   └── 依赖 Redis (但已经有了)                                           │
│   └── 推荐                                                                  │
│                                                                             │
│   方案C: 数据库轮询                                                         │
│   ├── 优点: 简单，无额外依赖                                                │
│   ├── 缺点:                                                                 │
│   │   ├── 延迟高 (轮询间隔)                                                 │
│   │   └── 浪费数据库资源                                                    │
│   └── 不推荐                                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 热更新流程设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           热更新流程                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Redis Channel: "engine:config_update"                                     │
│                                                                             │
│   消息格式:                                                                 │
│   {                                                                         │
│       "action": "camera_add" | "camera_remove" | "camera_update"           │
│                 | "algorithm_update" | "model_update",                     │
│       "data": { ... 具体配置 ... }                                         │
│   }                                                                         │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                             │
│   场景: 新增摄像头                                                          │
│                                                                             │
│   1. 用户在前端添加摄像头                                                   │
│      │                                                                      │
│      ▼                                                                      │
│   2. FastAPI 接收请求                                                       │
│      ├── 写入数据库                                                         │
│      └── 发布 Redis 消息:                                                   │
│          redis.publish("engine:config_update", {                           │
│              "action": "camera_add",                                        │
│              "data": {                                                      │
│                  "camera_id": "cam_005",                                   │
│                  "rtsp_url": "rtsp://...",                                 │
│                  "algorithms": [...]                                        │
│              }                                                              │
│          })                                                                 │
│      │                                                                      │
│      ▼                                                                      │
│   3. Engine Scheduler 收到消息                                              │
│      ├── 解析配置变更                                                       │
│      ├── 判断是否需要新模型 (如果是，先启动新 Worker)                       │
│      ├── 创建新的 result_queue_cam_005                                     │
│      ├── 启动新的 Pipeline 进程                                            │
│      └── 更新内部状态                                                       │
│      │                                                                      │
│      ▼                                                                      │
│   4. 返回成功                                                               │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                             │
│   场景: 删除摄像头                                                          │
│                                                                             │
│   1. FastAPI 发布消息: {"action": "camera_remove", "data": {"camera_id": "cam_003"}}
│      │                                                                      │
│      ▼                                                                      │
│   2. Engine Scheduler 收到消息                                              │
│      ├── 找到 cam_003 的 Pipeline 进程                                     │
│      ├── 发送停止信号                                                       │
│      ├── 等待 Pipeline 优雅退出                                            │
│      ├── 回收 result_queue_cam_003                                         │
│      └── 重新计算 Worker 数量 (如果某模型不再被使用，可以减少 Worker)       │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                             │
│   场景: 修改摄像头算法配置                                                  │
│                                                                             │
│   1. FastAPI 发布消息:                                                      │
│      {"action": "camera_update", "data": {"camera_id": "cam_001", "algorithms": [...]}}
│      │                                                                      │
│      ▼                                                                      │
│   2. Engine Scheduler 收到消息                                              │
│      ├── 方案A: 重启该 Pipeline (简单)                                     │
│      └── 方案B: 通知 Pipeline 热更新配置 (复杂，需要内部消息机制)           │
│                                                                             │
│      建议初期用方案A，单个 Pipeline 重启影响小                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 十四、整体通信架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   整体通信架构                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│   │                              FastAPI 服务                                        │  │
│   │                                                                                 │  │
│   │   HTTP API ◄────────────────────────────────────────────────────► 前端          │  │
│   │                                                                                 │  │
│   │   WebSocket Handler                                                             │  │
│   │   ├── 订阅 Redis: "detections:cam_001"  ──────► ws.send() ────► 前端 A         │  │
│   │   ├── 订阅 Redis: "detections:cam_001"  ──────► ws.send() ────► 前端 B         │  │
│   │   └── 订阅 Redis: "detections:cam_002"  ──────► ws.send() ────► 前端 C         │  │
│   │                                                                                 │  │
│   │   AlarmWorkerPool (后台线程池):                                                 │  │
│   │   ├── Worker-1 ─┬─► redis.blpop("alarm_queue") ─► save_to_db + notify         │  │
│   │   ├── Worker-2 ─┤                                                              │  │
│   │   ├── Worker-3 ─┤                                                              │  │
│   │   └── Worker-N ─┘                                                              │  │
│   │                                                                                 │  │
│   │   配置变更时:                                                                   │  │
│   │   redis.publish("engine:config_update", {...})  ──────────────────────┐        │  │
│   │                                                                        │        │  │
│   └────────────────────────────────────────────────────────────────────────┼────────┘  │
│                                                                            │            │
│                                                                            │            │
│                              ┌─────────────────────────────────────────────┘            │
│                              │                                                          │
│                              ▼                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│   │                            Redis (消息中枢)                                      │  │
│   │                                                                                 │  │
│   │   Pub/Sub Channels:                                                             │  │
│   │   ├── "detections:cam_001"      # 实时检测框 (Engine → FastAPI → 前端)         │  │
│   │   ├── "detections:cam_002"                                                     │  │
│   │   ├── "alarms:realtime"         # 实时告警 (Engine → FastAPI → 前端)           │  │
│   │   └── "engine:config_update"    # 配置更新 (FastAPI → Engine)                  │  │
│   │                                                                                 │  │
│   │   List Queues:                                                                  │  │
│   │   ├── "alarm_queue"             # 告警队列 (Engine → AlarmConsumer)            │  │
│   │   └── "notification_queue"      # 消息推送队列                                  │  │
│   │                                                                                 │  │
│   └─────────────────────────────────────────────────────────────────────────────────┘  │
│                    │                              ▲                                     │
│                    │                              │                                     │
│                    ▼                              │                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│   │                          视频处理引擎 (Engine)                                   │  │
│   │                                                                                 │  │
│   │   Scheduler (主进程)                                                            │  │
│   │   ├── 订阅 Redis: "engine:config_update"  ◄─────────────────────────────────┘  │  │
│   │   │   └── 收到配置变更时，动态管理 Pipeline                                     │  │
│   │   │                                                                             │  │
│   │   ├── multiprocessing.Queue (内存队列，跨进程)                                  │  │
│   │   │   ├── yolo_safety_queue                                                    │  │
│   │   │   ├── fire_queue                                                           │  │
│   │   │   ├── result_queue_cam_001                                                 │  │
│   │   │   └── result_queue_cam_002                                                 │  │
│   │   │                                                                             │  │
│   │   ├── InferenceService (子进程)                                                │  │
│   │   │   └── Workers 从 model_queue 取帧，结果写入 result_queue                   │  │
│   │   │                                                                             │  │
│   │   └── Pipeline-cam_001 (子进程)                                                │  │
│   │       ├── StreamReader: 帧 → model_queue                                       │  │
│   │       ├── StreamWriter: 推流到 ZLMediaKit                                      │  │
│   │       └── ResultHandler:                                                        │  │
│   │           ├── 从 result_queue 读取                                             │  │
│   │           ├── 去重过滤                                                          │  │
│   │           ├── redis.publish("detections:cam_001", ...)  # 实时绘框             │  │
│   │           └── redis.rpush("alarm_queue", ...)           # 异步告警             │  │
│   │                                                                                 │  │
│   └─────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                         │
│   注: AlarmConsumer 已内置于 FastAPI 服务中，作为后台线程池运行                       │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 十五、技术选型总结

| 通信场景 | 技术选型 | 理由 |
|----------|----------|------|
| 帧传输 (Pipeline→Worker) | `multiprocessing.Queue` | 共享内存，零拷贝，高性能 |
| 结果返回 (Worker→Pipeline) | `multiprocessing.Queue` | 同上 |
| 实时绘框 (Engine→FastAPI→前端) | `Redis Pub/Sub` | 解耦，多订阅者，低延迟 |
| 配置热更新 (FastAPI→Engine) | `Redis Pub/Sub` | 解耦，可携带数据，分布式 |
| 告警异步处理 | `Redis List` + 线程池 | 持久化，削峰，共享DB连接 |
| 告警存储/通知 | FastAPI 内置线程池 | 复用连接池，简化部署 |

---

## 十六、更新后的进程结构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          完整进程结构                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   独立启动的服务:                                                           │
│                                                                             │
│   1. FastAPI 服务                                                           │
│      └── uvicorn app.main:app --port 8000                                  │
│          ├── HTTP API 处理                                                  │
│          ├── WebSocket 连接管理                                             │
│          │   └── 订阅 Redis 并转发给前端                                    │
│          ├── 配置变更时发布 Redis 消息                                      │
│          └── AlarmConsumer 线程池 (内置)                                   │
│              ├── N 个 Worker 线程从 Redis 消费                             │
│              ├── 写入数据库                                                 │
│              └── 发送通知 (钉钉/邮件/短信)                                  │
│                                                                             │
│   2. 视频处理引擎                                                           │
│      └── python engine/main.py                                             │
│          ├── Scheduler (主进程)                                            │
│          │   ├── 订阅 Redis 配置更新                                        │
│          │   └── 管理子进程                                                 │
│          ├── InferenceService (子进程)                                     │
│          │   └── N 个 Worker 线程                                          │
│          └── Pipeline × M (子进程)                                         │
│              └── 3 个线程/每进程                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 十七、ZLMediaKit 流媒体对接设计

### 16.1 ZLMediaKit 简介

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ZLMediaKit 核心功能                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ZLMediaKit 是高性能流媒体服务器，支持:                                    │
│   ├── 协议: RTSP/RTMP/HTTP-FLV/HLS/WebRTC/GB28181                          │
│   ├── 转码: 可无转码转发，降低 CPU 开销                                     │
│   ├── 鉴权: Hook 回调机制，支持播放/推流权限控制                           │
│   ├── API:  RESTful API，支持流管理、状态查询                              │
│   └── 性能: 单机可支持数千路流                                              │
│                                                                             │
│   默认端口:                                                                 │
│   ├── HTTP API: 80                                                          │
│   ├── RTSP:     554                                                         │
│   ├── RTMP:     1935                                                        │
│   └── HTTP-FLV: 80 (与 API 同端口)                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.2 流媒体对接架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      流媒体对接流程                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                               摄像头                                         │
│                                  │                                          │
│                                  │ RTSP 拉流                                │
│                                  ▼                                          │
│   ┌───────────────────────────────────────────────────────────────┐        │
│   │                      Pipeline (StreamReader)                   │        │
│   │                                                               │        │
│   │   1. 从摄像头拉取 RTSP 流                                      │        │
│   │   2. 解码帧送入推理队列                                        │        │
│   │   3. 绘制检测框 (可选)                                         │        │
│   │   4. 编码推流到 ZLMediaKit                                     │        │
│   │                                                               │        │
│   └───────────────────────────────────────────────────────────────┘        │
│                                  │                                          │
│                                  │ RTMP 推流                                │
│                                  ▼                                          │
│   ┌───────────────────────────────────────────────────────────────┐        │
│   │                        ZLMediaKit                              │        │
│   │                                                               │        │
│   │   ├── 接收来自 Pipeline 的推流                                 │        │
│   │   ├── 自动转码/转封装为多种格式                                │        │
│   │   ├── 播放鉴权 (Hook 回调到 FastAPI)                           │        │
│   │   └── 分发给多个前端观看者                                     │        │
│   │                                                               │        │
│   │   流地址:                                                      │        │
│   │   ├── RTSP:     rtsp://host:554/live/camera_{id}              │        │
│   │   ├── RTMP:     rtmp://host:1935/live/camera_{id}             │        │
│   │   ├── HTTP-FLV: http://host/live/camera_{id}.live.flv         │        │
│   │   └── HLS:      http://host/live/camera_{id}/hls.m3u8         │        │
│   │                                                               │        │
│   └───────────────────────────────────────────────────────────────┘        │
│                                  │                                          │
│                                  │ HTTP-FLV                                 │
│                                  ▼                                          │
│   ┌───────────────────────────────────────────────────────────────┐        │
│   │                         前端 (flv.js)                          │        │
│   │                                                               │        │
│   │   1. 携带 Token 请求播放                                       │        │
│   │   2. ZLMediaKit 回调 FastAPI 验证 Token                        │        │
│   │   3. 验证通过后播放视频流                                      │        │
│   │   4. 同时接收 WebSocket 检测框数据，叠加显示                   │        │
│   │                                                               │        │
│   └───────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.3 Pipeline 启动时申请推流地址

```python
# engine/pipeline/pipeline.py

class Pipeline:
    def __init__(self, camera_id: str, camera_config: dict):
        self.camera_id = camera_id
        self.stream_key = f"camera_{camera_id}"  # 流标识
        self.push_url = None  # 推流地址，启动时申请
        
    async def start(self):
        """启动 Pipeline"""
        # Step 1: 向 ZLMediaKit 申请推流地址
        self.push_url = await self._request_push_url()
        
        # Step 2: 启动各线程
        self.stream_reader = StreamReader(self.camera_config["rtsp_url"])
        self.stream_writer = StreamWriter(self.push_url)
        self.result_handler = ResultHandler(self.camera_id)
        
        # ...
        
    async def _request_push_url(self) -> str:
        """向 ZLMediaKit 申请推流地址"""
        # 方案 A: 使用固定规则的地址 (推荐，简单)
        # 推流地址固定为: rtmp://zlm_host:1935/live/{stream_key}
        push_url = f"rtmp://{ZLM_HOST}:{ZLM_RTMP_PORT}/live/{self.stream_key}"
        return push_url
        
        # 方案 B: 动态申请 (复杂场景)
        # response = await zlm_client.add_stream_proxy(...)
        # return response["data"]["key"]
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      推流地址规则                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   固定规则 (推荐):                                                          │
│   │                                                                         │
│   │  推流地址: rtmp://{zlm_host}:1935/live/camera_{camera_id}              │
│   │  播放地址:                                                              │
│   │  ├── HTTP-FLV: http://{zlm_host}/live/camera_{camera_id}.live.flv     │
│   │  ├── RTSP:     rtsp://{zlm_host}:554/live/camera_{camera_id}          │
│   │  └── HLS:      http://{zlm_host}/live/camera_{camera_id}/hls.m3u8     │
│   │                                                                         │
│   优势:                                                                     │
│   ├── 无需动态申请，减少 API 调用                                           │
│   ├── 地址可预测，前端可直接拼接                                            │
│   └── ZLMediaKit 自动创建流，无需提前注册                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.4 ZLMediaKit Hook 鉴权回调

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ZLMediaKit Hook 机制                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ZLMediaKit 配置 (config.ini):                                             │
│   │                                                                         │
│   │  [hook]                                                                 │
│   │  enable=1                                                               │
│   │  on_play=http://fastapi_host:8000/api/v1/media/hook/on_play            │
│   │  on_publish=http://fastapi_host:8000/api/v1/media/hook/on_publish      │
│   │  on_stream_changed=http://fastapi_host:8000/api/v1/media/hook/on_stream│
│   │  on_stream_not_found=http://fastapi_host:8000/api/v1/media/hook/not_found│
│   │                                                                         │
│   Hook 触发时机:                                                            │
│   ├── on_play:      有人请求播放流时触发 (鉴权关键!)                       │
│   ├── on_publish:   有人推流时触发                                          │
│   ├── on_stream_changed: 流上线/下线时触发                                  │
│   └── on_stream_not_found: 请求的流不存在时触发                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```python
# app/api/endpoints/media_hooks.py

from fastapi import APIRouter, Request, HTTPException
from app.core.security import decode_access_token

router = APIRouter(prefix="/media/hook", tags=["媒体Hook"])


@router.post("/on_play")
async def on_play_hook(request: Request):
    """
    播放鉴权回调
    
    ZLMediaKit 在有人请求播放时调用此接口
    前端请求: http://zlm/live/camera_xxx.live.flv?token=xxx
    """
    data = await request.json()
    
    # 从请求参数中获取 Token
    params = data.get("params", "")  # "token=xxx&other=yyy"
    token = _extract_token(params)
    
    if not token:
        # 返回非 0 code 拒绝播放
        return {"code": -1, "msg": "缺少认证Token"}
    
    # 验证 Token
    payload = decode_access_token(token)
    if not payload:
        return {"code": -1, "msg": "Token无效或已过期"}
    
    # 可选: 检查用户是否有权限观看该摄像头
    user_id = payload.get("sub")
    stream_id = data.get("stream")  # camera_xxx
    # if not await check_camera_permission(user_id, stream_id):
    #     return {"code": -1, "msg": "无权限观看此摄像头"}
    
    # 返回 code=0 允许播放
    return {"code": 0, "msg": "success"}


@router.post("/on_publish")
async def on_publish_hook(request: Request):
    """
    推流鉴权回调
    
    只允许内部 Pipeline 推流，拒绝外部推流
    """
    data = await request.json()
    
    # 验证推流来源 IP
    ip = data.get("ip", "")
    
    # 只允许内网 IP 推流 (Pipeline 所在服务器)
    allowed_ips = ["127.0.0.1", "192.168.1.100"]  # 配置化
    if ip not in allowed_ips:
        return {"code": -1, "msg": "非法推流来源"}
    
    return {"code": 0, "msg": "success"}


@router.post("/on_stream")
async def on_stream_changed_hook(request: Request):
    """
    流状态变化回调
    
    用于记录流上线/下线状态
    """
    data = await request.json()
    
    regist = data.get("regist", False)  # True=上线, False=下线
    stream = data.get("stream", "")
    
    if regist:
        logger.info(f"流上线: {stream}")
        # 可选: 更新数据库中摄像头在线状态
    else:
        logger.info(f"流下线: {stream}")
        
    return {"code": 0, "msg": "success"}


@router.post("/not_found")
async def on_stream_not_found_hook(request: Request):
    """
    流不存在回调
    
    可用于自动拉流: 当请求的流不存在时，自动启动对应 Pipeline
    """
    data = await request.json()
    stream = data.get("stream", "")  # camera_xxx
    
    # 提取 camera_id
    if stream.startswith("camera_"):
        camera_id = stream.replace("camera_", "")
        # 可选: 通知 Engine 启动该摄像头的 Pipeline
        # await redis.publish("engine:start_camera", camera_id)
    
    return {"code": 0, "msg": "success"}


def _extract_token(params: str) -> str:
    """从 URL 参数中提取 token"""
    # params = "token=xxx&foo=bar"
    for param in params.split("&"):
        if param.startswith("token="):
            return param.split("=", 1)[1]
    return ""
```

### 16.5 前端播放流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      前端播放流程 (带鉴权)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. 前端获取播放地址 (API 返回)                                            │
│      GET /api/v1/cameras/{id}/stream                                        │
│      Response: {                                                            │
│          "flv_url": "http://zlm/live/camera_xxx.live.flv",                 │
│          "rtsp_url": "rtsp://zlm:554/live/camera_xxx",                     │
│          "hls_url": "http://zlm/live/camera_xxx/hls.m3u8"                  │
│      }                                                                      │
│                                                                             │
│   2. 前端播放时携带 Token                                                   │
│      const token = localStorage.getItem("access_token")                     │
│      const url = `${flv_url}?token=${token}`                               │
│                                                                             │
│   3. ZLMediaKit 收到请求，回调 FastAPI 验证 Token                           │
│                                                                             │
│   4. 验证通过，开始播放                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```typescript
// frontend/src/utils/player.ts

import flvjs from "flv.js";

export function createPlayer(videoElement: HTMLVideoElement, cameraId: string) {
    const token = localStorage.getItem("access_token");
    const baseUrl = import.meta.env.VITE_MEDIA_SERVER_URL;
    
    // 拼接带 Token 的播放地址
    const flvUrl = `${baseUrl}/live/camera_${cameraId}.live.flv?token=${token}`;
    
    if (flvjs.isSupported()) {
        const player = flvjs.createPlayer({
            type: "flv",
            url: flvUrl,
            isLive: true,
            hasAudio: false,
            cors: true
        });
        
        player.attachMediaElement(videoElement);
        player.load();
        player.play();
        
        return player;
    }
}
```

### 16.6 ZLMediaKit 客户端封装

```python
# common/media/zlm_client.py

import httpx
from typing import Optional, Dict, Any
from config.settings import settings

class ZLMediaKitClient:
    """ZLMediaKit API 客户端"""
    
    def __init__(self):
        self.base_url = settings.ZLM_API_URL  # http://localhost:80
        self.secret = settings.ZLM_SECRET     # API 密钥
        
    async def _request(self, api: str, params: dict = None) -> dict:
        """发送 API 请求"""
        params = params or {}
        params["secret"] = self.secret
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/index/api/{api}",
                params=params,
                timeout=10
            )
            return response.json()
    
    async def get_media_list(self) -> list:
        """获取所有在线流列表"""
        result = await self._request("getMediaList")
        return result.get("data", [])
    
    async def get_media_info(self, stream: str, app: str = "live") -> Optional[dict]:
        """获取指定流信息"""
        result = await self._request("getMediaInfo", {
            "app": app,
            "stream": stream,
            "schema": "rtmp"
        })
        if result.get("code") == 0:
            return result.get("data")
        return None
    
    async def close_stream(self, stream: str, app: str = "live") -> bool:
        """关闭指定流"""
        result = await self._request("close_streams", {
            "app": app,
            "stream": stream,
            "force": 1
        })
        return result.get("code") == 0
    
    async def add_stream_proxy(
        self, 
        stream: str, 
        rtsp_url: str,
        app: str = "live"
    ) -> Optional[str]:
        """
        添加拉流代理
        让 ZLMediaKit 主动拉取 RTSP 流 (可选方案)
        """
        result = await self._request("addStreamProxy", {
            "app": app,
            "stream": stream,
            "url": rtsp_url,
            "vhost": "__defaultVhost__",
            "enable_hls": 0,
            "enable_mp4": 0
        })
        if result.get("code") == 0:
            return result.get("data", {}).get("key")
        return None
    
    async def get_server_config(self) -> dict:
        """获取服务器配置"""
        result = await self._request("getServerConfig")
        return result.get("data", [])


# 单例
zlm_client = ZLMediaKitClient()
```

---

## 十八、Token 认证机制设计

### 17.1 整体认证架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      认证架构                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Token 类型:                                                               │
│   ├── Access Token:  短期有效 (默认 24h)，用于 API 请求                    │
│   └── Refresh Token: 长期有效 (7-30天)，用于刷新 Access Token              │
│                                                                             │
│   存储位置:                                                                 │
│   ├── 前端: localStorage (Access Token) + httpOnly Cookie (Refresh Token)  │
│   └── 后端: Redis 黑名单 (已登出的 Token)                                  │
│                                                                             │
│   认证流程:                                                                 │
│   ├── 登录:        账号密码 → Access Token + Refresh Token                │
│   ├── 请求:        Header: Authorization: Bearer {access_token}            │
│   ├── 刷新:        Refresh Token → 新 Access Token                         │
│   └── 登出:        Token 加入黑名单                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.2 Token 生成与验证

```python
# app/core/security.py

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建 Access Token"""
    to_encode = data.copy()
    
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """创建 Refresh Token (7天有效)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """解码并验证 Token"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token 已过期
    except jwt.InvalidTokenError:
        return None  # Token 无效


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)
```

### 17.3 登录/刷新/登出 API

```python
# app/api/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.core.database import get_db
from app.core.security import (
    create_access_token, 
    create_refresh_token,
    decode_access_token,
    verify_password
)
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    返回 Access Token (body) 和 Refresh Token (httpOnly cookie)
    """
    # 验证用户
    user = await AuthService.authenticate(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 生成 Token
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Refresh Token 设置为 httpOnly Cookie (更安全)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,       # 生产环境开启 HTTPS
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7天
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新 Access Token
    
    使用 Cookie 中的 Refresh Token 获取新的 Access Token
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="缺少 Refresh Token")
    
    # 验证 Refresh Token
    payload = decode_access_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的 Refresh Token")
    
    # 检查是否在黑名单中
    if await AuthService.is_token_blacklisted(refresh_token):
        raise HTTPException(status_code=401, detail="Token 已失效")
    
    # 生成新的 Access Token
    user_id = payload.get("sub")
    access_token = create_access_token(data={"sub": user_id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    用户登出
    
    将 Token 加入黑名单
    """
    # Access Token 加入黑名单
    if credentials:
        await AuthService.blacklist_token(credentials.credentials)
    
    # Refresh Token 加入黑名单
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await AuthService.blacklist_token(refresh_token)
    
    # 清除 Cookie
    response.delete_cookie("refresh_token")
    
    return {"message": "登出成功"}
```

### 17.4 Token 黑名单服务

```python
# app/services/auth_service.py

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import verify_password, decode_access_token
from common.redis.client import redis_client

class AuthService:
    """认证服务"""
    
    # Token 黑名单 Redis Key 前缀
    BLACKLIST_PREFIX = "token:blacklist:"
    
    @staticmethod
    async def authenticate(
        db: AsyncSession, 
        username: str, 
        password: str
    ) -> Optional[User]:
        """验证用户名密码"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        if not user.is_active:
            return None
            
        return user
    
    @staticmethod
    async def blacklist_token(token: str) -> None:
        """将 Token 加入黑名单"""
        payload = decode_access_token(token)
        if not payload:
            return
        
        # 计算 Token 剩余有效期
        exp = payload.get("exp", 0)
        now = int(time.time())
        ttl = max(exp - now, 0)
        
        if ttl > 0:
            # 在 Redis 中存储，TTL 为 Token 剩余有效期
            key = f"{AuthService.BLACKLIST_PREFIX}{token[:32]}"  # 只用前32字符作为 key
            await redis_client.setex(key, ttl, "1")
    
    @staticmethod
    async def is_token_blacklisted(token: str) -> bool:
        """检查 Token 是否在黑名单中"""
        key = f"{AuthService.BLACKLIST_PREFIX}{token[:32]}"
        return await redis_client.exists(key)
```

### 17.5 前端 Token 处理

```typescript
// frontend/src/utils/request.ts

import axios from "axios";
import { useUserStore } from "@/stores/user";
import router from "@/router";

const request = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 10000,
    withCredentials: true  // 携带 Cookie (Refresh Token)
});

// 请求拦截器 - 添加 Token
request.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("access_token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// 响应拦截器 - 处理 401
request.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        // 401 且未重试过 → 尝试刷新 Token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            
            try {
                // 调用刷新接口
                const { data } = await axios.post(
                    `${import.meta.env.VITE_API_BASE_URL}/auth/refresh`,
                    {},
                    { withCredentials: true }
                );
                
                // 保存新 Token
                localStorage.setItem("access_token", data.access_token);
                
                // 重试原请求
                originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
                return request(originalRequest);
                
            } catch (refreshError) {
                // 刷新失败 → 跳转登录页
                localStorage.removeItem("access_token");
                const userStore = useUserStore();
                userStore.logout();
                router.push("/login");
                return Promise.reject(refreshError);
            }
        }
        
        return Promise.reject(error);
    }
);

export default request;
```

```typescript
// frontend/src/stores/user.ts

import { defineStore } from "pinia";
import request from "@/utils/request";

export const useUserStore = defineStore("user", {
    state: () => ({
        token: localStorage.getItem("access_token") || "",
        user: null as any
    }),
    
    getters: {
        isLoggedIn: (state) => !!state.token
    },
    
    actions: {
        async login(username: string, password: string) {
            const { data } = await request.post("/auth/login", {
                username,
                password
            });
            
            this.token = data.access_token;
            this.user = data.user;
            localStorage.setItem("access_token", data.access_token);
        },
        
        async logout() {
            try {
                await request.post("/auth/logout");
            } finally {
                this.token = "";
                this.user = null;
                localStorage.removeItem("access_token");
            }
        },
        
        async fetchUserInfo() {
            const { data } = await request.get("/auth/me");
            this.user = data;
        }
    }
});
```

### 17.6 WebSocket Token 认证

```python
# app/websocket/handlers.py

from fastapi import WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_access_token
from app.services.auth_service import AuthService

async def authenticate_websocket(
    websocket: WebSocket,
    token: str = Query(None)
) -> Optional[str]:
    """
    WebSocket 连接认证
    
    前端连接: ws://host/ws/detections?token=xxx
    """
    if not token:
        await websocket.close(code=4001, reason="缺少认证Token")
        return None
    
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Token无效或已过期")
        return None
    
    if await AuthService.is_token_blacklisted(token):
        await websocket.close(code=4001, reason="Token已失效")
        return None
    
    return payload.get("sub")  # 返回 user_id


@router.websocket("/ws/detections/{camera_id}")
async def websocket_detections(
    websocket: WebSocket,
    camera_id: str,
    token: str = Query(None)
):
    """
    实时检测框 WebSocket
    
    连接后订阅 Redis，将检测数据转发给前端
    """
    user_id = await authenticate_websocket(websocket, token)
    if not user_id:
        return
    
    await websocket.accept()
    
    try:
        # 订阅 Redis 频道
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"detections:{camera_id}")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
                
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"detections:{camera_id}")
```

```typescript
// frontend/src/utils/websocket.ts

export function createDetectionSocket(cameraId: string) {
    const token = localStorage.getItem("access_token");
    const wsUrl = import.meta.env.VITE_WS_URL;
    
    const socket = new WebSocket(
        `${wsUrl}/ws/detections/${cameraId}?token=${token}`
    );
    
    socket.onmessage = (event) => {
        const detections = JSON.parse(event.data);
        // 处理检测数据，绘制框
        drawDetections(detections);
    };
    
    socket.onclose = (event) => {
        if (event.code === 4001) {
            // Token 问题，刷新后重连
            refreshTokenAndReconnect(cameraId);
        }
    };
    
    return socket;
}
```

### 17.7 认证流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      完整认证流程                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   登录流程:                                                                 │
│   ┌────────┐  POST /auth/login   ┌────────┐                                │
│   │  前端  │ ─────────────────► │ FastAPI │                                │
│   │        │  {user, password}  │         │                                │
│   │        │                     │         │                                │
│   │        │ ◄───────────────── │         │                                │
│   │        │  Access Token (body)│        │                                │
│   │        │  Refresh Token (cookie)      │                                │
│   └────────┘                     └────────┘                                │
│       │                                                                     │
│       │ localStorage.setItem("access_token", token)                        │
│       ▼                                                                     │
│                                                                             │
│   API 请求:                                                                 │
│   ┌────────┐  GET /api/xxx        ┌────────┐                               │
│   │  前端  │ ─────────────────► │ FastAPI │                                │
│   │        │  Authorization:     │         │                                │
│   │        │  Bearer {token}     │         │                                │
│   │        │ ◄───────────────── │         │                                │
│   │        │  200 / 401          │         │                                │
│   └────────┘                     └────────┘                                │
│       │                                                                     │
│       │ 401 时自动刷新 Token                                                │
│       ▼                                                                     │
│                                                                             │
│   Token 刷新:                                                               │
│   ┌────────┐  POST /auth/refresh ┌────────┐                                │
│   │  前端  │ ─────────────────► │ FastAPI │                                │
│   │        │  Cookie: refresh_token       │                                │
│   │        │ ◄───────────────── │         │                                │
│   │        │  新 Access Token   │         │                                │
│   └────────┘                     └────────┘                                │
│                                                                             │
│   视频播放鉴权:                                                             │
│   ┌────────┐ flv?token=xxx ┌────────────┐ Hook ┌────────┐                 │
│   │  前端  │ ────────────► │ ZLMediaKit │ ───► │ FastAPI │                 │
│   │        │               │            │ ◄─── │  验证   │                 │
│   │        │ ◄──────────── │   (播放)   │ 0/-1 │         │                 │
│   └────────┘    视频流     └────────────┘      └────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 十九、待确认问题 (已更新)

1. ~~FastAPI 与 Engine 是否同一启动脚本?~~ → **分别启动** ✓

2. ~~WebSocket 推送由谁负责?~~ → **Engine 发 Redis Pub/Sub，FastAPI 订阅后转发** ✓

3. ~~告警存储同步还是异步?~~ → **异步，通过 Redis List 队列** ✓

4. ~~是否需要热更新?~~ → **需要，通过 Redis Pub/Sub** ✓

5. ~~ZLMediaKit 鉴权机制?~~ → **Hook 回调到 FastAPI 验证 Token** ✓

6. ~~前端 Token 处理?~~ → **Access Token + Refresh Token 双 Token 机制** ✓

7. ~~AlarmConsumer 归属?~~ → **内置于 FastAPI，作为后台线程池运行** ✓
   - 属于业务逻辑层（存库、消息推送）
   - FastAPI 启动时自动启动 N 个 Worker 线程
   - 共享数据库连接池，无需额外进程管理

---

## 二十、配置项汇总

```python
# config/settings.py

class Settings(BaseSettings):
    """全局配置"""
    
    # ======== 基础配置 ========
    PROJECT_NAME: str = "AI Vision Platform"
    ENVIRONMENT: str = "development"  # development / production
    DEBUG: bool = True
    
    # ======== API 配置 ========
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # ======== 数据库配置 ========
    DATABASE_URL: str = "mysql+aiomysql://root:root@localhost:3306/ai_vision"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # ======== Redis 配置 ========
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    
    # ======== JWT 认证配置 ========
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7          # 7 天
    
    # ======== ZLMediaKit 配置 ========
    ZLM_API_URL: str = "http://localhost:80"     # API 地址
    ZLM_SECRET: str = "035c73f7-bb6b-4889-a715"  # API 密钥
    ZLM_RTMP_PORT: int = 1935
    ZLM_RTSP_PORT: int = 554
    ZLM_HTTP_FLV_PORT: int = 80
    ZLM_HOOK_ENABLE: bool = True
    ZLM_ALLOWED_PUSH_IPS: List[str] = ["127.0.0.1"]  # 允许推流的 IP
    
    # ======== 推理引擎配置 ========
    ENGINE_REDIS_CHANNEL: str = "engine:config_update"
    DEFAULT_INFERENCE_WORKERS: int = 4
    MAX_FRAME_QUEUE_SIZE: int = 30
    MAX_RESULT_QUEUE_SIZE: int = 100
    
    # ======== 存储配置 ========
    STORAGE_TYPE: str = "local"  # local / minio / oss
    LOCAL_STORAGE_PATH: str = "./data"
    
    # MinIO (可选)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "ai-vision"
    
    # ======== 日志配置 ========
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = "./logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

---

## 二十一、技术栈总结

| 分类 | 技术选型 | 用途 |
|------|----------|------|
| **Web框架** | FastAPI | HTTP API、WebSocket |
| **数据库** | MySQL 8.0 | 业务数据存储 |
| **ORM** | SQLAlchemy 2.0 | 异步数据库操作 |
| **缓存/消息** | Redis | Pub/Sub、队列、Token黑名单 |
| **流媒体** | ZLMediaKit | RTSP/RTMP/HTTP-FLV 转发 |
| **推理框架** | YOLO (Ultralytics) | 目标检测、分类 |
| **视频处理** | OpenCV | 拉流、解码、绘框 |
| **前端框架** | Vue 3 + TypeScript | SPA 应用 |
| **UI组件** | Naive UI | 后台管理界面 |
| **视频播放** | flv.js | HTTP-FLV 播放 |
| **进程通信** | multiprocessing.Queue | 高性能帧传输 |
| **认证** | JWT (PyJWT) | 无状态认证 |
| **容器化** | Docker + Docker Compose | 部署编排 |

---

**请确认以上设计是否符合预期。**
