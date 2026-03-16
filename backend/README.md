# AI Vision Platform - Backend

基于 FastAPI 的 AI 视觉平台后端服务。

## 技术栈

- **框架**: FastAPI
- **数据库**: MySQL（异步 aiomysql）
- **ORM**: SQLAlchemy 2.0
- **缓存**: Redis
- **认证**: JWT

## 快速开始

### 1. 创建虚拟环境（可选择）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件配置相关参数
```

### 4. 启动服务

见下方 [程序如何启动](#程序如何启动)。

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  

---

## 程序如何启动

### 前置条件

1. **MySQL**：已创建数据库（如 `ai_vision`），并在 `.env` 中配置 `DATABASE_URL`。  
2. **Redis**：已启动，并在 `.env` 中配置 `REDIS_URL`。  
3. **.env**：在 `backend` 目录下已复制 `.env.example` 为 `.env` 并填写各项配置。

### 开发环境启动

在项目 **backend** 目录下执行：

```bash
# 进入后端目录
cd backend

# 激活虚拟环境（若已创建）
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# 启动 FastAPI（热重载，默认 0.0.0.0:8000）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- 修改代码后会自动重载。  
- 接口地址：`http://localhost:8000`，API 前缀：`/api/v1`。  
- 健康检查：`http://localhost:8000/health`。
- uvicorn	启动 Uvicorn 服务器
- app.main:app	指定要运行的 Web 应用：- app.main：找到 app 目录下的 main.py 文件- :app：加载 main.py 中名为 app 的 FastAPI/Starlette 实例
- --reload	热重载：开发时修改代码后自动重启服务，无需手动停止 / 启动
- --host 0.0.0.0	允许所有网络设备访问（如同一局域网的电脑、手机，或服务器外网访问）
- --port 8000	指定服务运行的端口为 8000，访问地址为 http://服务器IP:8000

### 生产环境启动

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

- 不加 `--reload`，通过 `--workers` 指定进程数。  
- 也可使用 gunicorn：`gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000`。

### 使用 py 模块方式启动（可选）

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 视频处理引擎（独立进程，可选）

视频拉流、推理、告警等由独立引擎进程完成，与 FastAPI 分开启动（Engine 内部为**单进程 + 多线程**架构，通过 Scheduler 调度 InferenceService / PipelineService 管理各类 Worker/Pipeline 线程）：

```bash
cd backend
python -m engine.main
```

需保证 Redis、MySQL 及 `.env` 中相关配置正确，以便与主服务协同。

引擎进程不会直接访问数据库，只通过 **Redis** 获取摄像头、模型、算法及绑定配置：

- FastAPI 负责：
  - 读写 MySQL 中的业务配置（摄像头、模型、算法、摄像头-算法绑定等）
  - 启动时通过 `bootstrap_sync` 将当前 DB 配置全量写入 Redis，并为每路摄像头在流管理器中注册流；增删改配置时同步写/删 Redis 对应 Key
  - 通过 Redis Pub/Sub 向频道 `engine:config_update` 发布配置变更事件
- 引擎负责：
  - 启动时从 Redis 读取所需配置快照
  - 订阅 `engine:config_update` 频道，根据事件类型（模型新增/修改/删除、算法新增/修改/删除、摄像头算法绑定变更、摄像头启动/停止等）从 Redis 重新读取对应配置并更新内存

### 启动失败时检查

| 现象 | 可能原因 |
|------|----------|
| 端口被占用 | 更换 `--port` 或结束占用 8000 的进程 |
| 数据库连接失败 | 检查 `DATABASE_URL`、MySQL 是否启动、库是否已建 |
| Redis 连接失败 | 检查 `REDIS_URL`、Redis 是否启动 |
| 模块找不到 | 在 `backend` 目录下执行命令，并确认已 `pip install -r requirements.txt` |

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # 应用入口
│   ├── api/
│   │   ├── __init__.py          # API 路由聚合
│   │   └── endpoints/           # API 控制器 (FastAPI Router)
│   │       ├── auth_controller.py         # 认证
│   │       ├── cameras_controller.py      # 摄像头管理
│   │       ├── areas_controller.py        # 区域管理
│   │       ├── alarms_controller.py       # 告警管理
│   │       ├── algorithms_controller.py   # 算法管理
│   │       ├── system_controller.py       # 系统信息/仪表盘
│   │       └── media_hooks_controller.py  # 流媒体 Hook 回调
│   ├── services/               # 业务服务层（高内聚、可复用）
│   │   ├── auth_service.py
│   │   ├── camera_service.py
│   │   ├── area_service.py
│   │   ├── alarm_service.py
│   │   ├── algorithm_service.py
│   │   ├── model_service.py
│   │   ├── file_service.py
│   │   ├── notification_config_service.py
│   │   ├── notification_service.py
│   │   └── system_service.py
│   ├── core/
│   │   ├── config.py            # 配置
│   │   ├── security.py          # 安全/认证
│   │   └── redis.py             # Redis 连接与常用操作封装（支持 async + sync）
│   └── models/                  # 数据模型
│       ├── user.py
│       ├── camera.py
│       ├── area.py
│       ├── alarm.py
│       └── algorithm.py
├── tests/                       # 测试
├── requirements.txt             # 依赖
├── pyproject.toml              # 项目配置
└── .env.example                # 环境变量示例
```

## API 概览

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth` | 登录、用户信息 |
| 摄像头 | `/api/v1/cameras` | 摄像头 CRUD |
| 区域 | `/api/v1/areas` | 区域管理 |
| 告警 | `/api/v1/alarms` | 告警查询、处理 |
| 算法 | `/api/v1/algorithms` | 算法配置 |
| 系统 | `/api/v1/system` | 系统信息、日志 |

## 默认账号

- 用户名: `admin`
- 密码: `admin123`

## 开发说明

### 代码格式化

```bash
black app/
ruff check app/ --fix
```

### 运行测试

```bash
pytest
```

### 摄像头联调小贴士

- **连通性测试**：前端“流通性测试”按钮会调用 `POST /api/v1/cameras/probe-stream`，后端通过 OpenCV/ffprobe 获取 RTSP 流的宽高、帧率并回填表单。
- **抓拍快照**：`POST /api/v1/cameras/{id}/snapshot` 使用第 50 帧避免黑屏，通过统一存储接口写入本地或 MinIO，并将存储 key 写入 `camera.last_snapshot_path`。
- **缩略图展示**：摄像头列表与编辑页读取 `snapshot_url`（由存储层生成的 URL），无快照时使用默认占位图。
- **实时预览与心跳**：
  - `POST /api/v1/cameras/{id}/start` / `/stop`：通过 Redis 通知 Engine 启动/停止该摄像头的 Pipeline。
  - `GET /api/v1/cameras/{id}/play-url`：返回 ZLMediaKit 的播放地址（HTTP-FLV 等），前端用 flv.js 播放。
  - `POST /api/v1/cameras/{id}/live-heartbeat`：前端播放时每 60 秒调用一次，后端记录到 Redis，后续可用于自动关闭长期无观众的推流。

## ffmpeg
```bash
ffplay -x 1280 -y 720 -fflags nobuffer -flags low_delay -i "rtmp://172.21.68.125:1935/live/camera_926001bb83db48bcb62cf3ebf0eb1e72"

 ffplay -fflags nobuffer -flags low_delay -i "rtsp://172.21.68.125:8554/live/camera_local"
```

