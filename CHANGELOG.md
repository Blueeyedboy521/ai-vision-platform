## Changelog

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

