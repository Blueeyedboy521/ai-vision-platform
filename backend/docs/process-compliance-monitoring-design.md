# 工序合规监测系统设计文档

## 1. 系统概述

### 1.1 项目背景
基于现有 AI 视觉平台架构，增加工序合规监测功能，特别是设备巡检合规监测。系统将利用现有摄像头网络，实现对巡检人员行为的客观记录与核验，重点关注人员是否按时到达指定设备部位及其停留时间。

### 1.2 系统目标
- 基于现有摄像头网络实现设备巡检合规监测
- 支持巡检路线编排与管理
- 自动记录巡检行为并进行客观核验
- 提供巡检数据分析与报告
- 与现有系统架构无缝集成

### 1.3 核心功能
- 巡检路线编排与管理
- 巡检任务调度与下发
- 巡检过程视觉监测
- 巡检行为记录与核验（重点关注到达时间和停留时间）
- 巡检数据统计与分析

## 2. 现有架构分析

### 2.1 现有系统组件
- **前端**：Vue 3 + TypeScript + Naive UI
- **后端**：FastAPI + MySQL + Redis
- **AI引擎**：基于FFmpeg的视频处理和模型推理
- **流媒体**：ZLMediaKit
- **存储**：本地存储/MinIO

### 2.2 现有数据模型
- **摄像头管理**：camera表
- **区域管理**：area表（树形结构，支持层级）
- **算法管理**：model表
- **告警管理**：alarm表
- **用户管理**：user表
- **角色管理**：role表

### 2.3 现有API接口
- **摄像头API**：/api/v1/cameras
- **区域API**：/api/v1/areas
- **算法API**：/api/v1/models
- **告警API**：/api/v1/alarms
- **用户API**：/api/v1/users

### 2.4 现有AI能力
- **目标检测**：YOLO模型
- **视频处理**：FFmpeg + OpenCV
- **区域检测**：支持区域内目标检测
- **实时推流**：支持实时视频流处理

## 3. 系统设计

### 3.1 数据模型设计

#### 3.1.1 巡检路线表（inspection_route）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 路线ID（UUID） |
| name | VARCHAR | 100 | NOT NULL | 路线名称 |
| description | TEXT | - | NULL | 路线描述 |
| frequency_type | VARCHAR | 20 | NOT NULL | 频率类型（daily/weekly/monthly） |
| frequency_value | INT | - | NOT NULL | 频率值（如每天2次） |
| start_time | TIME | - | NOT NULL | 开始时间 |
| end_time | TIME | - | NOT NULL | 结束时间 |
| status | VARCHAR | 20 | NOT NULL | 状态（active/inactive） |
| estimated_duration | INT | - | NOT NULL | 预计完成时间（分钟） |
| created_by | VARCHAR | 36 | NOT NULL | 创建人ID |
| updated_by | VARCHAR | 36 | NOT NULL | 更新人ID |
| created_at | DATETIME | - | NOT NULL | 创建时间 |
| updated_at | DATETIME | - | NOT NULL | 更新时间 |

#### 3.1.2 巡检点表（inspection_point）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 巡检点ID（UUID） |
| route_id | VARCHAR | 36 | NOT NULL | 路线ID |
| area_id | VARCHAR | 36 | NOT NULL | 区域ID |
| device_id | VARCHAR | 36 | NOT NULL | 设备ID |
| part_id | VARCHAR | 36 | NULL | 设备部位ID（可选） |
| camera_id | VARCHAR | 36 | NOT NULL | 监控摄像头ID |
| sequence | INT | - | NOT NULL | 巡检顺序 |
| estimated_duration | INT | - | NOT NULL | 预计停留时间（分钟） |
| min_duration | INT | - | NOT NULL | 最小停留时间（秒） |
| max_duration | INT | - | NOT NULL | 最大停留时间（分钟） |
| created_by | VARCHAR | 36 | NOT NULL | 创建人ID |
| updated_by | VARCHAR | 36 | NOT NULL | 更新人ID |
| created_at | DATETIME | - | NOT NULL | 创建时间 |
| updated_at | DATETIME | - | NOT NULL | 更新时间 |

