## Changelog

### v2.8.1 - 2026-03-03

- **告警清洗与异步转发链路**：`ResultHandler` 对推理结果做阈值/区域/变化检测（3 秒窗口 + IoU 变化）后生成告警，先落本地临时截图，再由 `Scheduler` 内部告警线程上传到 Storage（MinIO）并写入 Redis `alarm_queue`，由 app 侧 `AlarmConsumer` 入库并推送 WS/通知。
- **摄像头在线状态（基于快照）**：`live_heartbeat_monitor` 定期遍历所有摄像头尝试更新快照，成功则设置 `camera:online:{camera_id}`（TTL=100s），失败则删除；摄像头列表/详情与系统看板从 Redis 实时读取在线状态。
- **前端实时数据对齐**：告警管理/首页告警列表/设备健康等改为调用后端真实接口（`/system/dashboard`、`/alarms`、`/alarms/stats`），并修复告警管理页“视频直播”取流逻辑，复用摄像头管理页的开播/取 `http-flv`/拼 token/开发代理与心跳保活方案。

### v2.8.0 - 2026-03-02

- **Engine 单进程多线程重构**：原本基于多进程的 Scheduler + InferenceService + Pipeline 架构，重构为单独的 Engine 进程内部通过线程并发的模型，`InferenceService` 与 `PipelineService` 作为高内聚服务类，由 `Scheduler` 只负责根据摄像头/模型状态做调度调用，避免跨进程 `multiprocessing.Queue` 句柄失效与重启带来的问题。
- **PipelineService 状态机与幂等化**：引入 `PipelineService` 统一管理每路摄像头的 `Pipeline` 实例，内部实现 S0/S1/S2/S3 状态机和 `reconcile_camera` 幂等逻辑，`Scheduler` 仅传入 `has_algorithms/is_live/is_infer` 三个维度，由服务内部决定是否创建、切换或销毁 Pipeline 及其内部 `StreamReader/StreamWriter/ResultHandler` 线程。
- **InferenceService Worker 自动扩缩容**：`InferenceService` 新增 `on_camera_inference_start/stop` 接口，自行维护「摄像头→模型」映射并根据使用同一模型的摄像头数量动态扩缩 Worker 数量（含回收不再被使用模型的 Worker），实现按需拉起/收紧推理线程，避免所有模型常驻占用 GPU/CPU。
- **Engine 重启状态恢复**：Engine 冷启动时从 Redis 恢复摄像头/模型/算法快照以及 `live_started` / `inference_started` 状态，`Scheduler` 会在启动 `InferenceService` 后为已在推理中的摄像头补发一次绑定事件，确保相关模型 Worker 自动恢复，无需前端重新点击“启动推理”。

### v2.7.0 - 2026-03-02

- **FFmpeg 拉流/推流延迟调优**：`StreamReader` 的 FFmpeg 命令增加 `-fflags nobuffer`、`-flags low_delay`、`-flags2 fast`、`-analyzeduration 0`、`-probesize 32` 等参数，尽量压低从摄像头到后端的内部缓冲；`StreamReader` 不再按 fps 主动 `sleep`，而是尽快把最新帧写入队列，由 FFmpeg 本身和 `StreamWriter` 控制节流，避免多层 `sleep` 造成画面滞后。
- **调试直推模式（StreamReader 直连 FFmpeg）**：新增调试开关 `ENGINE_DEBUG_READER_OPENCV_PUSH`（含义更新为 FFmpeg 直推），开启后 Pipeline 会关闭推理与 `StreamWriter`，由 `StreamReader` 直接用 FFmpeg 从 RTSP 拉流并推到 RTMP，用于快速定位端到端延迟来源，避免在调试阶段被绘框/告警/多级队列干扰判断。
- **Engine 队列与 Redis 封装**：在 Engine 侧新增 `engine/redis.py`，统一封装模型/算法/摄像头配置读取、直播/推理状态集合 (`cameras:live:started` / `cameras:inference:started`) 与心跳检测等逻辑，Scheduler 不再直接操作 `redis.sync_client`；`MemoryQueue` 继续基于 `multiprocessing.Queue` 实现，并增加详细调试日志（队列 id、pid、qsize、item_type），用于排查跨进程队列读写问题。
- **推理服务生命周期调整**：`Scheduler` 仅在首次需要推理时启动 `InferenceService` 进程，后续不再因「当前暂时无推理任务」而主动停止该进程，避免在 Windows spawn 模式下频繁重启进程导致的 `multiprocessing.Queue` 管道/句柄问题；推理资源控制改由「是否还有推理请求」与 Worker 空转来实现。

