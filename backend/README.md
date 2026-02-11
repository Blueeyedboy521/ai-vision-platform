# AI Vision Platform - Backend

基于 FastAPI 的 AI 视觉平台后端服务。

## 技术栈

- **框架**: FastAPI
- **数据库**: PostgreSQL / SQLite (开发)
- **ORM**: SQLAlchemy 2.0
- **缓存**: Redis
- **认证**: JWT

## 快速开始

### 1. 创建虚拟环境

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

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或者
python -m app.main
```

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

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
