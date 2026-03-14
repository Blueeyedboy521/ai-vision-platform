# 配置管理设计文档

## 1. 设计目标

### 1.1 背景
当前系统配置通过 `.env` 文件管理，所有配置信息都存储在环境变量中。为了支持负载均衡和动态配置调整，需要将部分配置迁移到数据库中管理。

### 1.2 设计目标
- 支持多实例负载均衡，配置统一管理
- 支持动态配置调整，无需重启服务
- 保持系统安全性，敏感配置继续使用环境变量
- 提高配置管理的灵活性和可维护性

## 2. 配置分类原则

### 2.1 必须保留在 .env 的配置
**特征**：
- 系统启动必需的基础配置
- 涉及安全性和敏感信息的配置
- 数据库连接相关配置
- 基础架构配置

**原因**：
- 确保系统启动的稳定性
- 防止敏感信息泄露
- 避免配置循环依赖
- 支持容器化部署

### 2.2 可以存储在数据库的配置
**特征**：
- 业务相关的功能配置
- 可动态调整的配置项
- 非敏感的配置信息
- 功能开关和阈值配置

**原因**：
- 支持动态配置更新
- 便于多实例配置同步
- 降低运维复杂度
- 提高配置管理的灵活性

## 3. 现有配置分析

### 3.1 现有 .env 配置（必须保留）

#### 3.1.1 基础配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 项目名称 | PROJECT_NAME | string | AI Vision Platform | 项目名称 | ✅ 现有 |
| 运行环境 | ENVIRONMENT | string | development | 运行环境: development / production / testing | ✅ 现有 |
| 调试模式 | DEBUG | boolean | True | 是否开启调试模式 | ✅ 现有 |

#### 3.1.2 数据库配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 数据库连接URL | DATABASE_URL | string | mysql+aiomysql://root:root@localhost:3306/ai_vision | 数据库连接URL | ✅ 现有 |
| 数据库连接池大小 | DB_POOL_SIZE | int | 10 | 数据库连接池大小 | ✅ 现有 |
| 数据库连接池最大溢出数 | DB_MAX_OVERFLOW | int | 20 | 数据库连接池最大溢出数 | ✅ 现有 |
| 数据库连接回收时间 | DB_POOL_RECYCLE | int | 3600 | 数据库连接回收时间(秒) | ✅ 现有 |

#### 3.1.3 Redis 配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| Redis 连接URL | REDIS_URL | string | redis://localhost:6379/0 | Redis 连接URL | ✅ 现有 |
| Redis 最大连接数 | REDIS_MAX_CONNECTIONS | int | 50 | Redis 最大连接数 | ✅ 现有 |

#### 3.1.4 JWT 认证配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| JWT 密钥 | SECRET_KEY | string | change-this-secret-key-in-production-environment | JWT 密钥，生产环境必须修改 | ✅ 现有 |
| JWT 加密算法 | ALGORITHM | string | HS256 | JWT 加密算法 | ✅ 现有 |
| Access Token 有效期 | ACCESS_TOKEN_EXPIRE_MINUTES | int | 1440 | Access Token 有效期(分钟)，默认24小时 | ✅ 现有 |
| Refresh Token 有效期 | REFRESH_TOKEN_EXPIRE_DAYS | int | 7 | Refresh Token 有效期(天)，默认7天 | ✅ 现有 |

#### 3.1.5 ZLMediaKit 流媒体配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| ZLMediaKit 主机地址 | ZLM_HOST | string | localhost | ZLMediaKit 主机地址 | ✅ 现有 |
| ZLMediaKit RTMP 端口 | ZLM_RTMP_PORT | int | 1935 | ZLMediaKit RTMP 端口 | ✅ 现有 |
| ZLMediaKit API 地址 | ZLM_API_URL | string | http://localhost:80 | ZLM_API 地址 | ✅ 现有 |
| ZLMediaKit API 密钥 | ZLM_SECRET | string | 035c73f7-bb6b-4889-a715-d9eb2d1925cc | ZLMediaKit API 密钥 | ✅ 现有 |
| ZLMediaKit RTSP 端口 | ZLM_RTSP_PORT | int | 554 | ZLMediaKit RTSP 端口 | ✅ 现有 |
| ZLMediaKit HTTP-FLV 端口 | ZLM_HTTP_FLV_PORT | int | 80 | ZLMediaKit HTTP-FLV 端口 | ✅ 现有 |
| 是否启用 ZLMediaKit Hook | ZLM_HOOK_ENABLE | bool | True | 是否启用 ZLMediaKit Hook | ✅ 现有 |
| 允许推流的 IP 地址 | ZLM_ALLOWED_PUSH_IPS | list | ["127.0.0.1", "192.168.1.0/24"] | 允许推流的 IP 地址 | ✅ 现有 |