### v2.6.0 - 2026-02-28

- **后端实时绘框与轻量推理器**：在 Engine Pipeline 中引入 `OverlayState` 作为同一进程内 `ResultHandler` 与 `StreamWriter` 间的共享检测结果缓存，`StreamWriter` 每帧从中读取最新 `frame_id` + `detections` 构造 `InferenceResult` 并调用各模型实现的 `draw_boxes` 完成实时绘框；新增配置开关 `ENGINE_STREAM_DRAW_BOXES` / `ENGINE_STREAM_DRAW_TTL_SEC` 控制是否开启后端绘框以及检测结果过期时间，支持仅后端绘框不影响告警保存与推送链路。
- **Pipeline 状态机与单进程多模式切换**：`Scheduler` 采用摄像头状态机（Idle / Live-only / Inference-only / Full）管理 Pipeline，确保同一摄像头始终只有一个 Pipeline 进程；通过 `pipeline_control_queue` 将 `set_mode` 命令发送到已运行的 Pipeline 子进程，由其内部动态启停 `StreamWriter` / `ResultHandler` 线程并切换模式，避免频繁重启子进程导致的开销与状态错乱。
- **ONNX 类别映射与算法聚合配置**：将 ONNX 推理实现的类别读取逻辑改为从 `model:config:{model_id}` 的 `algorithms` 字段构建 `target_class -> {code, name}` 映射，推理结果中 `class_name` 使用英文 `code` 参与绘框、`algo_name` 保留中文名称供告警使用；`write_model_to_redis` 负责写入包含算法列表的模型快照，避免在推理侧扫描所有 `algorithm:config:*` 带来的性能问题。
- **Redis 操作集中封装**：新增 `app/core/redis.py` 统一封装模型、算法与摄像头相关的 Redis 读写，包括 `write_model_to_redis`、`write_algorithm_to_redis`、`delete_algorithm_from_redis`、摄像头配置缓存、推理/直播状态集合与心跳 Key 更新等；`algorithms.py`、`models.py`、`cameras.py` 中不再直接调用 `redis.client`，而是通过这些封装方法间接访问 Redis，降低耦合度便于后续调整 Key 结构或序列化细节。

### v2.5.0 - 2026-02-28