#### 3.1.3 巡检任务表（inspection_task）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 任务ID（UUID） |
| route_id | VARCHAR | 36 | NOT NULL | 路线ID |
| task_no | VARCHAR | 50 | NOT NULL | 任务编号 |
| scheduled_time | DATETIME | - | NOT NULL | 计划执行时间 |
| actual_start_time | DATETIME | - | NULL | 实际开始时间 |
| actual_end_time | DATETIME | - | NULL | 实际结束时间 |
| status | VARCHAR | 20 | NOT NULL | 状态（scheduled/executing/completed/canceled） |
| assigned_user_id | VARCHAR | 36 | NOT NULL | 分配的用户ID |
| executor_id | VARCHAR | 36 | NULL | 实际执行人ID |
| duration | INT | - | NULL | 实际执行时间（分钟） |
| created_by | VARCHAR | 36 | NOT NULL | 创建人ID |
| updated_by | VARCHAR | 36 | NOT NULL | 更新人ID |
| created_at | DATETIME | - | NOT NULL | 创建时间 |
| updated_at | DATETIME | - | NOT NULL | 更新时间 |

#### 3.1.4 巡检记录表（inspection_record）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 记录ID（UUID） |
| task_id | VARCHAR | 36 | NOT NULL | 任务ID |
| point_id | VARCHAR | 36 | NOT NULL | 巡检点ID |
| start_time | DATETIME | - | NOT NULL | 开始时间 |
| end_time | DATETIME | - | NOT NULL | 结束时间 |
| duration | INT | - | NOT NULL | 停留时间（秒） |
| status | VARCHAR | 20 | NOT NULL | 状态（completed/timeout/skipped） |
| confidence | FLOAT | - | NOT NULL | 检测置信度 |
| image_url | VARCHAR | 255 | NULL | 现场截图URL |
| created_at | DATETIME | - | NOT NULL | 创建时间 |
| updated_at | DATETIME | - | NOT NULL | 更新时间 |

#### 3.1.5 巡检轨迹表（inspection_trail）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 轨迹ID（UUID） |
| task_id | VARCHAR | 36 | NOT NULL | 任务ID |
| user_id | VARCHAR | 36 | NOT NULL | 用户ID |
| point_id | VARCHAR | 36 | NOT NULL | 巡检点ID |
| camera_id | VARCHAR | 36 | NOT NULL | 摄像头ID |
| detected_time | DATETIME | - | NOT NULL | 检测时间 |
| confidence | FLOAT | - | NOT NULL | 检测置信度 |
| image_url | VARCHAR | 255 | NULL | 截图URL |
| created_at | DATETIME | - | NOT NULL | 创建时间 |

### 3.2 API接口设计

#### 3.2.1 巡检路线管理
```python
# 路线管理
GET /api/v1/inspection/routes
POST /api/v1/inspection/routes
GET /api/v1/inspection/routes/{id}
PUT /api/v1/inspection/routes/{id}
DELETE /api/v1/inspection/routes/{id}

# 巡检点管理
GET /api/v1/inspection/routes/{route_id}/points
POST /api/v1/inspection/routes/{route_id}/points
PUT /api/v1/inspection/points/{id}
DELETE /api/v1/inspection/points/{id}
```

#### 3.2.2 巡检任务管理
```python
# 任务管理
GET /api/v1/inspection/tasks
POST /api/v1/inspection/tasks
GET /api/v1/inspection/tasks/{id}
PUT /api/v1/inspection/tasks/{id}
DELETE /api/v1/inspection/tasks/{id}

# 任务执行
POST /api/v1/inspection/tasks/{id}/start
POST /api/v1/inspection/tasks/{id}/complete
POST /api/v1/inspection/tasks/{id}/cancel

# 任务记录
GET /api/v1/inspection/tasks/{id}/records
GET /api/v1/inspection/tasks/{id}/trails
```

#### 3.2.3 巡检统计分析
```python
# 巡检统计
GET /api/v1/inspection/stats/summary
GET /api/v1/inspection/stats/by-route
GET /api/v1/inspection/stats/by-user
GET /api/v1/inspection/stats/by-area

# 巡检报告
GET /api/v1/inspection/reports/daily
GET /api/v1/inspection/reports/weekly
GET /api/v1/inspection/reports/monthly
```

### 3.3 前端界面设计

#### 3.3.1 巡检路线编排
- **路线管理**：创建、编辑、删除巡检路线
- **巡检点管理**：为路线添加巡检点，配置摄像头、停留时间等
- **可视化编辑**：拖拽式编辑巡检路线，支持调整顺序
- **频率设置**：设置巡检频率和时间窗口

#### 3.3.2 巡检任务管理
- **任务列表**：查看所有巡检任务，支持筛选和排序
- **任务详情**：查看任务详情，包括执行状态和轨迹
- **任务分配**：分配巡检任务给特定用户
- **任务日历**：日历视图展示巡检任务安排

