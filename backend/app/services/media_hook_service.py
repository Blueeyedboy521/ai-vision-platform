# -*- coding: utf-8 -*-
"""
流媒体 Hook 业务逻辑：
- 播放与推流鉴权
- 流状态变化处理
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import ipaddress

from app.core.config import settings
from common.logging import logger


def parse_token_from_params(params: str) -> Optional[str]:
    """
    从 URL 参数中解析 Token，例如 "token=xxx&foo=bar"。
    """
    if not params:
        return None

    for param in params.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            if key == "token":
                return value

    return None


def verify_play_token(token: Optional[str], stream: str) -> bool:
    """
    验证播放 Token。
    """
    if not token:
        if settings.ENVIRONMENT == "development":
            return True
        return False

    from app.core.security import decode_access_token

    payload = decode_access_token(token)
    if payload is None:
        return False

    if payload.get("type") != "access":
        return False

    return True


def verify_push_ip(ip: str) -> bool:
    """
    验证推流 IP 是否在白名单中。
    """
    try:
        client_ip = ipaddress.ip_address(ip)
    except ValueError:
        return False

    for allowed in settings.ZLM_ALLOWED_PUSH_IPS:
        try:
            if "/" in allowed:
                network = ipaddress.ip_network(allowed, strict=False)
                if client_ip in network:
                    return True
            else:
                if client_ip == ipaddress.ip_address(allowed):
                    return True
        except ValueError:
            continue

    return False


async def handle_on_stream_changed(payload: Dict[str, Any]) -> None:
    """
    处理流状态变化，必要时更新摄像头状态。
    """
    app = payload.get("app")
    stream = payload.get("stream")
    regist = payload.get("regist")

    status = "上线" if regist else "下线"
    logger.info(
        f"流状态变化: app={app}, stream={stream}, 状态={status}"
    )

    if not isinstance(stream, str) or not stream.startswith("camera_"):
        return

    camera_id = stream.replace("camera_", "")

    try:
        from app.core.database import get_db_session
        from app.models import Camera
        from sqlalchemy import select

        async with get_db_session() as session:
            result = await session.execute(
                select(Camera).where(Camera.id == camera_id)
            )
            camera = result.scalar_one_or_none()

            if camera:
                camera.status = "online" if regist else "offline"
                await session.commit()
                logger.info(
                    f"摄像头状态已更新: {camera_id} -> {camera.status}"
                )
    except Exception as e:
        logger.error(f"更新摄像头状态失败: {e}")

