# AI 视觉平台 - 开发计划

## 版本规划概览

| 版本 | 阶段 | 主要目标 | 预计里程碑 |
|------|------|----------|------------|
| v1.1.0 | 已完成 | 后端架构重构 | ✅ 已发布 |
| v1.2.0 | Phase 1 | 基础设施搭建 (MySQL + Redis) | 待开发 |
| v1.3.0 | Phase 2 | 用户认证模块 | 待开发 |
| v1.4.0 | Phase 3 | 区域与摄像头管理 | 待开发 |
| v1.5.0 | Phase 4 | 模型与算法管理 | 待开发 |
| v1.6.0 | Phase 5 | 告警管理与统计 | 待开发 |
| v1.7.0 | Phase 6 | 系统管理与推送配置 | 待开发 |
| v1.8.0 | Phase 7 | WebSocket 实时推送 | 待开发 |
| v1.9.0 | Phase 8 | 视频处理引擎 (Engine) | 待开发 |
| v2.0.0 | Phase 9 | 集成测试与优化 | 待开发 |

---

## Phase 1: 基础设施搭建 (v1.2.0)

### 目标
搭建 MySQL 和 Redis 基础环境，确保后端服务能正常启动并连接数据库。

### 后端任务

#### 1.1 Docker 环境配置
- [ ] 创建 `docker-compose.yml`
  - MySQL 8.0 容器配置
  - Redis 7.0 容器配置
  - 网络配置
- [ ] 创建 `.env` 配置文件模板
- [ ] 编写数据库初始化脚本

#### 1.2 数据库连接验证
- [ ] 验证 MySQL 异步连接 (aiomysql)
- [ ] 验证 MySQL 同步连接 (pymysql)
- [ ] 验证 Redis 异步连接
- [ ] 验证 Redis 同步连接
- [ ] 自动创建数据库表结构

#### 1.3 初始化数据
- [ ] 创建默认管理员账号 (admin/admin123)
- [ ] 创建默认区域 (根区域)
- [ ] 验证数据插入成功

### 前端任务
- [ ] 配置 API 基础请求封装 (`src/api/request.ts`)
- [ ] 配置环境变量 (`.env.development`, `.env.production`)
- [ ] 添加请求/响应拦截器

### 联调测试
- [ ] 启动 Docker 容器 (MySQL + Redis)
- [ ] 启动后端服务 `uvicorn app.main:app`
- [ ] 验证 `/api/v1/system/health` 健康检查接口
- [ ] 验证数据库连接状态
- [ ] 验证 Redis 连接状态

### 交付物
- `docker-compose.yml`
- `.env.example` 完善
- `frontend/src/api/request.ts`
- 健康检查通过截图

---

## Phase 2: 用户认证模块 (v1.3.0)

### 目标
实现完整的用户登录、登出、Token 刷新功能，前后端联调通过。

### 后端任务

#### 2.1 认证 API 完善
- [ ] `POST /api/v1/auth/login` - 用户登录
  - 验证用户名密码
  - 生成 Access Token + Refresh Token
  - 返回用户信息
- [ ] `POST /api/v1/auth/refresh` - 刷新 Token
  - 验证 Refresh Token
  - 检查 Redis 黑名单
  - 生成新的 Token 对
- [ ] `POST /api/v1/auth/logout` - 用户登出
  - 将 Token 加入 Redis 黑名单
- [ ] `GET /api/v1/auth/me` - 获取当前用户信息
- [ ] `PUT /api/v1/auth/change-password` - 修改密码

#### 2.2 Token 黑名单
- [ ] 实现 Redis Token 黑名单存储
- [ ] Token 过期自动清理

### 前端任务

#### 2.3 登录页面
- [ ] 完善 `Login.vue` 页面
  - 表单验证
  - 调用登录 API
  - 存储 Token 到 localStorage
  - 登录成功跳转

#### 2.4 路由守卫
- [ ] 配置路由前置守卫
  - 检查 Token 有效性
  - 未登录跳转登录页
- [ ] 配置 Axios 拦截器
  - 请求添加 Authorization 头
  - 401 响应自动刷新 Token
  - 刷新失败跳转登录页

