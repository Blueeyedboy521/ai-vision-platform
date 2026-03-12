# -*- coding: utf-8 -*-
"""
消息推送 Provider 标准与实现

要求：
1) app 定义推送接口标准
2) 定义企微/钉钉实现类（暂时仅实现企微）
3) 支持两类模板：text/rich，由上层传入已渲染后的抽象消息
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Dict, Any

import httpx

from common.logging import logger


@dataclass(frozen=True)
class RenderedMessage:
    """
    抽象消息（模板渲染结果）
    """

    title: str
    text: str
    image_url: Optional[str] = None
    link_url: Optional[str] = None


class NotificationProvider(Protocol):
    name: str

    def send_sync(self, endpoint_config: Dict[str, Any], message: RenderedMessage) -> None:
        """
        同步发送。失败抛异常（由上层记录 DeliveryLog）
        """
        ...


class WeComBotProvider:
    """
    企微机器人（群机器人 webhook）

对外抽象为两类：
- text: 发送 markdown（更清晰）
- rich: 优先发送 news（单条图文），无 image_url 时降级 textcard/markdown
"""

    name = "wecom_bot"

    def send_sync(self, endpoint_config: Dict[str, Any], message: RenderedMessage) -> None:
        webhook = (endpoint_config or {}).get("webhook_url") or ""
        if not webhook:
            raise ValueError("endpoint_config.webhook_url 为空")

        payload = self._build_payload(endpoint_config, message)
        # 企微 webhook 是外网调用，给较短超时并捕获错误
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(webhook, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"企微推送失败: http={resp.status_code}, body={resp.text[:500]}")
        try:
            data = resp.json()
        except Exception:
            data = None
        if isinstance(data, dict) and data.get("errcode", 0) != 0:
            raise RuntimeError(f"企微推送失败: {data}")

    def _build_payload(self, endpoint_config: Dict[str, Any], message: RenderedMessage) -> Dict[str, Any]:
        # 简化：默认用 markdown；若 image_url + link_url 同时存在，则用 news
        if message.image_url and message.link_url:
            return {
                "msgtype": "news",
                "news": {
                    "articles": [
                        {
                            "title": message.title[:128],
                            "description": message.text[:512],
                            "url": message.link_url,
                            "picurl": message.image_url,
                        }
                    ]
                },
            }

        # markdown（企微支持）
        md = f"**{message.title}**\n\n{message.text}"
        if message.link_url:
            md += f"\n\n[查看详情]({message.link_url})"
        return {"msgtype": "markdown", "markdown": {"content": md}}


class DingTalkBotProvider:
    """
    钉钉机器人：暂时只定义接口，后续实现。
    """

    name = "dingtalk_bot"

    def send_sync(self, endpoint_config: Dict[str, Any], message: RenderedMessage) -> None:
        raise NotImplementedError("DingTalkBotProvider 暂未实现（计划中）")


def get_provider(provider: str) -> NotificationProvider:
    p = (provider or "").strip()
    if p == "wecom_bot":
        return WeComBotProvider()
    if p == "dingtalk_bot":
        return DingTalkBotProvider()
    raise ValueError(f"未知 provider: {provider}")

