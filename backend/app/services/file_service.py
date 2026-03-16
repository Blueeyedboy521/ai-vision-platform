# -*- coding: utf-8 -*-
"""
文件存储相关业务逻辑：
- 临时文件上传 / 删除 / 获取 URL
- 正式文件获取 URL / 预览 / 删除

Controller 仅负责路由与权限校验，本模块封装具体存储与路径规则。
"""

from __future__ import annotations

import mimetypes
from io import BytesIO
from typing import Optional, Tuple

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from common.logging import logger
from common.storage import get_storage
from app.core.security import decode_access_token
from app.services.auth_service import get_auth_service


def normalize_temp_path(path: str, category: str) -> str:
    """
    规范化临时文件路径：tmp/{category}/{path}
    """
    path = path.lstrip("/").replace("\\", "/")
    category = category.strip("/").replace("\\", "/") or "misc"
    return f"tmp/{category}/{path}"


def normalize_perm_path(path: str, category: str) -> str:
    """
    规范化正式文件路径：{category}/{path}
    """
    path = path.lstrip("/").replace("\\", "/")
    category = category.strip("/").replace("\\", "/") or "misc"
    return f"{category}/{path}"


def validate_access_token_from_query(token: Optional[str]) -> None:
    """
    允许以 QueryString 方式携带 token 时的基础校验。
    """
    if not token:
        raise HTTPException(status_code=401, detail="未提供认证凭证")
    payload = decode_access_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token 无效或已过期")


async def upload_temp_file_bytes(data: bytes, filename: str, category: str, user_id: Optional[str]) -> Tuple[str, str]:
    storage = get_storage()
    user_prefix = f"user_{user_id}" if user_id else "anonymous"
    temp_path = normalize_temp_path(f"{user_prefix}/{filename}", category)
    try:
        key = storage.save_file(data, temp_path, content_type=None)
        url = storage.get_url(key)
        return key, url
    except Exception as e:
        logger.error(f"上传临时文件失败: {e}")
        raise HTTPException(status_code=500, detail="上传失败，请稍后重试")


def delete_temp_file_by_key(key: str) -> None:
    storage = get_storage()
    ok = storage.delete_file(key)
    if not ok:
        raise HTTPException(status_code=404, detail="文件不存在或已删除")


def get_temp_file_url(key: str) -> str:
    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(status_code=404, detail="文件不存在")
    return storage.get_url(key)


def get_file_url(key: str) -> str:
    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(status_code=404, detail="文件不存在")
    return storage.get_url(key)


async def build_preview_response(
    filepath: str,
    variant: str,
    token: Optional[str],
    has_header_user: bool,
) -> StreamingResponse:
    """
    根据 filepath 和变体返回 StreamingResponse，包含必要的 token/黑名单校验。
    """
    if not has_header_user:
        auth_service = get_auth_service()
        if await auth_service.is_token_blacklisted(token or ""):
            raise HTTPException(status_code=401, detail="Token 已失效")
        validate_access_token_from_query(token)

    storage = get_storage()
    read_key = filepath
    if (variant or "").lower() == "thumb":
        from common.media.image import build_thumb_key

        thumb_key = build_thumb_key(filepath)
        if storage.exists(thumb_key):
            read_key = thumb_key

    if not storage.exists(read_key):
        raise HTTPException(status_code=404, detail="文件不存在")

    data = storage.get_file(read_key)
    if data is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    content_type, _ = mimetypes.guess_type(read_key)
    return StreamingResponse(
        BytesIO(data),
        media_type=content_type or "application/octet-stream",
    )


def delete_file_by_key(key: str) -> None:
    storage = get_storage()
    ok = storage.delete_file(key)
    if not ok:
        raise HTTPException(status_code=404, detail="文件不存在或已删除")

