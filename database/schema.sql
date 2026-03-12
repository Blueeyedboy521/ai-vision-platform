-- =====================================================
-- AI Vision Platform - 数据库表结构
-- 数据库: MySQL 8.0+
-- 字符集: utf8mb4
-- =====================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_vision DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_vision;

-- -----------------------------------------------------
-- 1. 用户与权限
-- -----------------------------------------------------

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id CHAR(32) NOT NULL COMMENT '用户ID (UUID)',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    email VARCHAR(100) DEFAULT NULL COMMENT '邮箱地址',
    real_name VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
    phone VARCHAR(20) DEFAULT NULL COMMENT '手机号码',
    avatar VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
    role VARCHAR(20) DEFAULT 'user' COMMENT '角色: admin-管理员, user-普通用户, viewer-只读用户',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用: 1-启用, 0-禁用',
    last_login_at DATETIME DEFAULT NULL COMMENT '最后登录时间',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username),
    KEY idx_role (role),
    KEY idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 创建默认管理员 (密码: admin123)
INSERT IGNORE INTO users (id, username, password_hash, real_name, role, is_active) 
VALUES ('00000000000000000000000000000001', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYTL0xU5Deaq', '系统管理员', 'admin', 1);

-- -----------------------------------------------------
-- 2. 区域管理
-- -----------------------------------------------------

-- 区域表 (树形结构)
CREATE TABLE IF NOT EXISTS areas (
    id CHAR(32) NOT NULL COMMENT '区域ID (UUID)',
    name VARCHAR(100) NOT NULL COMMENT '区域名称',
    parent_id CHAR(32) DEFAULT NULL COMMENT '父级区域ID',
    level INT DEFAULT 1 COMMENT '层级深度',
    hierarchy_path VARCHAR(500) DEFAULT NULL COMMENT '层级路径（按名称拼接，如 一级/二级/三级）',
    sort_order INT DEFAULT 0 COMMENT '排序序号',
    description TEXT DEFAULT NULL COMMENT '区域描述',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_parent_id (parent_id),
    KEY idx_level (level),
    KEY idx_hierarchy_path (hierarchy_path),
    KEY idx_sort_order (sort_order),
    CONSTRAINT fk_areas_parent FOREIGN KEY (parent_id) REFERENCES areas(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='区域表';

-- 创建默认根区域
INSERT IGNORE INTO areas (id, name, level, description) 
VALUES ('00000000000000000000000000000001', '默认区域', 1, '系统默认区域');

-- -----------------------------------------------------
-- 3. 摄像头管理
-- -----------------------------------------------------

-- 摄像头表
CREATE TABLE IF NOT EXISTS cameras (
    id CHAR(32) NOT NULL COMMENT '摄像头ID (UUID)',
    name VARCHAR(100) NOT NULL COMMENT '摄像头名称',
    code VARCHAR(50) NOT NULL COMMENT '摄像头编码 (唯一)',
    area_id CHAR(32) DEFAULT NULL COMMENT '所属区域ID',
    rtsp_url VARCHAR(500) NOT NULL COMMENT 'RTSP拉流地址（可含认证）',
    stream_url VARCHAR(500) DEFAULT NULL COMMENT '输出流地址 (ZLMediaKit)',
    resolution VARCHAR(20) DEFAULT NULL COMMENT '分辨率 (如: 1920x1080)',
    fps INT DEFAULT 25 COMMENT '帧率',
    skip_frames INT DEFAULT 5 COMMENT '推理跳帧数',
    status VARCHAR(20) DEFAULT 'offline' COMMENT '状态: online-在线, offline-离线, error-异常',
    last_online_at DATETIME DEFAULT NULL COMMENT '最后在线时间',
    description TEXT DEFAULT NULL COMMENT '摄像头描述',
    location VARCHAR(200) DEFAULT NULL COMMENT '安装位置描述',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用: 1-启用, 0-禁用',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_code (code),
    KEY idx_area_id (area_id),
    KEY idx_status (status),
    KEY idx_is_enabled (is_enabled),
    CONSTRAINT fk_cameras_area FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='摄像头表';

-- -----------------------------------------------------
-- 4. 模型管理
-- -----------------------------------------------------

-- AI 模型表
CREATE TABLE IF NOT EXISTS models (
    id CHAR(32) NOT NULL COMMENT '模型ID (UUID)',
    name VARCHAR(100) NOT NULL COMMENT '模型名称',
    code VARCHAR(50) NOT NULL COMMENT '模型编码 (唯一)',
    model_type VARCHAR(30) NOT NULL COMMENT '模型类型: yolo, onnx, tensorrt, pytorch, custom',
    model_path VARCHAR(500) NOT NULL COMMENT '模型文件路径',
    classes JSON NOT NULL COMMENT '支持的检测类别 (JSON数组)',
    version VARCHAR(20) DEFAULT NULL COMMENT '模型版本号',
    gpu_memory_mb INT DEFAULT NULL COMMENT '预估显存占用 (MB)',
    inference_ms INT DEFAULT NULL COMMENT '预估推理时间 (毫秒)',
    description TEXT DEFAULT NULL COMMENT '模型描述',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用: 1-启用, 0-禁用',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_code (code),
    KEY idx_model_type (model_type),
    KEY idx_is_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI模型表';

-- -----------------------------------------------------
-- 5. 算法/检测能力管理
-- -----------------------------------------------------

-- 检测能力表 (业务检测场景)
CREATE TABLE IF NOT EXISTS algorithms (
    id CHAR(32) NOT NULL COMMENT '算法ID (UUID)',
    name VARCHAR(100) NOT NULL COMMENT '算法名称',
    code VARCHAR(50) NOT NULL COMMENT '算法编码 (唯一)',
    model_id CHAR(32) NOT NULL COMMENT '关联模型ID',
    target_classes JSON NOT NULL COMMENT '使用的检测类别 (JSON数组)',
    default_confidence DECIMAL(3,2) DEFAULT 0.50 COMMENT '默认置信度阈值 (0.00-1.00)',
    alert_config JSON DEFAULT NULL COMMENT '告警配置 (JSON对象)',
    description TEXT DEFAULT NULL COMMENT '算法描述',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用: 1-启用, 0-禁用',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_code (code),
    KEY idx_model_id (model_id),
    KEY idx_is_enabled (is_enabled),
    CONSTRAINT fk_algorithms_model FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检测能力/算法表';

-- 告警配置 JSON 结构示例:
-- {
--     "trigger_type": "instant",     -- instant(立即) / duration(持续) / count(计数)
--     "duration_seconds": 0,         -- 持续 N 秒才告警
--     "count_threshold": 0,          -- 检测到 N 个才告警
--     "cooldown_seconds": 30,        -- 告警冷却时间
--     "alert_level": "warning"       -- info / warning / danger
-- }

-- -----------------------------------------------------
-- 6. 摄像头-算法配置
-- -----------------------------------------------------

-- 摄像头算法配置表
CREATE TABLE IF NOT EXISTS camera_algorithms (
    id CHAR(32) NOT NULL COMMENT '配置ID (UUID)',
    camera_id CHAR(32) NOT NULL COMMENT '摄像头ID',
    algorithm_id CHAR(32) NOT NULL COMMENT '算法ID',
    model_id CHAR(32) NOT NULL COMMENT '模型ID (冗余字段，便于查询)',
    confidence DECIMAL(3,2) DEFAULT NULL COMMENT '覆盖置信度阈值 (可选)',
    alert_config JSON DEFAULT NULL COMMENT '覆盖告警配置 (可选, JSON对象)',
    regions JSON DEFAULT NULL COMMENT '检测区域 (JSON数组, 多边形坐标)',
    inference_interval_sec INT NOT NULL DEFAULT 5 COMMENT '识别间隔(秒)',
    alarm_interval_sec INT NOT NULL DEFAULT 30 COMMENT '告警间隔(秒)',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用: 1-启用, 0-禁用',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_camera_algorithm (camera_id, algorithm_id),
    KEY idx_camera_id (camera_id),
    KEY idx_algorithm_id (algorithm_id),
    KEY idx_model_id (model_id),
    KEY idx_is_enabled (is_enabled),
    CONSTRAINT fk_ca_camera FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE,
    CONSTRAINT fk_ca_algorithm FOREIGN KEY (algorithm_id) REFERENCES algorithms(id) ON DELETE CASCADE,
    CONSTRAINT fk_ca_model FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='摄像头-算法配置表';

-- -----------------------------------------------------
-- 7. 告警管理
-- -----------------------------------------------------

-- 告警记录表
CREATE TABLE IF NOT EXISTS alarms (
    id CHAR(32) NOT NULL COMMENT '告警ID (UUID)',
    camera_id CHAR(32) NOT NULL COMMENT '摄像头ID',
    algorithm_id CHAR(32) NOT NULL COMMENT '算法ID',
    title VARCHAR(200) NOT NULL COMMENT '告警标题',
    level VARCHAR(20) DEFAULT 'warning' COMMENT '告警级别: info-提示, warning-警告, danger-危险',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '处理状态: pending-待处理, confirmed-已确认, ignored-已忽略, resolved-已解决',
    image_path VARCHAR(500) DEFAULT NULL COMMENT '告警截图路径',
    video_path VARCHAR(500) DEFAULT NULL COMMENT '告警视频片段路径',
    detection_data JSON DEFAULT NULL COMMENT '检测详情 (JSON对象)',
    confirmed_by CHAR(32) DEFAULT NULL COMMENT '处理人ID',
    confirmed_at DATETIME DEFAULT NULL COMMENT '处理时间',
    remark TEXT DEFAULT NULL COMMENT '处理备注',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID (系统自动创建时为空)',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_camera_id (camera_id),
    KEY idx_algorithm_id (algorithm_id),
    KEY idx_level (level),
    KEY idx_status (status),
    KEY idx_created_at (created_at),
    KEY idx_confirmed_by (confirmed_by),
    CONSTRAINT fk_alarms_camera FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE,
    CONSTRAINT fk_alarms_algorithm FOREIGN KEY (algorithm_id) REFERENCES algorithms(id) ON DELETE CASCADE,
    CONSTRAINT fk_alarms_confirmer FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='告警记录表';

-- -----------------------------------------------------
-- 8. 推送配置
-- -----------------------------------------------------

-- 推送渠道配置表
CREATE TABLE IF NOT EXISTS push_channels (
    id CHAR(32) NOT NULL COMMENT '渠道ID (UUID)',
    name VARCHAR(100) NOT NULL COMMENT '渠道名称',
    type VARCHAR(30) NOT NULL COMMENT '渠道类型: email-邮件, dingtalk-钉钉, wechat-微信, webhook-Webhook',
    config JSON NOT NULL COMMENT '渠道配置 (JSON对象)',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用: 1-启用, 0-禁用',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_type (type),
    KEY idx_is_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送渠道配置表';

-- 推送规则表 (哪些告警推送到哪些渠道)
CREATE TABLE IF NOT EXISTS push_rules (
    id CHAR(32) NOT NULL COMMENT '规则ID (UUID)',
    name VARCHAR(100) NOT NULL COMMENT '规则名称',
    channel_id CHAR(32) NOT NULL COMMENT '推送渠道ID',
    algorithm_ids JSON DEFAULT NULL COMMENT '算法ID列表 (JSON数组, 空表示全部)',
    camera_ids JSON DEFAULT NULL COMMENT '摄像头ID列表 (JSON数组, 空表示全部)',
    alert_levels JSON DEFAULT NULL COMMENT '告警级别列表 (JSON数组)',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用: 1-启用, 0-禁用',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_channel_id (channel_id),
    KEY idx_is_enabled (is_enabled),
    CONSTRAINT fk_rules_channel FOREIGN KEY (channel_id) REFERENCES push_channels(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送规则表';

-- -----------------------------------------------------
-- 8.1 新推送体系（Endpoint / Template / Policy / DeliveryLog）
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS notification_endpoints (
    id CHAR(32) NOT NULL COMMENT '通道ID (UUID)',
    name VARCHAR(100) NOT NULL COMMENT '通道名称',
    provider VARCHAR(32) NOT NULL COMMENT 'provider: wecom_bot/dingtalk_bot',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用: 1-启用, 0-禁用',
    encrypted_config TEXT NOT NULL COMMENT '加密配置（Fernet）',
    config_hint VARCHAR(255) DEFAULT NULL COMMENT '配置提示（脱敏）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_provider (provider),
    KEY idx_is_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送通道配置';

CREATE TABLE IF NOT EXISTS notification_templates (
    id CHAR(32) NOT NULL COMMENT '模板ID (UUID)',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    type VARCHAR(16) NOT NULL COMMENT 'text/rich',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    content JSON NOT NULL COMMENT '模板内容 JSON（title/text/image_url/link_url 等）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_type (type),
    KEY idx_is_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送模板';

CREATE TABLE IF NOT EXISTS notification_policies (
    id CHAR(32) NOT NULL COMMENT '策略ID (UUID)',
    name VARCHAR(100) NOT NULL COMMENT '策略名称',
    priority INT DEFAULT 100 COMMENT '优先级（小优先）',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `match` JSON NOT NULL COMMENT '匹配条件 JSON（支持多选/通配符/exclude/time_window 等）',
    actions JSON NOT NULL COMMENT '动作 JSON（actions 数组：endpoint_ids/template_id/throttle/dedup/retry 等）',
    match_desc TEXT DEFAULT NULL COMMENT '匹配条件中文描述（冗余）',
    actions_desc TEXT DEFAULT NULL COMMENT '动作中文描述（冗余）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_priority (priority),
    KEY idx_is_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送路由策略';

CREATE TABLE IF NOT EXISTS notification_delivery_logs (
    id CHAR(32) NOT NULL COMMENT '投递日志ID (UUID)',
    alarm_id CHAR(32) DEFAULT NULL COMMENT '告警ID（业务告警）',
    category VARCHAR(16) NOT NULL COMMENT 'ai/system',
    alarm_type VARCHAR(64) NOT NULL COMMENT '告警类型/系统类型',
    level VARCHAR(16) NOT NULL COMMENT 'info/warning/danger/critical',
    endpoint_id CHAR(32) NOT NULL COMMENT 'endpoint_id',
    provider VARCHAR(32) NOT NULL COMMENT 'provider',
    template_id CHAR(32) DEFAULT NULL COMMENT 'template_id',
    status VARCHAR(16) NOT NULL COMMENT 'success/failed/skipped',
    error TEXT DEFAULT NULL COMMENT '错误（脱敏）',
    request_meta JSON DEFAULT NULL COMMENT '请求元信息（脱敏）',
    response_meta JSON DEFAULT NULL COMMENT '响应元信息（脱敏）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_alarm_id (alarm_id),
    KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送审计日志';

-- -----------------------------------------------------
-- 9. 系统配置
-- -----------------------------------------------------

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id CHAR(32) NOT NULL COMMENT '配置ID (UUID)',
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT DEFAULT NULL COMMENT '配置值',
    description VARCHAR(500) DEFAULT NULL COMMENT '配置描述',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 插入默认系统配置
INSERT IGNORE INTO system_configs (id, config_key, config_value, description) VALUES
('00000000000000000000000000000001', 'site_name', 'AI Vision Platform', '站点名称'),
('00000000000000000000000000000002', 'alarm_retention_days', '90', '告警记录保留天数'),
('00000000000000000000000000000003', 'video_clip_duration', '10', '告警视频片段时长(秒)'),
('00000000000000000000000000000004', 'websocket_heartbeat', '30', 'WebSocket心跳间隔(秒)'),
('00000000000000000000000000000005', 'stream_server_url', 'http://localhost:8080', '流媒体服务器地址');

-- -----------------------------------------------------
-- 10. 操作日志
-- -----------------------------------------------------

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id CHAR(32) NOT NULL COMMENT '日志ID (UUID)',
    user_id CHAR(32) DEFAULT NULL COMMENT '操作用户ID',
    username VARCHAR(50) DEFAULT NULL COMMENT '操作用户名',
    action VARCHAR(50) NOT NULL COMMENT '操作类型: create-创建, update-更新, delete-删除, login-登录, logout-登出',
    resource_type VARCHAR(50) DEFAULT NULL COMMENT '资源类型: camera, model, algorithm, alarm等',
    resource_id CHAR(32) DEFAULT NULL COMMENT '资源ID',
    resource_name VARCHAR(200) DEFAULT NULL COMMENT '资源名称',
    detail JSON DEFAULT NULL COMMENT '操作详情 (JSON对象)',
    ip_address VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
    user_agent VARCHAR(500) DEFAULT NULL COMMENT '用户代理',
    created_by CHAR(32) DEFAULT NULL COMMENT '创建人ID',
    updated_by CHAR(32) DEFAULT NULL COMMENT '更新人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_user_id (user_id),
    KEY idx_action (action),
    KEY idx_resource_type (resource_type),
    KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- -----------------------------------------------------
-- 示例数据 (开发测试用)
-- -----------------------------------------------------

-- 示例模型
INSERT IGNORE INTO models (id, name, code, model_type, model_path, classes, gpu_memory_mb, inference_ms, description) VALUES
('10000000000000000000000000000001', '安全生产检测模型', 'yolo_safety_v1', 'yolo', 'models/yolo_safety_v1.pt', '["person", "helmet", "no_helmet", "vest", "no_vest"]', 500, 30, '检测人员、安全帽、反光衣'),
('10000000000000000000000000000002', '烟火检测模型', 'fire_smoke_v1', 'yolo', 'models/fire_smoke_v1.pt', '["fire", "smoke"]', 300, 25, '检测明火和烟雾');

-- 示例算法
INSERT IGNORE INTO algorithms (id, name, code, model_id, target_classes, default_confidence, alert_config) VALUES
('20000000000000000000000000000001', '人员入侵检测', 'person_intrusion', '10000000000000000000000000000001', '["person"]', 0.50, '{"trigger_type": "instant", "cooldown_seconds": 30, "alert_level": "danger"}'),
('20000000000000000000000000000002', '安全帽检测', 'helmet_detection', '10000000000000000000000000000001', '["no_helmet"]', 0.60, '{"trigger_type": "duration", "duration_seconds": 3, "cooldown_seconds": 60, "alert_level": "danger"}'),
('20000000000000000000000000000003', '反光衣检测', 'vest_detection', '10000000000000000000000000000001', '["no_vest"]', 0.60, '{"trigger_type": "instant", "cooldown_seconds": 60, "alert_level": "warning"}'),
('20000000000000000000000000000004', '烟火检测', 'fire_detection', '10000000000000000000000000000002', '["fire", "smoke"]', 0.50, '{"trigger_type": "instant", "cooldown_seconds": 30, "alert_level": "danger"}');

-- 示例摄像头
INSERT IGNORE INTO cameras (id, name, code, area_id, rtsp_url, status) VALUES
('30000000000000000000000000000001', '车间入口摄像头-01', 'CAM001', '00000000000000000000000000000001', 'rtsp://admin:admin123@192.168.1.100:554/stream1', 'offline'),
('30000000000000000000000000000002', '车间出口摄像头-02', 'CAM002', '00000000000000000000000000000001', 'rtsp://admin:admin123@192.168.1.101:554/stream1', 'offline');

-- 示例摄像头算法配置
INSERT IGNORE INTO camera_algorithms (id, camera_id, algorithm_id, model_id, confidence, is_enabled) VALUES
('40000000000000000000000000000001', '30000000000000000000000000000001', '20000000000000000000000000000001', '10000000000000000000000000000001', NULL, 1),
('40000000000000000000000000000002', '30000000000000000000000000000001', '20000000000000000000000000000002', '10000000000000000000000000000001', 0.70, 1),
('40000000000000000000000000000003', '30000000000000000000000000000002', '20000000000000000000000000000001', '10000000000000000000000000000001', NULL, 1),
('40000000000000000000000000000004', '30000000000000000000000000000002', '20000000000000000000000000000004', '10000000000000000000000000000002', NULL, 1);