#### 3.3.3 巡检执行
- **任务执行界面**：显示当前任务的路线和巡检点
- **实时定位**：显示当前位置和已完成的巡检点
- **异常上报**：快速上报异常情况

#### 3.3.4 巡检统计分析
- **统计仪表盘**：展示巡检完成率、按时率等关键指标
- **趋势分析**：巡检数据趋势图表
- **异常分析**：异常问题分布和趋势
- **导出报告**：导出巡检报告为PDF或Excel

### 3.4 AI视觉监测设计

#### 3.4.1 人员检测
- **目标检测**：使用现有YOLO模型检测人员
- **区域验证**：验证人员是否在指定巡检点区域内
- **停留时间计算**：计算人员在巡检点的停留时间

#### 3.4.2 区域监测
- **区域入侵检测**：检测人员是否进入指定巡检区域
- **停留时间分析**：分析人员在每个巡检点的停留时间
- **路线验证**：验证人员是否按照规定路线巡检

### 3.5 任务生成与触发逻辑

#### 3.5.1 任务生成
1. **定时任务**：每天凌晨根据巡检路线的频率设置生成当天的巡检任务
2. **生成逻辑**：
   - 遍历所有激活状态的巡检路线
   - 根据频率类型（daily/weekly/monthly）计算当天是否需要生成任务
   - 根据频率值确定生成任务的数量
   - 根据开始时间和预计完成时间确定具体的任务时间

#### 3.5.2 任务触发与执行流程

**1. 任务开始触发**：
- 系统在任务计划时间前15分钟发送通知给分配的用户
- 用户可通过前端界面确认开始任务
- 系统记录实际开始时间
- 系统自动触发对应路线的摄像头开始监控

**2. 任务执行过程**：
- 系统根据巡检点顺序引导用户完成巡检
- 摄像头实时监测用户是否到达指定位置
- 检测到用户到达后开始计时
- 监测用户在该点的停留时间
- 当用户离开巡检点区域时结束计时并记录停留时间
- 系统自动判断停留时间是否符合要求（在min_duration和max_duration之间）

**3. 任务完成**：
- 用户完成所有巡检点后，系统自动标记任务为完成
- 系统计算实际执行时间
- 生成巡检报告
- 系统自动停止相关摄像头的监控

**4. 异常处理**：
- 超时未开始：任务计划时间超过30分钟未开始，系统标记为超时
- 漏检：未检测到用户到达某个巡检点，系统标记为漏检
- 停留时间异常：停留时间不在规定范围内，系统标记为异常

### 3.6 与现有系统集成

#### 3.6.1 摄像头集成
- 利用现有摄像头网络进行视觉监测
- 复用现有摄像头管理API
- 利用现有流媒体服务进行视频处理

#### 3.6.2 用户系统集成
- 复用现有用户和权限系统
- 支持基于角色的访问控制

#### 3.6.3 告警系统集成
- 将巡检异常与现有告警系统集成
- 支持巡检异常的告警推送

#### 3.6.4 存储系统集成
- 使用现有存储系统存储巡检数据和图片
- 复用现有文件预览接口

#### 3.6.5 AI引擎集成
- 利用现有AI引擎进行人员检测
- 扩展现有推理服务支持巡检场景

## 4. 技术实现方案

### 4.1 后端实现

#### 4.1.1 目录结构
```
backend/
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       └── inspection.py  # 巡检相关API
│   ├── models/
│   │   └── inspection.py  # 巡检相关数据模型
│   ├── schemas/
│   │   └── inspection.py  # 巡检相关请求/响应模式
│   ├── services/
│   │   ├── inspection_service.py  # 巡检业务逻辑
│   │   ├── task_scheduler.py  # 任务调度器
│   │   └── inspection_monitor.py  # 巡检监测服务
│   └── consumer/
│       └── inspection_consumer.py  # 巡检数据消费者
├── engine/
│   ├── inference/
│   │   └── inferencer_inspection.py  # 巡检专用推理器
│   └── pipeline/
│       └── inspection_handler.py  # 巡检结果处理
└── common/
    └── inspection/
        ├── __init__.py
        └── utils.py  # 巡检工具函数
```

#### 4.1.2 核心服务

**1. 任务调度服务**
- 负责定期生成巡检任务
- 管理任务的生命周期
- 发送任务通知
- 触发摄像头监控

**2. 巡检监测服务**
- 监控摄像头实时视频
- 检测人员是否到达指定位置
- 记录停留时间
- 生成巡检记录

