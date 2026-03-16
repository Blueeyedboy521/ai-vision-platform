# -*- coding: utf-8 -*-
"""
流媒体 Hook API Controller

- 处理 ZLMediaKit Hook 回调
- 授权与状态更新逻辑委托给 media_hook_service
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from common.logging import logger
from app.services.media_hook_service import (
    parse_token_from_params,
    verify_play_token,
    verify_push_ip,
    handle_on_stream_changed,
)


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


@router.post("/on_play", response_model=HookResponse, summary="播放鉴权")
async def on_play_api(request: OnPlayRequest):
    """
    播放鉴权 Hook
    """
    logger.info(
        f"播放请求: app={request.app}, stream={request.stream}, ip={request.ip}"
    )

    token = parse_token_from_params(request.params or "")

    if not verify_play_token(token, request.stream):
        logger.warning(
            f"播放鉴权失败: stream={request.stream}, ip={request.ip}"
        )
        return HookResponse(code=-1, msg="鉴权失败")

    return HookResponse(code=0, msg="success")


@router.post("/on_publish", response_model=HookResponse, summary="推流鉴权")
async def on_publish_api(request: OnPublishRequest):
    """
    推流鉴权 Hook
    """
    logger.info(
        f"推流请求: app={request.app}, stream={request.stream}, ip={request.ip}"
    )

    if not verify_push_ip(request.ip):
        logger.warning(
            f"推流鉴权失败: IP不在白名单, stream={request.stream}, ip={request.ip}"
        )
        return HookResponse(code=-1, msg="IP不在白名单")

    return HookResponse(code=0, msg="success")


@router.post("/on_stream_changed", response_model=HookResponse, summary="流状态变化")
async def on_stream_changed_api(request: OnStreamChangedRequest):
    """
    流状态变化通知
    """
    await handle_on_stream_changed(request.model_dump())
    return HookResponse(code=0, msg="success")


@router.post("/on_stream_none_reader", response_model=HookResponse, summary="无人观看")
async def on_stream_none_reader_api(
    app: str,
    stream: str,
):
    """
    无人观看通知
    """
    logger.info(f"流无人观看: app={app}, stream={stream}")
    return HookResponse(code=0, msg="success")

