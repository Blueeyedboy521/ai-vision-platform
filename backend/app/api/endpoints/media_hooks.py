# -*- coding: utf-8 -*-
"""
流媒体 Hook API

处理 ZLMediaKit 的 Hook 回调
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from common.logging import logger


router = APIRouter()


class HookResponse(BaseModel):
    """Hook 响应"""
    code: int = Field(default=0, description="状态码: 0成功, 非0失败")
    msg: str = Field(default="success", description="消息")


class OnPlayRequest(BaseModel):
    """播放鉴权请求"""
    app: str = Field(description="应用名")
    stream: str = Field(description="流名称")
    ip: str = Field(description="客户端IP")
    params: Optional[str] = Field(default="", description="URL参数")
    port: Optional[int] = Field(default=None, description="客户端端口")
    schema: Optional[str] = Field(default=None, description="协议")
    vhost: Optional[str] = Field(default=None, description="虚拟主机")


class OnPublishRequest(BaseModel):
    """推流鉴权请求"""
    app: str = Field(description="应用名")
    stream: str = Field(description="流名称")
    ip: str = Field(description="推流端IP")
    params: Optional[str] = Field(default="", description="URL参数")
    port: Optional[int] = Field(default=None, description="推流端端口")
    schema: Optional[str] = Field(default=None, description="协议")
    vhost: Optional[str] = Field(default=None, description="虚拟主机")


class OnStreamChangedRequest(BaseModel):
    """流状态变化通知"""
    app: str = Field(description="应用名")
    stream: str = Field(description="流名称")
    regist: bool = Field(description="是否注册(true:上线, false:下线)")
    schema: Optional[str] = Field(default=None, description="协议")
    vhost: Optional[str] = Field(default=None, description="虚拟主机")


def parse_token_from_params(params: str) -> Optional[str]:
    """
    从 URL 参数中解析 Token
    
    Args:
        params: URL 参数字符串 (如 "token=xxx&foo=bar")
        
    Returns:
        Token 值，不存在则返回 None
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
    验证播放 Token
    
    Args:
        token: JWT Token
        stream: 流名称
        
    Returns:
        是否验证通过
    """
    if not token:
        # 如果没有 Token，检查是否允许匿名播放
        # 生产环境应该返回 False
        if settings.ENVIRONMENT == "development":
            return True
        return False
    
    # 验证 JWT Token
    from app.core.security import decode_access_token
    
    payload = decode_access_token(token)
    if payload is None:
        return False
    
    # 检查 Token 类型
    if payload.get("type") != "access":
        return False
    
    return True


def verify_push_ip(ip: str) -> bool:
    """
    验证推流 IP 是否在白名单中
    
    Args:
        ip: 推流端 IP
        
    Returns:
        是否允许推流
    """
    import ipaddress
    
    try:
        client_ip = ipaddress.ip_address(ip)
    except ValueError:
        return False
    
    for allowed in settings.ZLM_ALLOWED_PUSH_IPS:
        try:
            if "/" in allowed:
                # CIDR 格式
                network = ipaddress.ip_network(allowed, strict=False)
                if client_ip in network:
                    return True
            else:
                # 单个 IP
                if client_ip == ipaddress.ip_address(allowed):
                    return True
        except ValueError:
            continue
    
    return False


@router.post("/on_play", response_model=HookResponse, summary="播放鉴权")
async def on_play(request: OnPlayRequest):
    """
    播放鉴权 Hook
    
    当客户端请求播放流时触发
    """
    logger.info(
        f"播放请求: app={request.app}, "
        f"stream={request.stream}, "
        f"ip={request.ip}"
    )
    
    # 解析 Token
    token = parse_token_from_params(request.params)
    
    # 验证 Token
    if not verify_play_token(token, request.stream):
        logger.warning(
            f"播放鉴权失败: stream={request.stream}, ip={request.ip}"
        )
        return HookResponse(code=-1, msg="鉴权失败")
    
    return HookResponse(code=0, msg="success")


@router.post("/on_publish", response_model=HookResponse, summary="推流鉴权")
async def on_publish(request: OnPublishRequest):
    """
    推流鉴权 Hook
    
    当推流端开始推流时触发
    """
    logger.info(
        f"推流请求: app={request.app}, "
        f"stream={request.stream}, "
        f"ip={request.ip}"
    )
    
    # 验证推流 IP
    if not verify_push_ip(request.ip):
        logger.warning(
            f"推流鉴权失败: IP不在白名单, "
            f"stream={request.stream}, ip={request.ip}"
        )
        return HookResponse(code=-1, msg="IP不在白名单")
    
    return HookResponse(code=0, msg="success")


@router.post("/on_stream_changed", response_model=HookResponse, summary="流状态变化")
async def on_stream_changed(request: OnStreamChangedRequest):
    """
    流状态变化通知
    
    当流上线或下线时触发
    """
    status = "上线" if request.regist else "下线"
    logger.info(
        f"流状态变化: app={request.app}, "
        f"stream={request.stream}, "
        f"状态={status}"
    )
    
    # 更新摄像头状态
    if request.stream.startswith("camera_"):
        camera_id = request.stream.replace("camera_", "")
        
        # 异步更新数据库
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
                    camera.status = "online" if request.regist else "offline"
                    await session.commit()
                    logger.info(f"摄像头状态已更新: {camera_id} -> {camera.status}")
                    
        except Exception as e:
            logger.error(f"更新摄像头状态失败: {e}")
    
    return HookResponse(code=0, msg="success")


@router.post("/on_stream_none_reader", response_model=HookResponse, summary="无人观看")
async def on_stream_none_reader(
    app: str,
    stream: str
):
    """
    无人观看通知
    
    当流的所有观看者都断开时触发
    """
    logger.info(f"流无人观看: app={app}, stream={stream}")
    
    # 可以在这里决定是否关闭流
    # 返回 close: true 会关闭流
    return {"code": 0, "close": False}