#### 3.1.6 存储配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 存储类型 | STORAGE_TYPE | string | local | 存储类型: local / minio / oss | ✅ 现有 |
| 本地存储路径 | LOCAL_STORAGE_PATH | string | ./data | 本地存储路径 | ✅ 现有 |
| MinIO 服务地址 | MINIO_ENDPOINT | string | localhost:9000 | MinIO 服务地址 | ✅ 现有 |
| MinIO Access Key | MINIO_ACCESS_KEY | string | "" | MinIO Access Key | ✅ 现有 |
| MinIO Secret Key | MINIO_SECRET_KEY | string | "" | MinIO Secret Key | ✅ 现有 |
| MinIO 存储桶名称 | MINIO_BUCKET | string | ai-vision | MinIO 存储桶名称 | ✅ 现有 |
| MinIO 是否使用 HTTPS | MINIO_SECURE | bool | False | MinIO 是否使用 HTTPS | ✅ 现有 |

#### 3.1.7 日志配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 日志级别 | LOG_LEVEL | string | INFO | 日志级别: DEBUG / INFO / WARNING / ERROR | ✅ 现有 |
| 日志文件目录 | LOG_PATH | string | ./logs | 日志文件目录 | ✅ 现有 |
| 日志轮转时间 | LOG_ROTATION | string | 00:00 | 日志轮转时间 | ✅ 现有 |
| 日志保留时间 | LOG_RETENTION | string | 30 days | 日志保留时间 | ✅ 现有 |

### 3.2 可以迁移到数据库的配置

#### 3.2.1 API 配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| API 路由前缀 | API_V1_PREFIX | string | /api/v1 | API 路由前缀 | ✅ 现有 |
| 允许跨域的前端地址 | CORS_ORIGINS | list | ["http://localhost:5173", "http://127.0.0.1:5173"] | 允许跨域的前端地址 | ✅ 现有 |

#### 3.2.2 引擎配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 引擎配置更新 Redis 频道 | ENGINE_REDIS_CHANNEL | string | engine:config_update | 引擎配置更新 Redis 频道 | ✅ 现有 |
| 默认推理 Worker 数量 | DEFAULT_INFERENCE_WORKERS | int | 4 | 默认推理 Worker 数量 | ✅ 现有 |
| 帧队列最大长度 | MAX_FRAME_QUEUE_SIZE | int | 30 | 帧队列最大长度 | ✅ 现有 |
| 结果队列最大长度 | MAX_RESULT_QUEUE_SIZE | int | 100 | 结果队列最大长度 | ✅ 现有 |
| 是否将推理绘框图保存到本地 | TEST_SAVE_DRAW | bool | False | 是否将推理绘框图保存到本地用于验证 | ✅ 现有 |
| 测试绘框图保存目录 | TEST_SAVE_DRAW_DIR | string | "" | 测试绘框图保存目录 | ✅ 现有 |
| 是否在 StreamWriter 推流时实时绘框 | ENGINE_STREAM_DRAW_BOXES | bool | False | 是否在 StreamWriter 推流时实时绘框 | ✅ 现有 |
| 推流实时绘框结果过期时间 | ENGINE_STREAM_DRAW_TTL_SEC | float | 2.0 | 推流实时绘框结果过期时间（秒） | ✅ 现有 |
| 调试：由 StreamReader 直接用 FFmpeg 推流 | ENGINE_DEBUG_READER_OPENCV_PUSH | bool | False | 调试：由 StreamReader 直接用 FFmpeg 推流 | ✅ 现有 |
| FFmpeg 可执行文件路径 | FFMPEG_PATH | string | "" | FFmpeg 可执行文件路径或所在目录 | ✅ 现有 |
| ffprobe 可执行文件路径 | FFPROBE_PATH | string | "" | ffprobe 可执行文件路径或所在目录 | ✅ 现有 |

#### 3.2.3 告警消费者配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 告警消费者 Worker 数量 | ALARM_CONSUMER_WORKERS | int | 4 | 告警消费者 Worker 数量 | ✅ 现有 |
| 告警队列名称 | ALARM_QUEUE_NAME | string | alarm_queue | 告警队列名称 | ✅ 现有 |

