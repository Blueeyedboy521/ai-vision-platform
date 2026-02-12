# -*- coding: utf-8 -*-
"""
ZLMediaKit API 客户端

封装 ZLMediaKit 流媒体服务器的 RESTful API
"""
from typing import Optional, Dict, Any, List

import httpx

from common.logging import logger


class ZLMediaKitClient:
    """
    ZLMediaKit API 客户端
    
    提供流媒体服务器的常用 API 调用
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:80",
        secret: str = ""
    ):
        """
        初始化 ZLMediaKit 客户端
        
        Args:
            api_url: ZLMediaKit API 地址
            secret: API 密钥
        """
        self.api_url = api_url.rstrip("/")
        self.secret = secret
        self._timeout = 10.0
    
    async def _request(
        self,
        api: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送 API 请求
        
        Args:
            api: API 名称
            params: 请求参数
            
        Returns:
            API 响应
        """
        params = params or {}
        params["secret"] = self.secret
        
        url = f"{self.api_url}/index/api/{api}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    timeout=self._timeout
                )
                return response.json()
        except Exception as e:
            logger.error(f"ZLMediaKit API 请求失败: {api}, 错误: {e}")
            return {"code": -1, "msg": str(e)}
    
    def _request_sync(
        self,
        api: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        同步发送 API 请求
        
        Args:
            api: API 名称
            params: 请求参数
            
        Returns:
            API 响应
        """
        params = params or {}
        params["secret"] = self.secret
        
        url = f"{self.api_url}/index/api/{api}"
        
        try:
            with httpx.Client() as client:
                response = client.get(
                    url,
                    params=params,
                    timeout=self._timeout
                )
                return response.json()
        except Exception as e:
            logger.error(f"ZLMediaKit API 请求失败: {api}, 错误: {e}")
            return {"code": -1, "msg": str(e)}
    
    # ==================== 服务器信息 ====================
    
    async def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return await self._request("getServerConfig")
    
    async def get_threads_load(self) -> Dict[str, Any]:
        """获取线程负载"""
        return await self._request("getThreadsLoad")
    
    # ==================== 流管理 ====================
    
    async def get_media_list(
        self,
        schema: Optional[str] = None,
        vhost: str = "__defaultVhost__",
        app: Optional[str] = None,
        stream: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取流列表
        
        Args:
            schema: 协议类型 (rtsp/rtmp/hls 等)
            vhost: 虚拟主机
            app: 应用名
            stream: 流名称
            
        Returns:
            流列表
        """
        params = {"vhost": vhost}
        
        if schema:
            params["schema"] = schema
        if app:
            params["app"] = app
        if stream:
            params["stream"] = stream
        
        result = await self._request("getMediaList", params)
        
        if result.get("code") == 0:
            return result.get("data", [])
        return []
    
    async def get_media_info(
        self,
        stream: str,
        app: str = "live",
        schema: str = "rtmp",
        vhost: str = "__defaultVhost__"
    ) -> Optional[Dict[str, Any]]:
        """
        获取流详细信息
        
        Args:
            stream: 流名称
            app: 应用名
            schema: 协议类型
            vhost: 虚拟主机
            
        Returns:
            流信息，不存在返回 None
        """
        result = await self._request("getMediaInfo", {
            "schema": schema,
            "vhost": vhost,
            "app": app,
            "stream": stream
        })
        
        if result.get("code") == 0:
            return result.get("data")
        return None
    
    async def close_stream(
        self,
        stream: str,
        app: str = "live",
        vhost: str = "__defaultVhost__",
        force: bool = True
    ) -> bool:
        """
        关闭流
        
        Args:
            stream: 流名称
            app: 应用名
            vhost: 虚拟主机
            force: 是否强制关闭
            
        Returns:
            是否成功
        """
        result = await self._request("close_streams", {
            "vhost": vhost,
            "app": app,
            "stream": stream,
            "force": 1 if force else 0
        })
        
        success = result.get("code") == 0
        if success:
            logger.info(f"流已关闭: {app}/{stream}")
        else:
            logger.warning(f"关闭流失败: {app}/{stream}, {result}")
        
        return success
    
    async def close_streams(
        self,
        schema: Optional[str] = None,
        vhost: str = "__defaultVhost__",
        app: Optional[str] = None,
        stream: Optional[str] = None,
        force: bool = True
    ) -> int:
        """
        批量关闭流
        
        Args:
            schema: 协议类型
            vhost: 虚拟主机
            app: 应用名
            stream: 流名称
            force: 是否强制关闭
            
        Returns:
            关闭的流数量
        """
        params = {
            "vhost": vhost,
            "force": 1 if force else 0
        }
        
        if schema:
            params["schema"] = schema
        if app:
            params["app"] = app
        if stream:
            params["stream"] = stream
        
        result = await self._request("close_streams", params)
        
        if result.get("code") == 0:
            count = result.get("count_closed", 0)
            logger.info(f"批量关闭流: {count} 路")
            return count
        return 0
    
    # ==================== 拉流代理 ====================
    
    async def add_stream_proxy(
        self,
        stream: str,
        url: str,
        app: str = "live",
        vhost: str = "__defaultVhost__",
        retry_count: int = 3,
        timeout_sec: int = 10,
        enable_rtsp: bool = True,
        enable_rtmp: bool = True,
        enable_hls: bool = False,
        enable_mp4: bool = False
    ) -> Optional[str]:
        """
        添加拉流代理
        
        让 ZLMediaKit 主动拉取远程流
        
        Args:
            stream: 流名称
            url: 远程流地址 (RTSP/RTMP)
            app: 应用名
            vhost: 虚拟主机
            retry_count: 重试次数
            timeout_sec: 超时时间
            enable_rtsp: 启用 RTSP
            enable_rtmp: 启用 RTMP
            enable_hls: 启用 HLS
            enable_mp4: 启用 MP4 录制
            
        Returns:
            流的 key，失败返回 None
        """
        result = await self._request("addStreamProxy", {
            "vhost": vhost,
            "app": app,
            "stream": stream,
            "url": url,
            "retry_count": retry_count,
            "timeout_sec": timeout_sec,
            "enable_rtsp": 1 if enable_rtsp else 0,
            "enable_rtmp": 1 if enable_rtmp else 0,
            "enable_hls": 1 if enable_hls else 0,
            "enable_mp4": 1 if enable_mp4 else 0
        })
        
        if result.get("code") == 0:
            key = result.get("data", {}).get("key")
            logger.info(f"拉流代理已添加: {app}/{stream}, key={key}")
            return key
        else:
            logger.error(f"添加拉流代理失败: {result}")
            return None
    
    async def del_stream_proxy(self, key: str) -> bool:
        """
        删除拉流代理
        
        Args:
            key: 流的 key
            
        Returns:
            是否成功
        """
        result = await self._request("delStreamProxy", {"key": key})
        
        if result.get("code") == 0:
            logger.info(f"拉流代理已删除: {key}")
            return True
        else:
            logger.warning(f"删除拉流代理失败: {key}, {result}")
            return False
    
    # ==================== 录制控制 ====================
    
    async def start_record(
        self,
        stream: str,
        app: str = "live",
        vhost: str = "__defaultVhost__",
        record_type: int = 0,  # 0:HLS, 1:MP4
        custom_path: Optional[str] = None
    ) -> bool:
        """
        开始录制
        
        Args:
            stream: 流名称
            app: 应用名
            vhost: 虚拟主机
            record_type: 录制类型
            custom_path: 自定义保存路径
            
        Returns:
            是否成功
        """
        params = {
            "vhost": vhost,
            "app": app,
            "stream": stream,
            "type": record_type
        }
        
        if custom_path:
            params["customized_path"] = custom_path
        
        result = await self._request("startRecord", params)
        return result.get("code") == 0
    
    async def stop_record(
        self,
        stream: str,
        app: str = "live",
        vhost: str = "__defaultVhost__",
        record_type: int = 0
    ) -> bool:
        """
        停止录制
        
        Args:
            stream: 流名称
            app: 应用名
            vhost: 虚拟主机
            record_type: 录制类型
            
        Returns:
            是否成功
        """
        result = await self._request("stopRecord", {
            "vhost": vhost,
            "app": app,
            "stream": stream,
            "type": record_type
        })
        return result.get("code") == 0
    
    # ==================== 辅助方法 ====================
    
    def get_play_url(
        self,
        stream: str,
        app: str = "live",
        protocol: str = "http-flv"
    ) -> str:
        """
        获取播放地址
        
        Args:
            stream: 流名称
            app: 应用名
            protocol: 协议类型 (http-flv/rtsp/rtmp/hls)
            
        Returns:
            播放地址
        """
        from config.settings import settings
        
        # 解析 API URL 获取主机地址
        import urllib.parse
        parsed = urllib.parse.urlparse(self.api_url)
        host = parsed.hostname
        
        if protocol == "http-flv":
            port = settings.ZLM_HTTP_FLV_PORT
            return f"http://{host}:{port}/{app}/{stream}.live.flv"
        elif protocol == "rtsp":
            port = settings.ZLM_RTSP_PORT
            return f"rtsp://{host}:{port}/{app}/{stream}"
        elif protocol == "rtmp":
            port = settings.ZLM_RTMP_PORT
            return f"rtmp://{host}:{port}/{app}/{stream}"
        elif protocol == "hls":
            port = settings.ZLM_HTTP_FLV_PORT
            return f"http://{host}:{port}/{app}/{stream}/hls.m3u8"
        else:
            return f"http://{host}/{app}/{stream}.live.flv"
    
    def get_push_url(
        self,
        stream: str,
        app: str = "live",
        protocol: str = "rtmp"
    ) -> str:
        """
        获取推流地址
        
        Args:
            stream: 流名称
            app: 应用名
            protocol: 协议类型 (rtmp/rtsp)
            
        Returns:
            推流地址
        """
        from config.settings import settings
        
        import urllib.parse
        parsed = urllib.parse.urlparse(self.api_url)
        host = parsed.hostname
        
        if protocol == "rtmp":
            port = settings.ZLM_RTMP_PORT
            return f"rtmp://{host}:{port}/{app}/{stream}"
        elif protocol == "rtsp":
            port = settings.ZLM_RTSP_PORT
            return f"rtsp://{host}:{port}/{app}/{stream}"
        else:
            return f"rtmp://{host}:1935/{app}/{stream}"


# 全局客户端实例
_zlm_client: Optional[ZLMediaKitClient] = None


def get_zlm_client() -> ZLMediaKitClient:
    """
    获取全局 ZLMediaKit 客户端实例
    
    Returns:
        ZLMediaKitClient 实例
    """
    global _zlm_client
    if _zlm_client is None:
        from config.settings import settings
        _zlm_client = ZLMediaKitClient(
            api_url=settings.ZLM_API_URL,
            secret=settings.ZLM_SECRET
        )
    return _zlm_client