#### 2.5 用户状态管理
- [ ] 创建 `stores/user.ts` (Pinia)
  - 用户信息存储
  - 登录/登出方法
  - Token 管理

### 联调测试
- [ ] 测试登录流程 (正确/错误密码)
- [ ] 测试 Token 过期自动刷新
- [ ] 测试登出后 Token 失效
- [ ] 测试路由守卫拦截

### 交付物
- 登录功能完整可用
- Token 自动刷新机制
- 路由权限控制

---

## Phase 3: 区域与摄像头管理 (v1.4.0)

### 目标
实现区域树形管理和摄像头 CRUD 功能。

### 后端任务

#### 3.1 区域管理 API
- [ ] `GET /api/v1/areas` - 获取区域列表
- [ ] `GET /api/v1/areas/tree` - 获取区域树
- [ ] `POST /api/v1/areas` - 创建区域
- [ ] `PUT /api/v1/areas/{id}` - 更新区域
- [ ] `DELETE /api/v1/areas/{id}` - 删除区域 (校验子区域/摄像头)

#### 3.2 摄像头管理 API
- [ ] `GET /api/v1/cameras` - 获取摄像头列表 (分页、筛选)
- [ ] `GET /api/v1/cameras/{id}` - 获取摄像头详情
- [ ] `POST /api/v1/cameras` - 创建摄像头
- [ ] `PUT /api/v1/cameras/{id}` - 更新摄像头
- [ ] `DELETE /api/v1/cameras/{id}` - 删除摄像头
- [ ] `POST /api/v1/cameras/{id}/start` - 启动摄像头
- [ ] `POST /api/v1/cameras/{id}/stop` - 停止摄像头

### 前端任务

#### 3.3 摄像头管理页面
- [ ] 完善 `CameraManagement.vue`
  - 区域树形选择器
  - 摄像头列表表格
  - 新增/编辑摄像头弹窗
  - 删除确认
  - 启动/停止操作
- [ ] 创建 `api/camera.ts` API 封装
- [ ] 创建 `api/area.ts` API 封装

### 联调测试
- [ ] 测试区域 CRUD
- [ ] 测试摄像头 CRUD
- [ ] 测试区域-摄像头关联
- [ ] 测试分页和筛选

### 交付物
- 区域树形管理功能
- 摄像头完整管理功能

---

## Phase 4: 模型与算法管理 (v1.5.0)

### 目标
实现 AI 模型管理和算法配置功能。

### 后端任务

#### 4.1 模型管理 API
- [ ] `GET /api/v1/models` - 获取模型列表
- [ ] `GET /api/v1/models/{id}` - 获取模型详情
- [ ] `POST /api/v1/models` - 创建模型
- [ ] `PUT /api/v1/models/{id}` - 更新模型
- [ ] `DELETE /api/v1/models/{id}` - 删除模型
- [ ] 模型文件上传处理

#### 4.2 算法管理 API
- [ ] `GET /api/v1/algorithms` - 获取算法列表
- [ ] `GET /api/v1/algorithms/{id}` - 获取算法详情
- [ ] `POST /api/v1/algorithms` - 创建算法
- [ ] `PUT /api/v1/algorithms/{id}` - 更新算法
- [ ] `DELETE /api/v1/algorithms/{id}` - 删除算法

#### 4.3 摄像头-算法关联 API
- [ ] `GET /api/v1/cameras/{id}/algorithms` - 获取摄像头算法配置
- [ ] `POST /api/v1/cameras/{id}/algorithms` - 添加算法到摄像头
- [ ] `PUT /api/v1/cameras/{id}/algorithms/{alg_id}` - 更新配置
- [ ] `DELETE /api/v1/cameras/{id}/algorithms/{alg_id}` - 移除算法

### 前端任务

#### 4.4 算法管理页面
- [ ] 完善 `AlgorithmManagement.vue`
  - 模型列表管理
  - 算法列表管理
  - 模型-算法关联配置
  - 检测区域绘制组件
- [ ] 创建 `api/model.ts` API 封装
- [ ] 创建 `api/algorithm.ts` API 封装

### 联调测试
- [ ] 测试模型 CRUD
- [ ] 测试算法 CRUD
- [ ] 测试摄像头-算法关联
- [ ] 测试检测区域配置

