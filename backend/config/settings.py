# -*- coding: utf-8 -*-
"""
全局配置模块

使用 Pydantic Settings 管理配置，支持环境变量和 .env 文件
"""
import os
from typing import List, Optional
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger

class Settings(BaseSettings):
    """
    全局配置类
    
    配置优先级: 环境变量 > .env 文件 > 默认值
    """
    # 打印初始化日志
    logger.info("初始化配置...")
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # ==================== 基础配置 ====================
    PROJECT_NAME: str = Field(
        default="AI Vision Platform",
        description="项目名称"
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="运行环境: development / production / testing"
    )
    DEBUG: bool = Field(
        default=True,
        description="是否开启调试模式"
    )
    
    # ==================== API 配置 ====================
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API 路由前缀"
    )
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="允许跨域的前端地址"
    )
    
    # ==================== 数据库配置 ====================
    DATABASE_URL: str = Field(
        default="mysql+aiomysql://root:root@localhost:3306/ai_vision",
        description="数据库连接URL"
    )
    DB_POOL_SIZE: int = Field(
        default=10,
        description="数据库连接池大小"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=20,
        description="数据库连接池最大溢出数"
    )
    DB_POOL_RECYCLE: int = Field(
        default=3600,
        description="数据库连接回收时间(秒)"
    )
    
    # ==================== Redis 配置 ====================
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 连接URL"
    )
    REDIS_MAX_CONNECTIONS: int = Field(
        default=50,
        description="Redis 最大连接数"
    )
    
    # ==================== JWT 认证配置 ====================
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production-environment",
        description="JWT 密钥，生产环境必须修改"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT 加密算法"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24,
        description="Access Token 有效期(分钟)，默认24小时"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh Token 有效期(天)，默认7天"
    )
    
    # ==================== ZLMediaKit 流媒体配置 ====================
    ZLM_HOST: str = Field(
        default="localhost",
        description="ZLMediaKit 主机地址"
    )
    ZLM_RTMP_PORT: int = Field(
        default=1935,
        description="ZLMediaKit 端口"
    )
    ZLM_API_URL: str = Field(
        default="http://localhost:80",
        description="ZLMediaKit API 地址"
    )
    ZLM_SECRET: str = Field(
        default="035c73f7-bb6b-4889-a715-d9eb2d1925cc",
        description="ZLMediaKit API 密钥"
    )
    ZLM_RTMP_PORT: int = Field(
        default=1935,
        description="ZLMediaKit RTMP 端口"
    )
    ZLM_RTSP_PORT: int = Field(
        default=554,
        description="ZLMediaKit RTSP 端口"
    )
    ZLM_HTTP_FLV_PORT: int = Field(
        default=80,
        description="ZLMediaKit HTTP-FLV 端口"
    )
    ZLM_HOOK_ENABLE: bool = Field(
        default=True,
        description="是否启用 ZLMediaKit Hook"
    )
    ZLM_ALLOWED_PUSH_IPS: List[str] = Field(
        default=["127.0.0.1", "192.168.1.0/24"],
        description="允许推流的 IP 地址"
    )
    
    # ==================== 引擎配置 ====================
    ENGINE_REDIS_CHANNEL: str = Field(
        default="engine:config_update",
        description="引擎配置更新 Redis 频道"
    )
    DEFAULT_INFERENCE_WORKERS: int = Field(
        default=4,
        description="默认推理 Worker 数量"
    )
    MAX_FRAME_QUEUE_SIZE: int = Field(
        default=30,
        description="帧队列最大长度"
    )
    MAX_RESULT_QUEUE_SIZE: int = Field(
        default=100,
        description="结果队列最大长度"
    )
    TEST_SAVE_DRAW: bool = Field(
        default=False,
        description="是否将推理绘框图保存到本地用于验证（Worker 中调用 draw_boxes 并保存）"
    )
    TEST_SAVE_DRAW_DIR: str = Field(
        default="",
        description="测试绘框图保存目录，如 G:/ai/temp；TEST_SAVE_DRAW 为 True 时生效"
    )
    ENGINE_STREAM_DRAW_BOXES: bool = Field(
        default=False,
        description="是否在 StreamWriter 推流时实时绘框（方案A：用最新推理结果覆盖后续帧，允许拖影）"
    )
    ENGINE_STREAM_DRAW_TTL_SEC: float = Field(
        default=2.0,
        description="推流实时绘框结果过期时间（秒）。超过该时间未收到新推理结果，则不再绘制"
    )

    # ==================== 存储配置 ====================
    STORAGE_TYPE: str = Field(
        default="local",
        description="存储类型: local / minio / oss"
    )
    LOCAL_STORAGE_PATH: str = Field(
        default="./data",
        description="本地存储路径"
    )
    MINIO_ENDPOINT: str = Field(
        default="localhost:9000",
        description="MinIO 服务地址"
    )
    MINIO_ACCESS_KEY: str = Field(
        default="",
        description="MinIO Access Key"
    )
    MINIO_SECRET_KEY: str = Field(
        default="",
        description="MinIO Secret Key"
    )
    MINIO_BUCKET: str = Field(
        default="ai-vision",
        description="MinIO 存储桶名称"
    )
    MINIO_SECURE: bool = Field(
        default=False,
        description="MinIO 是否使用 HTTPS"
    )
    
    # ==================== 告警消费者配置 ====================
    ALARM_CONSUMER_WORKERS: int = Field(
        default=4,
        description="告警消费者 Worker 数量"
    )
    ALARM_QUEUE_NAME: str = Field(
        default="alarm_queue",
        description="告警队列名称"
    )
    
    # ==================== 通知配置 ====================
    # 钉钉机器人
    DINGTALK_WEBHOOK_URL: str = Field(
        default="",
        description="钉钉机器人 Webhook URL"
    )
    DINGTALK_SECRET: str = Field(
        default="",
        description="钉钉机器人签名密钥"
    )
    
    # 邮件配置
    SMTP_HOST: str = Field(
        default="smtp.qq.com",
        description="SMTP 服务器地址"
    )
    SMTP_PORT: int = Field(
        default=465,
        description="SMTP 端口"
    )
    SMTP_USER: str = Field(
        default="",
        description="SMTP 用户名"
    )
    SMTP_PASSWORD: str = Field(
        default="",
        description="SMTP 密码"
    )
    SMTP_FROM: str = Field(
        default="",
        description="发件人地址"
    )
    SMTP_USE_SSL: bool = Field(
        default=True,
        description="是否使用 SSL"
    )
    
    # ==================== 日志配置 ====================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="日志级别: DEBUG / INFO / WARNING / ERROR"
    )
    LOG_PATH: str = Field(
        default="./logs",
        description="日志文件目录"
    )
    LOG_ROTATION: str = Field(
        default="00:00",
        description="日志轮转时间"
    )
    LOG_RETENTION: str = Field(
        default="30 days",
        description="日志保留时间"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS_ORIGINS，支持 JSON 数组或逗号分隔的字符串"""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @field_validator("ZLM_ALLOWED_PUSH_IPS", mode="before")
    @classmethod
    def parse_allowed_ips(cls, v):
        """解析允许推流的 IP 列表"""
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",") if ip.strip()]
        return v
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例
    
    使用 lru_cache 确保只创建一次实例
    """
    config = Settings()
    logger.info(f"配置初始化完成: {config}")
    return config


# 全局配置实例
settings = get_settings()