#### 3.2.4 推送/通知配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 推送任务队列名称 | NOTIFICATION_QUEUE_NAME | string | notification_queue | 推送任务队列名称（Redis list） | ✅ 现有 |
| 推送消费者 Worker 数量 | NOTIFICATION_CONSUMER_WORKERS | int | 2 | 推送消费者 Worker 数量 | ✅ 现有 |
| 通知配置加密密钥 | NOTIFICATION_ENCRYPTION_KEY | string | "" | 通知配置加密密钥（Fernet） | ✅ 现有 |

### 3.3 建议增加的配置（数据库存储）

#### 3.3.1 系统功能配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 系统名称 | system.name | string | AI 视觉管理平台 | 系统显示名称 | ⭐ 建议 |
| 系统描述 | system.description | string | AI 视觉智能监控平台 | 系统描述信息 | ⭐ 建议 |
| 系统Logo | system.logo | string | /static/logo.png | 系统Logo路径 | ⭐ 建议 |
| 系统主题 | system.theme | string | light | 系统默认主题（light/dark） | ⭐ 建议 |
| 系统语言 | system.language | string | zh-CN | 系统默认语言 | ⭐ 建议 |
| 系统时区 | system.timezone | string | Asia/Shanghai | 系统默认时区 | ⭐ 建议 |
| 系统维护模式 | system.maintenance_mode | boolean | false | 系统维护模式开关 | ⭐ 建议 |
| 系统维护提示 | system.maintenance_message | string | 系统维护中，请稍后访问 | 维护模式提示信息 | ⭐ 建议 |

#### 3.3.2 推送通知配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 默认推送渠道 | push.default_channel | string | - | 默认推送渠道ID | ⭐ 建议 |
| 推送重试次数 | push.retry_count | int | 3 | 推送失败重试次数 | ⭐ 建议 |
| 推送重试间隔 | push.retry_interval | int | 5 | 推送重试间隔（秒） | ⭐ 建议 |
| 推送超时时间 | push.timeout | int | 30 | 推送请求超时时间（秒） | ⭐ 建议 |
| 告警保留天数 | push.alarm_retention_days | int | 30 | 告警数据保留天数 | ⭐ 建议 |
| 消息保留天数 | push.message_retention_days | int | 7 | 消息数据保留天数 | ⭐ 建议 |

#### 3.3.3 视频监控配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 默认视频质量 | video.default_quality | string | 720p | 默认视频质量（360p/720p/1080p） | ⭐ 建议 |
| 视频流超时 | video.stream_timeout | int | 60 | 视频流连接超时时间（秒） | ⭐ 建议 |
| 最大并发流 | video.max_concurrent_streams | int | 10 | 最大并发视频流数量 | ⭐ 建议 |
| 视频录制开关 | video.enable_recording | boolean | false | 是否启用视频录制 | ⭐ 建议 |
| 录制存储路径 | video.recording_path | string | ./recordings | 视频录制存储路径 | ⭐ 建议 |
| 录制保留天数 | video.recording_retention_days | int | 7 | 录制文件保留天数 | ⭐ 建议 |

#### 3.3.4 算法推理配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 默认置信度阈值 | algorithm.default_confidence | float | 0.5 | 默认检测置信度阈值（0-1） | ⭐ 建议 |
| 推理间隔秒数 | algorithm.inference_interval | int | 5 | 推理间隔时间（秒） | ⭐ 建议 |
| 最大推理并发数 | algorithm.max_inference_concurrent | int | 5 | 最大并发推理任务数 | ⭐ 建议 |
| 推理超时时间 | algorithm.inference_timeout | int | 30 | 单次推理超时时间（秒） | ⭐ 建议 |
| 结果缓存时间 | algorithm.result_cache_seconds | int | 60 | 推理结果缓存时间（秒） | ⭐ 建议 |

#### 3.3.5 告警管理配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 告警级别阈值 | alarm.level_threshold | json | {"low":0.3,"medium":0.5,"high":0.8} | 告警级别判定阈值 | ⭐ 建议 |
| 告警去重时间 | alarm.deduplication_seconds | int | 60 | 告警去重时间窗口（秒） | ⭐ 建议 |
| 告警自动确认时间 | alarm.auto_confirm_seconds | int | 300 | 告警自动确认时间（秒） | ⭐ 建议 |
| 告警升级时间 | alarm.escalation_minutes | int | 30 | 告警升级时间（分钟） | ⭐ 建议 |
| 告警统计时间范围 | alarm.stats_time_range | int | 24 | 告警统计时间范围（小时） | ⭐ 建议 |