**3. 巡检数据分析服务**
- 分析巡检数据
- 生成统计报表
- 识别异常模式

### 4.2 前端实现

#### 4.2.1 页面结构
```
frontend/src/views/
└── inspection/
    ├── RouteManagement.vue  # 路线管理
    ├── TaskManagement.vue  # 任务管理
    ├── TaskExecution.vue  # 任务执行
    ├── Stats.vue  # 统计分析
    └── Reports.vue  # 报告生成
```

#### 4.2.2 核心组件
- **巡检路线编辑器**：可视化编辑巡检路线和巡检点
- **任务执行组件**：引导用户完成巡检任务
- **实时监测组件**：显示实时监测结果
- **统计图表组件**：展示巡检数据统计

### 4.3 AI引擎扩展

#### 4.3.1 推理器扩展
- 基于现有YOLO推理器扩展巡检专用推理器
- 优化人员检测算法，提高准确率
- 支持区域内人员检测和停留时间计算

#### 4.3.2 结果处理
- 扩展现有结果处理逻辑，支持巡检场景
- 实现停留时间计算
- 生成巡检记录和轨迹

## 5. 部署方案

### 5.1 系统架构
- **前端**：部署在Web服务器
- **后端**：部署在应用服务器
- **AI引擎**：部署在GPU服务器
- **数据库**：MySQL主从架构
- **缓存**：Redis集群
- **存储**：MinIO集群

### 5.2 性能优化
- **视频处理优化**：使用GPU加速视频处理
- **模型优化**：使用轻量级模型进行实时检测
- **数据缓存**：使用Redis缓存热点数据
- **异步处理**：使用Celery处理异步任务
- **负载均衡**：使用Nginx进行负载均衡

### 5.3 安全考虑
- **数据加密**：敏感数据加密存储
- **访问控制**：基于现有权限系统的访问控制
- **数据备份**：定期备份巡检数据
- **审计日志**：记录所有操作日志

## 6. 实施计划

### 6.1 阶段一：基础架构搭建
- 设计并创建数据库表结构
- 实现巡检路线管理API
- 开发巡检路线编排前端界面

### 6.2 阶段二：核心功能实现
- 实现巡检任务管理API
- 开发巡检任务管理前端界面
- 集成AI视觉监测功能

### 6.3 阶段三：系统集成
- 与现有摄像头系统集成
- 与现有用户系统集成
- 与现有告警系统集成

### 6.4 阶段四：测试与优化
- 系统功能测试
- 性能测试与优化
- 安全测试

### 6.5 阶段五：部署与上线
- 系统部署
- 用户培训
- 系统上线运行

## 7. 预期效果

### 7.1 业务价值
- **提高巡检效率**：自动化巡检任务管理和监测
- **确保巡检质量**：客观记录和核验巡检行为
- **降低人工成本**：减少人工监督和管理成本
- **提升管理水平**：数据驱动的巡检管理和分析

### 7.2 技术价值
- **扩展现有系统**：基于现有架构扩展新功能
- **AI应用落地**：将AI技术应用于实际业务场景
- **数据价值挖掘**：通过巡检数据挖掘业务价值
- **系统架构优化**：优化现有系统架构，提高可扩展性

## 8. 风险评估

### 8.1 技术风险
- **AI模型准确性**：人员检测和行为分析的准确性
- **系统性能**：实时视频处理的性能要求
- **数据存储**：大量视频和图片数据的存储需求

### 8.2 业务风险
- **用户接受度**：巡检人员对新系统的接受度
- **流程适配**：现有巡检流程与新系统的适配
- **成本投入**：系统开发和部署的成本投入

### 8.3 应对措施
- **模型优化**：持续优化AI模型，提高准确性
- **性能优化**：优化系统架构，提高性能
- **分阶段实施**：分阶段实施，降低风险
- **用户培训**：加强用户培训，提高接受度

## 9. 结论

本设计方案基于现有系统架构，实现了工序合规监测功能，特别是设备巡检合规监测。通过AI视觉监测技术，系统能够客观记录和核验巡检行为，重点关注人员是否按时到达指定设备部位及其停留时间，不需要检测检查项和设备运行状态。

系统设计考虑了与现有系统的集成，确保了系统的可扩展性和稳定性。分阶段实施计划降低了项目风险，确保了系统的顺利上线。

预期该系统将为工厂管理带来显著的业务价值，推动工厂管理向数字化、智能化方向发展。