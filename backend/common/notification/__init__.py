# -*- coding: utf-8 -*-
"""
通知模块

提供多种消息推送渠道的实现
"""
from .interface import NotificationInterface, NotificationMessage
from .dingtalk import DingTalkNotifier
from .email_sender import EmailNotifier

__all__ = [
    "NotificationInterface",
    "NotificationMessage", 
    "DingTalkNotifier",
    "EmailNotifier",
    "get_notifiers"
]


def get_notifiers() -> list:
    """
    获取已配置的通知器列表
    
    根据配置自动初始化可用的通知器
    
    Returns:
        通知器实例列表
    """
    from config.settings import settings
    
    notifiers = []
    
    # 钉钉通知
    if settings.DINGTALK_WEBHOOK_URL:
        notifiers.append(DingTalkNotifier(
            webhook_url=settings.DINGTALK_WEBHOOK_URL,
            secret=settings.DINGTALK_SECRET if settings.DINGTALK_SECRET else None
        ))
    
    # 邮件通知
    if settings.SMTP_HOST and settings.SMTP_USER:
        notifiers.append(EmailNotifier(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            user=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            sender=settings.SMTP_FROM or settings.SMTP_USER,
            use_ssl=settings.SMTP_USE_SSL
        ))
    
    return notifiers
