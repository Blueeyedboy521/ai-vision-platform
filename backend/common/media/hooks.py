# -*- coding: utf-8 -*-
"""
ZLMediaKit Hook 数据结构

定义 Hook 回调的请求和响应数据结构
"""
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class HookBaseRequest:
    """
    Hook 请求基类
    
    ZLMediaKit 所有 Hook 回调的公共字段
    """
    app: str                          # 应用名
    stream: str                       # 流名称
    vhost: str = "__defaultVhost__"   # 虚拟主机
    schema: Optional[str] = None      # 协议类型


@dataclass  
class OnPlayHook(HookBaseRequest):
    """
    播放鉴权 Hook
    
    当客户端请求播放流时触发
    """
    ip: str                           # 客户端 IP
    port: int = 0                     # 客户端端口
    params: str = ""                  # URL 参数
    id: str = ""                      # 流ID
    

@dataclass
class OnPublishHook(HookBaseRequest):
    """
    推流鉴权 Hook
    
    当推流端开始推流时触发
    """
    ip: str                           # 推流端 IP
    port: int = 0                     # 推流端端口
    params: str = ""                  # URL 参数
    id: str = ""                      # 流ID


@dataclass
class OnStreamChangedHook(HookBaseRequest):
    """
    流状态变化 Hook
    
    当流上线或下线时触发
    """
    regist: bool                      # 是否注册 (true: 上线, false: 下线)
    

@dataclass
class OnStreamNoneReaderHook(HookBaseRequest):
    """
    无人观看 Hook
    
    当流的所有观看者都断开时触发
    """
    pass


@dataclass
class HookResponse:
    """
    Hook 响应
    
    ZLMediaKit Hook 的标准响应格式
    """
    code: int = 0                     # 状态码: 0成功, 非0失败
    msg: str = "success"              # 消息
    
    # 特定 Hook 的额外字段
    enableHls: bool = True            # 是否启用 HLS
    enableMP4: bool = False           # 是否启用 MP4 录制
    enableRtxp: bool = True           # 是否启用 RTMP/RTSP
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "code": self.code,
            "msg": self.msg
        }
