# -*- coding: utf-8 -*-
"""
告警消费者

处理从 Redis 队列中获取的告警消息
"""
import json
from datetime import datetime
from typing import Optional

from common.logging import logger
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
    # 2. 异步推送：入队 notification_queue，由 NotificationWorkerPool 消费
    try:
        enqueue_notification_event_from_alarm(alarm_data)
    except Exception as e:
        logger.error(f"入队推送任务失败(可忽略): {e}")
    
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
        
        # 计算区域层级名称：优先使用 Camera.area_id -> Area.hierarchy_path，
        # 回退到 alarm_data 透传字段，最后回退空。
        area_name = None
        try:
            from app.models import Camera, Area
            cam_id = alarm_data.get("camera_id")
            if cam_id:
                cam = session.query(Camera).filter(Camera.id == cam_id).first()
                if cam and getattr(cam, "area_id", None):
                    area = session.query(Area).filter(Area.id == cam.area_id).first()
                    if area:
                        area_name = getattr(area, "hierarchy_path", None) or getattr(area, "name", None)
        except Exception as e:
            logger.debug(f"补齐 area_name 失败(可忽略): {e}")
        if not area_name:
            area_name = alarm_data.get("area_name") or alarm_data.get("region_name")

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
            detection_data=alarm_data.get("detections", []),
            # 冗余字段：减少告警列表页 join/循环查询
            camera_name=alarm_data.get("camera_name"),
            algorithm_name=alarm_data.get("algorithm_name"),
            area_name=area_name,
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


def enqueue_notification_event_from_alarm(alarm_data: dict) -> None:
    """
    将告警推送任务写入 Redis notification_queue（异步发送）。
    """
    from app.services.notification_service import enqueue_notification_event

    payload = {
        "category": "ai",
        "alarm_id": alarm_data.get("alarm_id"),
        "alarm_type": alarm_data.get("alarm_type") or alarm_data.get("algorithm_code") or "ai_alarm",
        "level": _map_alert_level(alarm_data.get("alert_level", "info")),
        "camera_id": alarm_data.get("camera_id"),
        "camera_name": alarm_data.get("camera_name"),
        # 区域路径：dispatch_event 会根据 camera_id 补全 area_id_path/area_name_path；此处仅预填名称路径供无 camera_id 时展示
        "area_id_path": None,
        "area_name_path": alarm_data.get("area_name") or alarm_data.get("region_name"),
        "area_name": alarm_data.get("area_name") or alarm_data.get("region_name"),  # 模板 {{area_name}}
        "algorithm_id": alarm_data.get("algorithm_id"),
        "algorithm_name": alarm_data.get("algorithm_name"),
        "title": alarm_data.get("title") or alarm_data.get("algorithm_name") or "告警通知",
        "text": alarm_data.get("description") or "",
        # snapshot_url 建议走 preview（缩略图），由模板决定是否使用
        "image_url": None,
        "link_url": None,
    }
    enqueue_notification_event(payload)


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
    # 创建同步 Redis 客户端（使用 common.redis 封装）
    from common.redis.client import get_redis_client

    redis_client = get_redis_client().sync_client
    
    try:
        # 构建发布消息
        snapshot_key = alarm_data.get("snapshot_path")
        snapshot_url = None
        if snapshot_key:
            from urllib.parse import quote
            # WS/列表优先使用缩略图
            snapshot_url = f"/api/v1/files/preview?filepath={quote(str(snapshot_key))}&variant=thumb"
        message = {
            "type": "new_alarm",
            "alarm_id": alarm_data.get("alarm_id"),
            "camera_id": alarm_data.get("camera_id"),
            "camera_name": alarm_data.get("camera_name"),
            "area_name": alarm_data.get("area_name") or alarm_data.get("region_name"),
            "algorithm_id": alarm_data.get("algorithm_id"),
            "algorithm_name": alarm_data.get("algorithm_name"),
            "level": alarm_data.get("alert_level", "info"),
            "title": alarm_data.get("title"),
            "timestamp": alarm_data.get("timestamp"),
            "snapshot_path": snapshot_key,
            "snapshot_url": snapshot_url,
            "detection_data": alarm_data.get("detections", []),
        }
        
        redis_client.publish(
            RedisChannels.ALARMS_REALTIME,
            json.dumps(message, ensure_ascii=False)
        )
        
        logger.debug(f"实时告警已发布: {alarm_data.get('alarm_id')}")
        
    finally:
        redis_client.close()
