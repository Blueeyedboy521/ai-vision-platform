# -*- coding: utf-8 -*-
"""
告警消费者

处理从 Redis 队列中获取的告警消息
"""
import json
from datetime import datetime
from typing import Optional

import redis

from common.logging import logger
from common.notification import get_notifiers, NotificationMessage
from common.storage import get_storage
from common.redis.channels import RedisChannels
from config.settings import settings


def process_alarm(alarm_data: dict) -> None:
    """
    处理告警消息
    
    执行以下操作:
    1. 保存告警到数据库
    2. 发送通知 (高级别告警)
    3. 发布实时告警事件 (WebSocket)
    
    Args:
        alarm_data: 告警数据
    """
    alarm_id = alarm_data.get("alarm_id")
    camera_id = alarm_data.get("camera_id")
    alert_level = alarm_data.get("alert_level", "info")
    
    logger.info(
        f"处理告警: alarm_id={alarm_id}, "
        f"camera_id={camera_id}, "
        f"level={alert_level}"
    )
    
    # 1. 保存到数据库
    try:
        save_alarm_to_db(alarm_data)
    except Exception as e:
        logger.error(f"保存告警到数据库失败: {e}")
    
    # 2. 发送通知 (高级别告警)
    if alert_level in ("high", "danger", "critical"):
        try:
            send_notifications(alarm_data)
        except Exception as e:
            logger.error(f"发送告警通知失败: {e}")
    
    # 3. 发布实时告警事件
    try:
        publish_realtime_alarm(alarm_data)
    except Exception as e:
        logger.error(f"发布实时告警失败: {e}")


def save_alarm_to_db(alarm_data: dict) -> None:
    """
    保存告警到数据库
    
    Args:
        alarm_data: 告警数据
    """
    from app.core.database import get_sync_db_session
    from app.models import Alarm
    from app.models.base import generate_uuid
    
    with get_sync_db_session() as session:
        # 检查是否已存在 (防止重复处理)
        alarm_id = alarm_data.get("alarm_id")
        if alarm_id:
            existing = session.query(Alarm).filter(
                Alarm.id == alarm_id
            ).first()
            if existing:
                logger.debug(f"告警已存在，跳过: {alarm_id}")
                return
        else:
            alarm_id = generate_uuid()
        
        # 创建告警记录
        alarm = Alarm(
            id=alarm_id,
            camera_id=alarm_data.get("camera_id"),
            algorithm_id=alarm_data.get("algorithm_id"),
            alarm_type=alarm_data.get("alarm_type", "detection"),
            level=_map_alert_level(alarm_data.get("alert_level", "info")),
            title=alarm_data.get("title"),
            description=alarm_data.get("description"),
            alarm_time=datetime.fromisoformat(
                alarm_data.get("timestamp", datetime.now().isoformat())
            ),
            snapshot_url=alarm_data.get("snapshot_path"),
            detection_data=alarm_data.get("detections", [])
        )
        
        session.add(alarm)
        session.commit()
        
        logger.info(f"告警已保存: {alarm_id}")


def _map_alert_level(level: str) -> str:
    """
    映射告警级别
    
    Args:
        level: 原始级别
        
    Returns:
        标准化级别
    """
    level_map = {
        "info": "info",
        "low": "info",
        "warning": "warning",
        "medium": "warning",
        "danger": "danger",
        "high": "danger",
        "critical": "critical"
    }
    return level_map.get(level.lower(), "info")


def send_notifications(alarm_data: dict) -> None:
    """
    发送告警通知
    
    根据配置的通知渠道发送通知
    
    Args:
        alarm_data: 告警数据
    """
    notifiers = get_notifiers()
    
    if not notifiers:
        logger.debug("没有配置通知渠道，跳过通知发送")
        return
    
    # 创建通知消息
    message = NotificationMessage.from_alarm(alarm_data)
    
    # 发送到所有通知渠道
    success_channels = []
    
    for notifier in notifiers:
        if not notifier.is_enabled():
            continue
        
        try:
            # 使用同步方法发送
            success = notifier.send_sync(message)
            if success:
                success_channels.append(notifier.name)
        except Exception as e:
            logger.error(f"通知发送失败 [{notifier.name}]: {e}")
    
    if success_channels:
        logger.info(
            f"告警通知已发送: alarm_id={alarm_data.get('alarm_id')}, "
            f"渠道={','.join(success_channels)}"
        )
        
        # 更新数据库中的推送状态
        _update_push_status(
            alarm_data.get("alarm_id"),
            success_channels
        )


def _update_push_status(
    alarm_id: Optional[str],
    channels: list
) -> None:
    """
    更新告警推送状态
    
    Args:
        alarm_id: 告警ID
        channels: 已推送的渠道
    """
    if not alarm_id:
        return
    
    from app.core.database import get_sync_db_session
    from app.models import Alarm
    
    try:
        with get_sync_db_session() as session:
            alarm = session.query(Alarm).filter(
                Alarm.id == alarm_id
            ).first()
            
            if alarm:
                alarm.is_pushed = True
                alarm.push_channels = ",".join(channels)
                session.commit()
    except Exception as e:
        logger.error(f"更新推送状态失败: {e}")


def publish_realtime_alarm(alarm_data: dict) -> None:
    """
    发布实时告警事件
    
    通过 Redis Pub/Sub 发布到 WebSocket 处理器
    
    Args:
        alarm_data: 告警数据
    """
    # 创建同步 Redis 客户端
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )
    
    try:
        # 构建发布消息
        message = {
            "type": "new_alarm",
            "alarm_id": alarm_data.get("alarm_id"),
            "camera_id": alarm_data.get("camera_id"),
            "camera_name": alarm_data.get("camera_name"),
            "algorithm_id": alarm_data.get("algorithm_id"),
            "algorithm_name": alarm_data.get("algorithm_name"),
            "level": alarm_data.get("alert_level", "info"),
            "title": alarm_data.get("title"),
            "timestamp": alarm_data.get("timestamp"),
            "snapshot_path": alarm_data.get("snapshot_path")
        }
        
        redis_client.publish(
            RedisChannels.ALARMS_REALTIME,
            json.dumps(message, ensure_ascii=False)
        )
        
        logger.debug(f"实时告警已发布: {alarm_data.get('alarm_id')}")
        
    finally:
        redis_client.close()