- **推理层接口化与实现拆分**：Engine 推理抽象为统一接口 `Inferencer`（`inferencer.py`），包含 `load()`、`infer(params)`、`draw_boxes(result)`、`close()`；YOLO 与 ONNX 分别实现于 `inferencer_yolo.py`、`inferencer_onnx.py`；`build_inferencer(model_type, ...)` 工厂按类型创建实现类，Worker 只负责调用 `load()` 与 `infer(params)` 并入队。
- **推理结果与入参统一**：`infer(params)` 接收含 `frame/request_id/camera_id/frame_id` 的字典，实现类内部计时并返回完整 `InferenceResult`（含 `detections`、`inference_time_ms` 等）；Worker 不再二次组装结果；`InferenceResult` 增加可选字段 `frame` 仅用于 `draw_boxes`。
- **实现类自管加载与 classes**：各实现类在 `load()` 内完成模型下载（含存储路径→本地）、从 Redis `model:config:{model_id}` 读取 `classes` 初始化类别名；Worker 不再传 `class_names`，Service 不再向 Worker 传递 `classes`。
- **绘框接口与测试保存**：接口定义 `draw_boxes(result: InferenceResult)`，由各实现类在 `result.frame` 上绘制 `result.detections`；配置项 `TEST_SAVE_DRAW`、`TEST_SAVE_DRAW_DIR`（.env + config.settings）控制是否在 Worker 中调用 `draw_boxes` 并保存绘框图到本地用于验证。
- **认证与用户缓存**：登录成功后用户信息写入 Redis（`user:cache:{user_id}`），TTL 与 access token 一致；`get_current_user` 优先使用请求内 `request.state.current_user`，再查 Redis，未命中再查 DB 并回写缓存；同请求内多次依赖只解析一次；修改密码后清除对应用户缓存。
- **接口冗余与查询优化**：去除增删改接口中不必要的 `db.refresh`（areas/algorithms/models/cameras）；`get_cameras` 不再 `selectinload(Camera.area)`，列表仅返回 `area_id`，`area_name` 由前端从区域树解析；算法创建后不再 refresh，摄像头-算法配置更新后使用直接属性写 Redis 避免懒加载。
- **配置与示例**：`.env.example` 与 `config.settings` 新增 `TEST_SAVE_DRAW`、`TEST_SAVE_DRAW_DIR`；Scheduler 模型配置增加 `classes` 写入 Redis 供 Engine 使用，`input_size` 统一为 (h,w)。

### v2.4.0 - 2026-02-26

- **摄像头实时预览（HTTP-FLV）**：前端新增 `FlvPlayer` 组件，使用 flv.js 在页面内播放 HTTP-FLV 流，摄像头管理页与配置页均支持点击“播放”在弹窗中预览实时画面，避免浏览器直接下载 FLV 文件。
- **跨域与开发代理优化**：在 ZLMediaKit 保持安全配置的前提下，通过 Vite `/flv` 代理将 `http://127.0.0.1:8080` 映射为同源路径，解决前端开发环境下 HTTP-FLV 的 CORS 限制。
- **摄像头算法配置统一管理**：后端新增摄像头-算法配置更新接口（支持置信度、启用状态与检测区域 `regions`），前端将“已配置算法”合并进“算法能力与阈值配置”模块，支持在同一列表中添加/删除算法、调节置信度、启用开关与时间计划。
- **检测区域绘制持久化**：DrawRegionModal 支持绘制多边形检测区域，保存后写入 `camera_algorithms.regions` 字段并同步到 Redis 与 Engine；重新打开摄像头配置页时会从后端加载并在画布上还原已配置区域。
- **直播心跳与状态监控基础**：补充摄像头直播心跳服务与相关管道日志，Engine 可结合 `/cameras/{id}/live-heartbeat` 与 Redis Key 实现对推流会话的超时回收与在线状态更新，为后续完善摄像头状态管理打基础。
- **Pipeline 三模式与推理开关**：Engine 支持 `live_only` / `inference_only` / `full` 三种 Pipeline 模式，依据「点播状态 + 启用算法 + 推理开关」自动切换；FastAPI 新增 `/cameras/{id}/start-inference` / `stop-inference` 接口，前端在列表/卡片中可单独控制后台推理启停。
- **推流状态与心跳联动**：`StreamWriter` 周期性将正在推流的摄像头写入 `cameras:live:started`，并为该集合设置适当 TTL，配合 `/cameras/{id}/start` 即时写入的首帧心跳，使 `live_heartbeat_monitor` 能依据集合与心跳 Key 精准判断无人观看时自动触发停止推流。
- **摄像头管理 UI 增强**：摄像头管理页支持区域树默认选中根节点且在新增/编辑后保持展开与选中状态；列表/卡片视图统一展示「推理中 / 未启动推理」状态徽标并提供显式的启停按钮；HTTP-FLV 播放失败时前端会以 5 秒间隔自动重试最多 30 秒，失败后给出友好提示。
 - **模型存储与推理日志增强**：`StorageInterface` 新增通用 `upload_file` / `download_file` 能力并在 `MinIOStorage` 中实现，`InferenceWorker` 启动时会通过统一存储将模型文件下载到本地临时目录后再加载，并在推理循环中每 ~10 秒输出一次包含 `model_id`、`camera_id`、`frame_id` 与平均耗时的存活日志，便于排查模型与性能问题。