### 交付物
- 模型管理功能
- 算法管理功能
- 摄像头算法配置功能

---

## Phase 5: 告警管理与统计 (v1.6.0)

### 目标
实现告警查询、确认、统计功能。

### 后端任务

#### 5.1 告警管理 API
- [ ] `GET /api/v1/alarms` - 获取告警列表 (分页、筛选)
- [ ] `GET /api/v1/alarms/{id}` - 获取告警详情
- [ ] `PUT /api/v1/alarms/{id}/confirm` - 确认告警
- [ ] `PUT /api/v1/alarms/batch-confirm` - 批量确认
- [ ] `DELETE /api/v1/alarms/{id}` - 删除告警

#### 5.2 告警统计 API
- [ ] `GET /api/v1/alarms/stats` - 告警统计概览
- [ ] `GET /api/v1/alarms/stats/by-camera` - 按摄像头统计
- [ ] `GET /api/v1/alarms/stats/by-algorithm` - 按算法统计
- [ ] `GET /api/v1/alarms/stats/trend` - 告警趋势

### 前端任务

#### 5.3 告警管理页面
- [ ] 完善 `AlarmManagement.vue`
  - 告警列表表格
  - 多条件筛选
  - 告警详情弹窗
  - 批量操作
- [ ] 创建 `api/alarm.ts` API 封装

#### 5.4 Dashboard 页面
- [ ] 完善 `Dashboard.vue`
  - 对接统计 API
  - 实时数据展示
  - 告警趋势图表

### 联调测试
- [ ] 测试告警列表查询
- [ ] 测试告警筛选功能
- [ ] 测试告警确认流程
- [ ] 测试统计数据准确性

### 交付物
- 告警管理功能
- 告警统计功能
- Dashboard 数据展示

---

## Phase 6: 系统管理与推送配置 (v1.7.0)

### 目标
实现系统配置、用户管理、消息推送配置功能。

### 后端任务

#### 6.1 用户管理 API
- [ ] `GET /api/v1/users` - 获取用户列表
- [ ] `POST /api/v1/users` - 创建用户
- [ ] `PUT /api/v1/users/{id}` - 更新用户
- [ ] `DELETE /api/v1/users/{id}` - 删除用户

#### 6.2 系统信息 API
- [ ] `GET /api/v1/system/info` - 获取系统信息
- [ ] `GET /api/v1/system/dashboard` - Dashboard 统计数据

#### 6.3 推送配置 API
- [ ] `GET /api/v1/notifications/config` - 获取推送配置
- [ ] `PUT /api/v1/notifications/config` - 更新推送配置
- [ ] `POST /api/v1/notifications/test` - 测试推送

### 前端任务

#### 6.4 系统管理页面
- [ ] 完善 `SystemManagement.vue`
  - 用户管理 Tab
  - 系统配置 Tab
  - 系统信息展示

#### 6.5 推送管理页面
- [ ] 完善 `PushManagement.vue`
  - 钉钉配置
  - 邮件配置
  - Webhook 配置
  - 测试推送功能

### 联调测试
- [ ] 测试用户 CRUD
- [ ] 测试推送配置保存
- [ ] 测试钉钉推送
- [ ] 测试邮件推送

### 交付物
- 用户管理功能
- 系统配置功能
- 消息推送配置功能

---

## Phase 7: WebSocket 实时推送 (v1.8.0)

### 目标
实现 WebSocket 实时推送检测结果和告警。

### 后端任务

#### 7.1 WebSocket 服务
- [ ] 完善 `websocket/manager.py` 连接管理
- [ ] 完善 `websocket/handlers.py` Redis 订阅转发
- [ ] 实现 `/ws/detections/{camera_id}` 检测结果推送
- [ ] 实现 `/ws/alarms` 实时告警推送

#### 7.2 Redis Pub/Sub
- [ ] 实现检测结果频道订阅
- [ ] 实现告警频道订阅
- [ ] 连接断开重连机制

### 前端任务

#### 7.3 WebSocket 客户端
- [ ] 创建 `utils/websocket.ts` WebSocket 封装
  - 自动重连
  - 心跳检测
  - 消息解析