#### 3.3.6 用户和权限配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 默认用户角色 | user.default_role | string | user | 新用户默认角色ID | ⭐ 建议 |
| 密码最小长度 | user.password_min_length | int | 6 | 密码最小长度 | ⭐ 建议 |
| 密码复杂度要求 | user.password_complexity | boolean | true | 是否要求密码复杂度 | ⭐ 建议 |
| 登录失败锁定次数 | user.login_lock_attempts | int | 5 | 登录失败锁定次数 | ⭐ 建议 |
| 账号锁定时间 | user.lock_minutes | int | 30 | 账号锁定时间（分钟） | ⭐ 建议 |
| Token有效期 | user.token_expire_minutes | int | 1440 | 用户Token有效期（分钟） | ⭐ 建议 |

#### 3.3.7 系统性能配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 分页默认大小 | pagination.default_size | int | 20 | 分页默认每页数量 | ⭐ 建议 |
| 分页最大大小 | pagination.max_size | int | 100 | 分页最大每页数量 | ⭐ 建议 |
| API限流窗口 | api.rate_limit_window | int | 60 | API限流时间窗口（秒） | ⭐ 建议 |
| API限流次数 | api.rate_limit_count | int | 100 | API限流请求次数 | ⭐ 建议 |
| 缓存过期时间 | cache.expire_seconds | int | 3600 | 默认缓存过期时间（秒） | ⭐ 建议 |
| 异步任务超时 | async_task_timeout | int | 300 | 异步任务超时时间（秒） | ⭐ 建议 |

#### 3.3.8 UI和界面配置
| 配置项 | 配置Key | 数据类型 | 默认值 | 描述 | 状态 |
|-------|---------|---------|---------|------|------|
| 页面标题 | ui.page_title | string | AI 视觉管理平台 | 页面标题 | ⭐ 建议 |
| 页面Logo | ui.page_logo | string | /static/logo.png | 页面Logo路径 | ⭐ 建议 |
| 默认主题 | ui.default_theme | string | light | 默认界面主题 | ⭐ 建议 |
| 支持的主题 | ui.available_themes | json | ["light","dark"] | 支持的主题列表 | ⭐ 建议 |
| 侧边栏宽度 | ui.sidebar_width | int | 240 | 侧边栏宽度（像素） | ⭐ 建议 |
| 表格行高 | ui.table_row_height | int | 48 | 表格行高（像素） | ⭐ 建议 |

## 4. 数据库表设计

### 4.1 系统配置表（sys_config）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 配置ID（UUID） |
| config_key | VARCHAR | 100 | UNIQUE NOT NULL | 配置键 |
| config_value | TEXT | - | NOT NULL | 配置值（JSON格式） |
| config_type | VARCHAR | 20 | NOT NULL | 配置类型（string/int/float/boolean/json） |
| category | VARCHAR | 50 | NOT NULL | 配置分类 |
| description | VARCHAR | 255 | NULL | 配置描述 |
| is_system | BOOLEAN | - | NOT NULL DEFAULT false | 是否为系统配置 |
| is_public | BOOLEAN | - | NOT NULL DEFAULT false | 是否为公开配置 |
| sort_order | INT | - | NOT NULL DEFAULT 0 | 排序字段 |
| created_by | VARCHAR | 36 | NULL | 创建人ID |
| updated_by | VARCHAR | 36 | NULL | 更新人ID |
| created_at | DATETIME | - | NOT NULL | 创建时间 |
| updated_at | DATETIME | - | NOT NULL | 更新时间 |

### 4.2 配置变更记录表（sys_config_history）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 记录ID（UUID） |
| config_id | VARCHAR | 36 | NOT NULL | 配置ID |
| old_value | TEXT | - | NULL | 修改前的值 |
| new_value | TEXT | - | NOT NULL | 修改后的值 |
| change_reason | VARCHAR | 500 | NULL | 修改原因 |
| operator_id | VARCHAR | 36 | NOT NULL | 操作人ID |
| operator_name | VARCHAR | 100 | NOT NULL | 操作人姓名 |
| created_at | DATETIME | - | NOT NULL | 创建时间 |

