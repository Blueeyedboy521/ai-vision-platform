# AI Vision Platform - Frontend

基于 Vue 3 + TypeScript + Vite 的 AI 视觉平台前端。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **构建**: Vite
- **状态管理**: Pinia
- **路由**: Vue Router
- **UI**: 自定义组件

## 快速开始

### 1. 安装依赖

```bash
pnpm install
# 或
npm install
```

### 2. 启动开发服务器

```bash
pnpm dev
# 或
npm run dev
```

### 3. 构建生产版本

```bash
pnpm build
# 或
npm run build
```

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── assets/         # 样式资源
│   │   └── styles/
│   ├── components/     # 组件
│   ├── views/          # 页面视图
│   ├── router/         # 路由配置
│   ├── stores/         # 状态管理
│   ├── App.vue         # 根组件
│   └── main.ts         # 入口文件
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## 主要功能模块

- **仪表盘**: 系统概览、统计图表
- **视频预览**: 实时视频流查看
- **摄像头管理**: 摄像头配置、区域管理
- **告警管理**: 告警列表、处理
- **算法管理**: 算法配置
- **推送管理**: 告警推送配置
- **系统管理**: 用户、角色、日志