#### 7.4 视频预览页面
- [ ] 完善 `VideoPreview.vue`
  - WebSocket 连接管理
  - 实时检测框绘制
  - 多路视频切换

#### 7.5 实时告警通知
- [ ] 全局告警消息提示
- [ ] 告警声音提醒

### 联调测试
- [ ] 测试 WebSocket 连接建立
- [ ] 测试检测结果实时推送
- [ ] 测试告警实时推送
- [ ] 测试断线重连

### 交付物
- WebSocket 实时通信
- 视频检测框实时绘制
- 告警实时通知

---

## Phase 8: 视频处理引擎 (v1.9.0)

### 目标
实现完整的视频处理引擎，包括拉流、推理、推流、告警生成。

### 后端任务

#### 8.1 引擎调度器 (Scheduler)
- [ ] 实现 `engine/scheduler.py`
  - 进程管理
  - 配置热更新
  - 健康检查

#### 8.2 推理服务 (InferenceService)
- [ ] 实现 `engine/inference/service.py`
- [ ] 实现 `engine/inference/worker.py`
- [ ] 实现 `engine/inference/model_loader.py`
  - YOLO 模型加载
  - ONNX 模型加载
  - TensorRT 模型加载

#### 8.3 流处理管道 (Pipeline)
- [ ] 实现 `engine/pipeline/pipeline.py`
- [ ] 实现 `engine/pipeline/stream_reader.py` (RTSP 拉流)
- [ ] 实现 `engine/pipeline/stream_writer.py` (RTMP 推流)
- [ ] 实现 `engine/pipeline/result_handler.py`

#### 8.4 告警处理
- [ ] 告警去重 (时间窗口 + IoU)
- [ ] 告警入库
- [ ] 告警截图保存
- [ ] Redis 消息发布

### 联调测试
- [ ] 测试单路视频拉流
- [ ] 测试 AI 推理
- [ ] 测试检测结果推送
- [ ] 测试告警生成
- [ ] 测试多路并发

### 交付物
- 完整的视频处理引擎
- AI 推理功能
- 告警自动生成

---

## Phase 9: 集成测试与优化 (v2.0.0)

### 目标
完成整体联调测试，优化性能，准备生产部署。

### 任务

#### 9.1 集成测试
- [ ] 端到端完整流程测试
- [ ] 多用户并发测试
- [ ] 多路视频压力测试
- [ ] 长时间稳定性测试

#### 9.2 性能优化
- [ ] 数据库查询优化
- [ ] Redis 缓存优化
- [ ] 前端加载优化
- [ ] 视频编解码优化

#### 9.3 部署准备
- [ ] 完善 Dockerfile
- [ ] 完善 docker-compose.yml (生产配置)
- [ ] 编写部署文档
- [ ] 编写用户手册

#### 9.4 代码质量
- [ ] 代码审查
- [ ] 单元测试补充
- [ ] API 文档完善
- [ ] 注释和文档完善

### 交付物
- v2.0.0 正式版本
- 完整部署文档
- 用户使用手册

---

## 开发规范

### Git 提交规范

```
feat: 新增功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式调整
refactor: 重构代码
test: 测试相关
chore: 构建/工具相关
```

### 版本发布流程

1. 完成当前阶段所有任务
2. 本地运行联调测试
3. 提交代码到分支
4. 合并到主分支 (如需要)
5. 创建版本 Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z: 版本描述"`
6. 推送 Tag: `git push origin vX.Y.Z`

### 联调测试检查清单

- [ ] 后端服务启动正常
- [ ] 前端项目编译通过
- [ ] API 接口响应正确
- [ ] 数据库操作正确
- [ ] Redis 操作正确
- [ ] 页面功能正常
- [ ] 无控制台错误
- [ ] 无网络请求错误

---

## 当前进度

- [x] v1.0.0 - 初始版本发布
- [x] v1.1.0 - 后端架构重构
- [ ] v1.2.0 - 基础设施搭建 (进行中)

---

## 备注

1. 每个阶段完成后，确保联调测试通过再发布版本
2. 遇到问题及时记录，必要时调整计划
3. 保持代码提交粒度适中，便于追溯
4. 重要变更需要更新相关文档
