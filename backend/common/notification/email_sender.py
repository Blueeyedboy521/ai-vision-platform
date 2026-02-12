# -*- coding: utf-8 -*-
"""
邮件通知实现

通过 SMTP 发送告警邮件
"""
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor

from common.logging import logger
from .interface import NotificationInterface, NotificationMessage, NotificationLevel


class EmailNotifier(NotificationInterface):
    """
    邮件通知
    
    通过 SMTP 服务器发送邮件
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        sender: Optional[str] = None,
        use_ssl: bool = True
    ):
        """
        初始化邮件通知器
        
        Args:
            host: SMTP 服务器地址
            port: SMTP 端口
            user: SMTP 用户名
            password: SMTP 密码
            sender: 发件人地址 (默认使用 user)
            use_ssl: 是否使用 SSL
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.sender = sender or user
        self.use_ssl = use_ssl
        
        self._enabled = bool(host and user and password)
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    @property
    def name(self) -> str:
        return "email"
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def _build_email(
        self,
        message: NotificationMessage,
        recipients: List[str]
    ) -> MIMEMultipart:
        """
        构建邮件
        
        Args:
            message: 通知消息
            recipients: 收件人列表
            
        Returns:
            MIMEMultipart 邮件对象
        """
        # 级别对应的标签
        level_text = {
            NotificationLevel.INFO: "[信息]",
            NotificationLevel.WARNING: "[警告]",
            NotificationLevel.DANGER: "[危险]",
            NotificationLevel.CRITICAL: "[严重]"
        }
        
        level_tag = level_text.get(message.level, "[信息]")
        subject = f"{level_tag} {message.title}"
        
        # 创建邮件
        email = MIMEMultipart("alternative")
        email["Subject"] = subject
        email["From"] = self.sender
        email["To"] = ", ".join(recipients)
        
        # 构建 HTML 内容
        html_content = self._build_html_body(message)
        
        # 添加 HTML 内容
        html_part = MIMEText(html_content, "html", "utf-8")
        email.attach(html_part)
        
        return email
    
    def _build_html_body(self, message: NotificationMessage) -> str:
        """
        构建 HTML 邮件正文
        
        Args:
            message: 通知消息
            
        Returns:
            HTML 字符串
        """
        # 级别对应的颜色
        level_colors = {
            NotificationLevel.INFO: "#17a2b8",
            NotificationLevel.WARNING: "#ffc107",
            NotificationLevel.DANGER: "#dc3545",
            NotificationLevel.CRITICAL: "#721c24"
        }
        
        color = level_colors.get(message.level, "#17a2b8")
        
        # 构建内容行
        content_lines = message.content.replace("\n", "<br>")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; border-top: none; }}
                .footer {{ font-size: 12px; color: #6c757d; margin-top: 20px; }}
                .info-item {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #495057; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">{message.title}</h2>
                </div>
                <div class="content">
                    <p>{content_lines}</p>
        """
        
        # 添加摄像头信息
        if message.camera_name:
            html += f"""
                    <div class="info-item">
                        <span class="label">摄像头:</span> {message.camera_name}
                    </div>
            """
        
        # 添加算法信息
        if message.algorithm_name:
            html += f"""
                    <div class="info-item">
                        <span class="label">检测算法:</span> {message.algorithm_name}
                    </div>
            """
        
        # 添加截图链接
        if message.snapshot_url:
            html += f"""
                    <div class="info-item">
                        <a href="{message.snapshot_url}" style="color: {color};">查看告警截图</a>
                    </div>
            """
        
        html += f"""
                    <div class="footer">
                        告警时间: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
                        此邮件由 AI Vision Platform 自动发送，请勿回复。
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_email_sync(
        self,
        email: MIMEMultipart,
        recipients: List[str]
    ) -> bool:
        """
        同步发送邮件 (内部方法)
        
        Args:
            email: 邮件对象
            recipients: 收件人列表
            
        Returns:
            是否发送成功
        """
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=30)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=30)
                server.starttls()
            
            server.login(self.user, self.password)
            server.sendmail(self.sender, recipients, email.as_string())
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    async def send(self, message: NotificationMessage) -> bool:
        """
        异步发送邮件
        
        Args:
            message: 通知消息
            
        Returns:
            是否发送成功
        """
        if not self._enabled:
            logger.warning("邮件通知未启用")
            return False
        
        recipients = message.recipients
        if not recipients:
            logger.warning("邮件接收者列表为空")
            return False
        
        email = self._build_email(message, recipients)
        
        # 在线程池中执行同步发送
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self._executor,
                self._send_email_sync,
                email,
                recipients
            )
            
            if result:
                logger.info(f"邮件发送成功: {message.title} -> {recipients}")
            
            return result
            
        except Exception as e:
            logger.error(f"邮件发送异常: {e}")
            return False
    
    def send_sync(self, message: NotificationMessage) -> bool:
        """
        同步发送邮件
        
        Args:
            message: 通知消息
            
        Returns:
            是否发送成功
        """
        if not self._enabled:
            logger.warning("邮件通知未启用")
            return False
        
        recipients = message.recipients
        if not recipients:
            logger.warning("邮件接收者列表为空")
            return False
        
        email = self._build_email(message, recipients)
        result = self._send_email_sync(email, recipients)
        
        if result:
            logger.info(f"邮件发送成功: {message.title} -> {recipients}")
        
        return result
