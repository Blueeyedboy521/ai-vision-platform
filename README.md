# AI Vision Platform

智能视频分析平台 - 基于 AI 的视频监控与告警系统。

## 项目结构

```
ai-vision-platform/
├── frontend/           # 前端项目 (Vue 3 + TypeScript + Vite)
├── backend/            # 后端项目 (Python + FastAPI)
├── .cursor/            # Cursor IDE 配置
└── README.md
```

## 功能特性

- **实时视频预览**: 多路视频流同时查看
- **智能告警**: 基于 AI 算法的自动告警检测
- **区域管理**: 灵活的摄像头分区管理
- **算法配置**: 多种检测算法可配置
- **告警推送**: 支持多渠道告警通知
- **系统管理**: 用户、角色、权限管理

## 支持的算法

- 人员入侵检测
- 烟火检测
- 安全帽检测
- 人员聚集检测
- 离岗检测
- 更多...

## 快速开始

### 启动后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Vue3)                           │
│  - 实时视频播放 (WebRTC/HLS)                             │
│  - 告警展示与处理                                         │
│  - 系统配置管理                                           │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP / WebSocket
┌─────────────────────▼───────────────────────────────────┐
│              后端 API (FastAPI)                          │
│  - RESTful API                                          │
│  - JWT 认证                                              │
│  - 业务逻辑处理                                           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              数据存储层                                   │
│  - PostgreSQL / SQLite (业务数据)                        │
│  - Redis (缓存、消息队列)                                 │
└─────────────────────────────────────────────────────────┘
```

## 文档

- [前端文档](./frontend/README.md)
- [后端文档](./backend/README.md)

## License

MIT