### v2.3.0 - 2026-02-25

- **应用启动与 Redis 缓存**：新增 `bootstrap_sync`，FastAPI 启动时将 DB 中模型、算法、摄像头及摄像头-算法绑定全量写入 Redis，并为每路摄像头在 `stream_manager` 中注册流，Engine 冷启动即可从 Redis 读到完整配置；摄像头增/改/删时同步写/删 `camera:config:{id}`，保证与 DB 一致。
- **点播鉴权**：前端获取播放地址后在 URL 上拼接当前用户 JWT（`?token=...`），ZLMediaKit 通过 Hook `on_play` 回调后端校验 token，鉴权逻辑与 WebHook 地址已写入架构文档。
- **Engine 跨进程队列**：请求中不再携带 `result_queue`，避免 “Queue objects should only be shared through inheritance”；InferenceService 启动时传入 `result_queues` 映射，Worker 按 `camera_id` 回写结果队列；Worker 兼容 dict 请求。
- **推流实现**：StreamWriter 改为使用 FFmpeg 子进程从 stdin 接收 rawvideo(BGR24) 推 RTMP，替代 OpenCV VideoWriter，解决部分环境 RTMP 推流失败问题。
- **拉流/推流帧率**：StreamReader、StreamWriter 均按墙钟时间节流（`next_read_time` / `next_send_time`），严格按配置 fps 间隔取帧/发帧，避免画面过快。

### v2.2.0 - 2026-02-11

- 摄像头连通性与表单联动：前端“流通性测试”调用 `/cameras/probe-stream`，自动回填宽高、帧率/分辨率并随摄像头保存到数据库。
- 摄像头抓拍与 MinIO 存储：后端抓拍使用第 50 帧避免黑屏，统一通过 `StorageInterface` 将快照保存到本地或 MinIO，`last_snapshot_path` 存储 key，前端通过预签名 URL 预览。
- 摄像头预览图统一展示快照：摄像头列表与编辑页默认显示最近一次抓拍图，无图时使用默认占位图。
- 实时预览与心跳保活：新增摄像头“播放/停止”按钮，点击调用 `/cameras/{id}/start`/`/stop` 与 `/cameras/{id}/play-url`，同时每 60 秒向 `/cameras/{id}/live-heartbeat` 上报心跳，后续可驱动 Engine 精细控制 Pipeline 与推流。

### v2.1.0 - 2026-02-11

- 模型与算法能力联动：模型上架时按检测类别自动生成算法列表，算法增删改后自动回写模型检测类别字段。
- 引擎配置解耦：FastAPI 负责将摄像头、模型、算法及绑定配置写入 Redis，Engine 仅通过 Redis 快照+事件拉取配置并热更新。
- 存储抽象与 MinIO 支持：封装统一 `StorageInterface`，新增 MinIO S3 实现，所有文件访问通过 `get_storage()` 选择 local/minio。
- 文件管理与临时存储：新增 `/files` API 与临时目录 `tmp/`，模型文件上传先存临时，模型上架/修改时自动迁移至 `models/{model_id}/...` 并删除临时文件。
- 模型管理前端增强：模型上架/编辑支持上传单个模型附件、显示存储 key、从后端加载/保存算法配置，所有接口统一使用 `{code, message, data}` 响应结构。
- 引擎与告警修复：Alarm 线程池改用同步 Redis 客户端避免协程错误，Engine Scheduler 从 Redis 加载真实摄像头/模型/算法配置代替示例硬编码。

### v2.0.1 - 2026-02-11

- 新的提交：本次版本发布包含最近一次代码更新。

