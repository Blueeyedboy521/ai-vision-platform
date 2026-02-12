# -*- coding: utf-8 -*-
"""
WebSocket 连接管理器

管理所有 WebSocket 连接，支持按频道分组
"""
import json
import asyncio
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

from common.logging import logger


@dataclass
class ConnectionInfo:
    """
    连接信息
    """
    
    websocket: WebSocket
    user_id: Optional[str] = None
    channels: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    
    def __hash__(self):
        return id(self.websocket)


class ConnectionManager:
    """
    WebSocket 连接管理器
    
    功能:
    - 管理所有 WebSocket 连接
    - 支持按频道订阅和广播
    - 支持向特定用户推送消息
    """
    
    def __init__(self):
        """初始化连接管理器"""
        # 所有活跃连接
        self._connections: Dict[WebSocket, ConnectionInfo] = {}
        
        # 频道 -> 连接集合
        self._channels: Dict[str, Set[WebSocket]] = {}
        
        # 用户 -> 连接集合
        self._user_connections: Dict[str, Set[WebSocket]] = {}
        
        # 锁
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None
    ) -> ConnectionInfo:
        """
        接受 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接
            user_id: 用户ID (可选)
            
        Returns:
            连接信息
        """
        await websocket.accept()
        
        conn_info = ConnectionInfo(
            websocket=websocket,
            user_id=user_id
        )
        
        async with self._lock:
            self._connections[websocket] = conn_info
            
            # 如果有用户ID，添加到用户连接映射
            if user_id:
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = set()
                self._user_connections[user_id].add(websocket)
        
        logger.info(
            f"WebSocket 连接建立: "
            f"user_id={user_id}, "
            f"总连接数={len(self._connections)}"
        )
        
        return conn_info
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        断开 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接
        """
        async with self._lock:
            conn_info = self._connections.pop(websocket, None)
            
            if conn_info is None:
                return
            
            # 从所有频道中移除
            for channel in conn_info.channels:
                if channel in self._channels:
                    self._channels[channel].discard(websocket)
                    if not self._channels[channel]:
                        del self._channels[channel]
            
            # 从用户连接映射中移除
            if conn_info.user_id:
                user_conns = self._user_connections.get(conn_info.user_id)
                if user_conns:
                    user_conns.discard(websocket)
                    if not user_conns:
                        del self._user_connections[conn_info.user_id]
        
        logger.info(
            f"WebSocket 连接断开: "
            f"user_id={conn_info.user_id if conn_info else None}, "
            f"总连接数={len(self._connections)}"
        )
    
    async def subscribe(
        self,
        websocket: WebSocket,
        channel: str
    ) -> bool:
        """
        订阅频道
        
        Args:
            websocket: WebSocket 连接
            channel: 频道名称
            
        Returns:
            是否成功
        """
        async with self._lock:
            conn_info = self._connections.get(websocket)
            if conn_info is None:
                return False
            
            # 添加到频道
            if channel not in self._channels:
                self._channels[channel] = set()
            self._channels[channel].add(websocket)
            
            # 更新连接信息
            conn_info.channels.add(channel)
        
        logger.debug(f"订阅频道: {channel}, 订阅者数={len(self._channels.get(channel, set()))}")
        return True
    
    async def unsubscribe(
        self,
        websocket: WebSocket,
        channel: str
    ) -> bool:
        """
        取消订阅频道
        
        Args:
            websocket: WebSocket 连接
            channel: 频道名称
            
        Returns:
            是否成功
        """
        async with self._lock:
            conn_info = self._connections.get(websocket)
            if conn_info is None:
                return False
            
            # 从频道中移除
            if channel in self._channels:
                self._channels[channel].discard(websocket)
                if not self._channels[channel]:
                    del self._channels[channel]
            
            # 更新连接信息
            conn_info.channels.discard(channel)
        
        return True
    
    async def send_personal(
        self,
        websocket: WebSocket,
        message: Any
    ) -> bool:
        """
        向单个连接发送消息
        
        Args:
            websocket: WebSocket 连接
            message: 消息内容
            
        Returns:
            是否成功
        """
        try:
            if isinstance(message, dict):
                await websocket.send_json(message)
            else:
                await websocket.send_text(str(message))
            return True
        except Exception as e:
            logger.warning(f"发送 WebSocket 消息失败: {e}")
            return False
    
    async def broadcast_to_channel(
        self,
        channel: str,
        message: Any,
        exclude: Optional[WebSocket] = None
    ) -> int:
        """
        向频道广播消息
        
        Args:
            channel: 频道名称
            message: 消息内容
            exclude: 排除的连接
            
        Returns:
            成功发送的数量
        """
        async with self._lock:
            subscribers = self._channels.get(channel, set()).copy()
        
        if not subscribers:
            return 0
        
        # 序列化消息
        if isinstance(message, dict):
            message_str = json.dumps(message, ensure_ascii=False)
        else:
            message_str = str(message)
        
        success_count = 0
        failed_connections = []
        
        for ws in subscribers:
            if exclude and ws == exclude:
                continue
            
            try:
                await ws.send_text(message_str)
                success_count += 1
            except Exception:
                failed_connections.append(ws)
        
        # 清理失败的连接
        for ws in failed_connections:
            await self.disconnect(ws)
        
        return success_count
    
    async def broadcast_to_user(
        self,
        user_id: str,
        message: Any
    ) -> int:
        """
        向指定用户的所有连接发送消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            成功发送的数量
        """
        async with self._lock:
            user_conns = self._user_connections.get(user_id, set()).copy()
        
        if not user_conns:
            return 0
        
        success_count = 0
        failed_connections = []
        
        for ws in user_conns:
            try:
                if isinstance(message, dict):
                    await ws.send_json(message)
                else:
                    await ws.send_text(str(message))
                success_count += 1
            except Exception:
                failed_connections.append(ws)
        
        # 清理失败的连接
        for ws in failed_connections:
            await self.disconnect(ws)
        
        return success_count
    
    async def broadcast_all(
        self,
        message: Any,
        exclude: Optional[WebSocket] = None
    ) -> int:
        """
        向所有连接广播消息
        
        Args:
            message: 消息内容
            exclude: 排除的连接
            
        Returns:
            成功发送的数量
        """
        async with self._lock:
            all_conns = list(self._connections.keys())
        
        success_count = 0
        failed_connections = []
        
        for ws in all_conns:
            if exclude and ws == exclude:
                continue
            
            try:
                if isinstance(message, dict):
                    await ws.send_json(message)
                else:
                    await ws.send_text(str(message))
                success_count += 1
            except Exception:
                failed_connections.append(ws)
        
        # 清理失败的连接
        for ws in failed_connections:
            await self.disconnect(ws)
        
        return success_count
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self._connections)
    
    def get_channel_subscriber_count(self, channel: str) -> int:
        """获取频道订阅者数"""
        return len(self._channels.get(channel, set()))


# 全局连接管理器实例
connection_manager = ConnectionManager()
