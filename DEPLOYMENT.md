# AI 视觉平台部署指南

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [开发环境](#开发环境)
- [生产环境](#生产环境)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 环境要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| 存储 | 50GB SSD | 200GB+ SSD |
| GPU | - | NVIDIA RTX 3060+ (用于 AI 推理) |

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- (可选) NVIDIA Docker Runtime (GPU 支持)

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-repo/ai-vision-platform.git
cd ai-vision-platform
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，修改数据库密码等敏感信息
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 访问服务

- 前端界面: http://localhost
- API 文档: http://localhost/api/docs
- ZLMediaKit: http://localhost:8080

---

## 开发环境

### 启动基础设施

```bash
# 仅启动 MySQL, Redis, ZLMediaKit
docker-compose -f docker-compose.dev.yml up -d
```

### 启动后端服务

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 启动视频处理引擎 (可选)

```bash
cd backend
python engine/main.py
```

---

## 生产环境

### 1. 服务器准备

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# (可选) 安装 NVIDIA Docker
# 参考: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### 2. 配置

```bash
# 复制配置文件
cp .env.example .env

# 编辑生产配置
vim .env
```

重要配置项：

```env
# 数据库
MYSQL_ROOT_PASSWORD=<强密码>
MYSQL_PASSWORD=<强密码>

# Redis
REDIS_PASSWORD=<强密码>

# JWT
JWT_SECRET_KEY=<随机字符串>

# ZLMediaKit
ZLM_SECRET=<随机UUID>
```

### 3. 构建前端

```bash
cd frontend
npm install
npm run build
```

### 4. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 启动包含引擎的完整服务
docker-compose --profile engine up -d
```

### 5. 配置反向代理 (可选)

如果需要 HTTPS，推荐使用 Nginx 或 Traefik 作为反向代理。

---

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 | root123456 |
| `MYSQL_DATABASE` | 数据库名 | ai_vision |
| `MYSQL_USER` | 数据库用户 | aivision |
| `MYSQL_PASSWORD` | 数据库密码 | aivision123 |
| `REDIS_PASSWORD` | Redis 密码 | redis123 |
| `JWT_SECRET_KEY` | JWT 密钥 | - |
| `ZLM_SECRET` | ZLMediaKit API 密钥 | - |
| `BACKEND_PORT` | 后端端口 | 8000 |
| `FRONTEND_PORT` | 前端端口 | 80 |

### 端口映射

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 80 | HTTP |
| Backend | 8000 | API |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |
| ZLMediaKit | 1935 | RTMP |
| ZLMediaKit | 554 | RTSP |
| ZLMediaKit | 8080 | HTTP-FLV/API |

---

## 常见问题

### 1. 数据库连接失败

检查 MySQL 服务状态：
```bash
docker-compose logs mysql
```

### 2. Redis 连接失败

检查 Redis 密码配置是否正确。

### 3. 视频无法播放

1. 检查 ZLMediaKit 服务状态
2. 检查防火墙是否开放相关端口
3. 确认视频流地址正确

### 4. GPU 推理不工作

1. 确认已安装 NVIDIA Docker Runtime
2. 检查 GPU 驱动版本
3. 取消 docker-compose.yml 中 GPU 配置的注释

---

## 维护命令

```bash
# 查看日志
docker-compose logs -f [service]

# 重启服务
docker-compose restart [service]

# 更新服务
docker-compose pull
docker-compose up -d

# 备份数据
docker-compose exec mysql mysqldump -u root -p ai_vision > backup.sql

# 清理资源
docker-compose down -v  # 警告: 会删除所有数据
```

---

## 联系支持

如有问题，请提交 Issue 或联系开发团队。
