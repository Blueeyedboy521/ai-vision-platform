# -*- coding: utf-8 -*-
"""
流管理器

管理摄像头流的生命周期
"""
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from common.logging import logger
from .zlm_client import get_zlm_client


@dataclass
class StreamInfo:
    """
    流信息数据类
    """
    camera_id: str                    # 摄像头ID
    stream_key: str                   # 流标识 (camera_{id})
    rtsp_url: str                     # 原始 RTSP 地址
    push_url: Optional[str] = None    # 推流地址
    play_url_flv: Optional[str] = None    # HTTP-FLV 播放地址
    play_url_rtsp: Optional[str] = None   # RTSP 播放地址
    play_url_hls: Optional[str] = None    # HLS 播放地址
    status: str = "offline"           # 状态: online/offline/error
    started_at: Optional[datetime] = None  # 启动时间
    error_msg: Optional[str] = None   # 错误信息


class StreamManager:
    """
    流管理器
    
    负责管理所有摄像头流的状态和地址
    """
    
    def __init__(self):
        """初始化流管理器"""
        self._streams: Dict[str, StreamInfo] = {}
        self._zlm_client = get_zlm_client()
    
    def generate_stream_key(self, camera_id: str) -> str:
        """
        生成流标识
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            流标识
        """
        return f"camera_{camera_id}"
    
    def get_stream_info(self, camera_id: str) -> Optional[StreamInfo]:
        """
        获取流信息
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            流信息，不存在返回 None
        """
        stream_key = self.generate_stream_key(camera_id)
        return self._streams.get(stream_key)
    
    def register_stream(
        self,
        camera_id: str,
        rtsp_url: str
    ) -> StreamInfo:
        """
        注册流
        
        Args:
            camera_id: 摄像头ID
            rtsp_url: RTSP 地址
            
        Returns:
            流信息
        """
        stream_key = self.generate_stream_key(camera_id)
        
        # 生成各种地址
        push_url = self._zlm_client.get_push_url(stream_key)
        play_url_flv = self._zlm_client.get_play_url(stream_key, protocol="http-flv")
        play_url_rtsp = self._zlm_client.get_play_url(stream_key, protocol="rtsp")
        play_url_hls = self._zlm_client.get_play_url(stream_key, protocol="hls")
        
        stream_info = StreamInfo(
            camera_id=camera_id,
            stream_key=stream_key,
            rtsp_url=rtsp_url,
            push_url=push_url,
            play_url_flv=play_url_flv,
            play_url_rtsp=play_url_rtsp,
            play_url_hls=play_url_hls,
            status="offline"
        )
        
        self._streams[stream_key] = stream_info
        logger.info(f"流已注册: {stream_key}")
        
        return stream_info
    
    def unregister_stream(self, camera_id: str) -> None:
        """
        注销流
        
        Args:
            camera_id: 摄像头ID
        """
        stream_key = self.generate_stream_key(camera_id)
        
        if stream_key in self._streams:
            del self._streams[stream_key]
            logger.info(f"流已注销: {stream_key}")
    
    def update_stream_status(
        self,
        camera_id: str,
        status: str,
        error_msg: Optional[str] = None
    ) -> None:
        """
        更新流状态
        
        Args:
            camera_id: 摄像头ID
            status: 状态
            error_msg: 错误信息
        """
        stream_key = self.generate_stream_key(camera_id)
        
        if stream_key in self._streams:
            self._streams[stream_key].status = status
            self._streams[stream_key].error_msg = error_msg
            
            if status == "online" and self._streams[stream_key].started_at is None:
                self._streams[stream_key].started_at = datetime.now()
            
            logger.debug(f"流状态更新: {stream_key} -> {status}")
    
    async def check_stream_online(self, camera_id: str) -> bool:
        """
        检查流是否在线
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            是否在线
        """
        stream_key = self.generate_stream_key(camera_id)
        media_info = await self._zlm_client.get_media_info(stream_key)
        
        is_online = media_info is not None
        self.update_stream_status(
            camera_id,
            "online" if is_online else "offline"
        )
        
        return is_online
    
    async def close_stream(self, camera_id: str) -> bool:
        """
        关闭流
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            是否成功
        """
        stream_key = self.generate_stream_key(camera_id)
        success = await self._zlm_client.close_stream(stream_key)
        
        if success:
            self.update_stream_status(camera_id, "offline")
        
        return success
    
    def get_all_streams(self) -> Dict[str, StreamInfo]:
        """
        获取所有流信息
        
        Returns:
            流信息字典
        """
        return self._streams.copy()
    
    def get_play_urls(self, camera_id: str, token: Optional[str] = None) -> Dict[str, str]:
        """
        获取播放地址 (带 Token)
        
        Args:
            camera_id: 摄像头ID
            token: 认证 Token
            
        Returns:
            播放地址字典
        """
        stream_info = self.get_stream_info(camera_id)
        
        if stream_info is None:
            return {}
        
        urls = {
            "flv": stream_info.play_url_flv,
            "rtsp": stream_info.play_url_rtsp,
            "hls": stream_info.play_url_hls
        }
        
        # 如果有 Token，添加到 URL 参数
        if token:
            urls["flv"] = f"{urls['flv']}?token={token}"
            urls["hls"] = f"{urls['hls']}?token={token}"
        
        return urls


# 全局流管理器实例
_stream_manager: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    """
    获取全局流管理器实例
    
    Returns:
        StreamManager 实例
    """
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
    return _stream_manager