## 5. 配置管理API设计

### 5.1 配置查询接口
```python
# 获取所有配置
GET /api/configs

# 获取指定分类的配置
GET /api/configs?category=system

# 获取单个配置
GET /api/configs/{config_key}

# 获取公开配置（无需认证）
GET /api/configs/public
```

### 5.2 配置管理接口
```python
# 更新配置
PUT /api/configs/{config_key}

# 批量更新配置
PUT /api/configs/batch

# 重置配置为默认值
POST /api/configs/{config_key}/reset

# 获取配置变更历史
GET /api/configs/{config_key}/history
```

### 5.3 配置缓存策略
```python
# 配置缓存
- 使用Redis缓存配置信息
- 缓存时间：5分钟
- 配置更新时自动清除缓存
- 支持手动刷新缓存

# 配置预热
- 系统启动时加载常用配置到缓存
- 定期刷新热点配置
- 支持配置变更通知
```

## 6. 配置迁移策略

### 6.1 迁移原则
1. **渐进式迁移**：先迁移非核心配置，逐步迁移所有可迁移配置
2. **兼容性保证**：保留.env配置的读取逻辑，优先使用数据库配置
3. **回滚机制**：支持快速回滚到.env配置模式
4. **监控验证**：密切监控配置迁移后的系统稳定性

### 6.2 迁移步骤
1. **第一阶段**：迁移引擎配置
   - DEFAULT_INFERENCE_WORKERS、MAX_FRAME_QUEUE_SIZE等
   - 验证配置读取和更新功能

2. **第二阶段**：迁移API和告警配置
   - API_V1_PREFIX、CORS_ORIGINS、ALARM_CONSUMER_WORKERS等
   - 验证动态配置调整功能

3. **第三阶段**：迁移推送和通知配置
   - NOTIFICATION_QUEUE_NAME、NOTIFICATION_CONSUMER_WORKERS等
   - 验证系统性能影响

4. **第四阶段**：清理和优化
   - 清理.env中的冗余配置
   - 优化配置管理界面
   - 完善配置文档

## 7. 负载均衡支持

### 7.1 配置同步机制
```python
# 配置同步策略
- 主从配置同步
- 配置变更广播
- 定期配置校验
- 配置冲突解决

# 配置一致性保证
- 配置版本号
- 配置校验和
- 配置变更日志
- 自动配置修复
```

### 7.2 配置热更新
```python
# 配置热更新机制
- WebSocket配置推送
- 配置变更事件
- 实时配置生效
- 配置回滚支持

# 配置更新流程
1. 管理员修改配置
2. 数据库更新配置
3. 清除配置缓存
4. 推送配置变更
5. 各实例更新内存配置
6. 验证配置生效
```

## 8. 安全考虑

### 8.1 配置安全
- 敏感配置必须保留在.env文件
- 配置修改需要权限验证
- 配置变更需要审计日志
- 支持配置备份和恢复

### 8.2 访问控制
- 配置管理需要管理员权限
- 系统配置需要超级管理员权限
- 配置历史记录完整审计
- 支持配置修改审批流程

## 9. 性能优化

### 9.1 配置缓存
- 使用Redis缓存热点配置
- 配置预加载机制
- 智能缓存失效策略
- 配置查询性能监控

### 9.2 配置加载
- 延迟加载非核心配置
- 配置按需加载
- 配置懒加载机制
- 配置加载性能优化

## 10. 监控和告警

### 10.1 配置监控
- 配置变更监控
- 配置生效监控
- 配置性能监控
- 配置异常监控

### 10.2 告警机制
- 配置错误告警
- 配置冲突告警
- 配置性能告警
- 配置安全告警

## 11. 总结

本设计方案实现了配置管理的现代化改造：

1. **分层配置管理**：
   - .env保留基础架构和安全配置
   - 数据库管理业务功能和动态配置
   - 支持动态配置调整

2. **负载均衡支持**：
   - 配置统一管理
   - 配置同步机制
   - 配置热更新
   - 多实例配置一致性

3. **灵活性和可维护性**：
   - 配置分类清晰
   - 配置管理界面友好
   - 配置变更可追溯
   - 支持配置回滚

4. **安全性和稳定性**：
   - 敏感配置保护
   - 配置权限控制
   - 配置变更审计
   - 系统稳定性保证

该方案为系统的负载均衡升级和动态配置管理提供了完整的技术基础。