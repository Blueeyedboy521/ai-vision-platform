# -*- coding: utf-8 -*-
"""
钉钉机器人通知实现

通过钉钉 Webhook 发送告警通知
"""
import time
import hmac
import hashlib
import base64
import urllib.parse
from typing import Optional

import httpx

from common.logging import logger
from .interface import NotificationInterface, NotificationMessage, NotificationLevel


class DingTalkNotifier(NotificationInterface):
    """
    钉钉机器人通知
    
    支持普通 Webhook 和签名验证模式
    """
    
    def __init__(
        self,
        webhook_url: str,
        secret: Optional[str] = None
    ):
        """
        初始化钉钉通知器
        
        Args:
            webhook_url: 钉钉机器人 Webhook URL
            secret: 签名密钥 (可选，如果配置了加签)
        """
        self.webhook_url = webhook_url
        self.secret = secret
        self._enabled = bool(webhook_url)
    
    @property
    def name(self) -> str:
        return "dingtalk"
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def _generate_sign(self) -> tuple:
        """
        生成签名
        
        Returns:
            (timestamp, sign) 元组
        """
        if not self.secret:
            return None, None
        
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(
            secret_enc,
            string_to_sign_enc,
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return timestamp, sign
    
    def _get_webhook_url(self) -> str:
        """获取带签名的 Webhook URL"""
        if not self.secret:
            return self.webhook_url
        
        timestamp, sign = self._generate_sign()
        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
    
    def _build_message(self, message: NotificationMessage) -> dict:
        """
        构建钉钉消息体
        
        Args:
            message: 通知消息
            
        Returns:
            钉钉 API 消息格式
        """
        # 级别对应的颜色标记
        level_emoji = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.DANGER: "🔴",
            NotificationLevel.CRITICAL: "🚨"
        }
        
        emoji = level_emoji.get(message.level, "ℹ️")
        
        # 构建 Markdown 格式的内容
        markdown_content = f"### {emoji} {message.title}\n\n"
        markdown_content += f"{message.content}\n\n"
        
        # 添加截图链接 (如果有)
        if message.snapshot_url:
            markdown_content += f"[查看截图]({message.snapshot_url})\n\n"
        
        # 添加时间
        markdown_content += f"> {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return {
            "msgtype": "markdown",
            "markdown": {
                "title": message.title,
                "text": markdown_content
            }
        }
    
    async def send(self, message: NotificationMessage) -> bool:
        """
        异步发送钉钉通知
        
        Args:
            message: 通知消息
            
        Returns:
            是否发送成功
        """
        if not self._enabled:
            logger.warning("钉钉通知未启用")
            return False
        
        url = self._get_webhook_url()
        payload = self._build_message(message)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=10.0
                )
                
                result = response.json()
                
                if result.get("errcode") == 0:
                    logger.info(f"钉钉通知发送成功: {message.title}")
                    return True
                else:
                    logger.error(f"钉钉通知发送失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"钉钉通知发送异常: {e}")
            return False
    
    def send_sync(self, message: NotificationMessage) -> bool:
        """
        同步发送钉钉通知
        
        Args:
            message: 通知消息
            
        Returns:
            是否发送成功
        """
        if not self._enabled:
            logger.warning("钉钉通知未启用")
            return False
        
        url = self._get_webhook_url()
        payload = self._build_message(message)
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json=payload,
                    timeout=10.0
                )
                
                result = response.json()
                
                if result.get("errcode") == 0:
                    logger.info(f"钉钉通知发送成功: {message.title}")
                    return True
                else:
                    logger.error(f"钉钉通知发送失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"钉钉通知发送异常: {e}")
            return False
