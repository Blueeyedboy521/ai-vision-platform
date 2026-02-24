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

视频拉流、推理、告警等由独立引擎进程完成，与 FastAPI 分开启动：

```bash
cd backend
python -m engine.main
```

需保证 Redis、MySQL 及 `.env` 中相关配置正确，以便与主服务协同。

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
│   ├── main.py              # 应用入口
│   ├── api/
│   │   ├── __init__.py      # API 路由聚合
│   │   └── endpoints/       # API 端点
│   │       ├── auth.py      # 认证
│   │       ├── cameras.py   # 摄像头管理
│   │       ├── areas.py     # 区域管理
│   │       ├── alarms.py    # 告警管理
│   │       ├── algorithms.py # 算法管理
│   │       └── system.py    # 系统管理
│   ├── core/
│   │   ├── config.py        # 配置
│   │   └── security.py      # 安全/认证
│   └── models/              # 数据模型
│       ├── user.py
│       ├── camera.py
│       ├── area.py
│       ├── alarm.py
│       └── algorithm.py
├── tests/                   # 测试
├── requirements.txt         # 依赖
├── pyproject.toml          # 项目配置
└── .env.example            # 环境变量示例
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
