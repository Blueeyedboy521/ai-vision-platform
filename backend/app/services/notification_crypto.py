# -*- coding: utf-8 -*-
"""
通知配置加密/解密与脱敏回显

要求：
- 数据库存储加密后的 endpoint 配置；
- 前端查看/编辑时只能拿到脱敏内容；
- 更新时支持“保持原值”（不传/传掩码则不更新）。
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from common.logging import logger
from config.settings import settings


MASK = "********"


def _get_fernet():
    try:
        from cryptography.fernet import Fernet
    except Exception as e:
        raise RuntimeError(f"缺少依赖 cryptography，无法加密通知配置: {e}")
    key = (getattr(settings, "NOTIFICATION_ENCRYPTION_KEY", "") or "").strip()
    if not key:
        # 机制：未显式配置时，从 SECRET_KEY 派生一个稳定的 Fernet key，保证“可用 + 可部署”
        # 生产环境仍建议显式配置 NOTIFICATION_ENCRYPTION_KEY（支持密钥轮换、避免耦合 JWT secret）。
        import base64
        import hashlib

        seed = (getattr(settings, "SECRET_KEY", "") or "").encode("utf-8")
        digest = hashlib.sha256(seed).digest()[:32]
        key = base64.urlsafe_b64encode(digest).decode("utf-8")
        logger.warning("未配置 NOTIFICATION_ENCRYPTION_KEY，已使用 SECRET_KEY 派生加密密钥（建议生产环境显式配置）")
    return Fernet(key.encode("utf-8"))


def encrypt_config(config: Dict[str, Any]) -> str:
    f = _get_fernet()
    raw = json.dumps(config or {}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return f.encrypt(raw).decode("utf-8")


def decrypt_config(token: str) -> Dict[str, Any]:
    f = _get_fernet()
    raw = f.decrypt((token or "").encode("utf-8"))
    return json.loads(raw.decode("utf-8"))


def mask_config(provider: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    按 provider 返回脱敏配置给前端展示
    """
    cfg = dict(config or {})

    def _mask_url(u: str) -> str:
        u = str(u or "")
        if len(u) <= 16:
            return MASK
        # 保留协议与末尾片段
        return u[:8] + MASK + u[-6:]

    # 通用字段
    for k in ("webhook_url", "secret", "token", "key"):
        if k in cfg and cfg.get(k):
            if k == "webhook_url":
                cfg[k] = _mask_url(cfg[k])
            else:
                cfg[k] = MASK

    # provider 特定字段可以继续扩展
    return cfg


def merge_update_config(
    provider: str,
    old_config: Dict[str, Any],
    new_config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    更新配置合并规则：
    - new_config 为 None：保持旧配置
    - 传入字段值为 MASK：保持旧值
    - 其它：覆盖旧值
    """
    if new_config is None:
        return dict(old_config or {})
    merged = dict(old_config or {})
    for k, v in (new_config or {}).items():
        if isinstance(v, str) and v.strip() == MASK:
            continue
        merged[k] = v
    return merged

