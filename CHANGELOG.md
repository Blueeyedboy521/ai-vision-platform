## Changelog

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

