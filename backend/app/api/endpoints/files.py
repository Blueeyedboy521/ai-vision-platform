# -*- coding: utf-8 -*-
"""
文件存储 API

封装统一的文件上传/删除/查看/下载能力，支持：
- 临时文件：前端上传但尚未业务提交时使用，路径统一加 tmp 前缀
- 正式文件：模型文件、告警截图、头像等业务正式文件
"""
from typing import Optional
from io import BytesIO
import mimetypes

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, get_current_user_optional
from app.models import User
from app.schemas.common import success_response
from common.storage import get_storage
from common.logging import logger
from app.core.security import decode_access_token
from app.services.auth_service import get_auth_service


router = APIRouter()

def _validate_access_token_from_query(token: Optional[str]) -> None:
    """
    允许前端以 QueryString 方式携带 token（img 标签无法设置 Authorization Header）。
    这里只做 access token 的基础校验与黑名单校验，不再额外查 DB。
    """
    if not token:
        raise HTTPException(status_code=401, detail="未提供认证凭证")
    payload = decode_access_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    # 黑名单校验（同步/异步均可能；此处按 async service 调用）


def _normalize_temp_path(path: str, category: str) -> str:
    """
    规范化临时文件路径：
    tmp/{category}/{path}
    """
    path = path.lstrip("/").replace("\\", "/")
    category = category.strip("/").replace("\\", "/") or "misc"
    return f"tmp/{category}/{path}"


def _normalize_perm_path(path: str, category: str) -> str:
    """
    规范化正式文件路径：
    {category}/{path}
    """
    path = path.lstrip("/").replace("\\", "/")
    category = category.strip("/").replace("\\", "/") or "misc"
    return f"{category}/{path}"


@router.post("/temp", summary="上传临时文件")
async def upload_temp_file(
    file: UploadFile = File(...),
    category: str = Query(
        "misc",
        description="业务类别: model/avatar/snapshot/video 等，用于归类临时文件",
    ),
    current_user: User = Depends(get_current_user),  # 仅用于权限校验
):
    """
    上传临时文件到存储（不直接写入业务表）。

    前端场景：
    - 选择模型文件 / 头像等 ⇒ 调用本接口上传到 tmp 目录，得到 temp_key + url
    - 表单真正保存成功前，仅保存 temp_key 在前端状态
    """
    storage = get_storage()

    # 临时路径使用用户 ID 做一层隔离，避免不同用户冲突
    filename = file.filename or "unnamed.bin"
    user_prefix = f"user_{current_user.id}" if getattr(current_user, "id", None) else "anonymous"
    temp_path = _normalize_temp_path(f"{user_prefix}/{filename}", category)

    try:
        data = await file.read()
        key = storage.save_file(data, temp_path, content_type=file.content_type)
        url = storage.get_url(key)
        return success_response({"key": key, "url": url})
    except Exception as e:
        logger.error(f"上传临时文件失败: {e}")
        raise HTTPException(status_code=500, detail="上传失败，请稍后重试")


@router.delete("/temp", summary="删除临时文件")
async def delete_temp_file(
    key: str = Query(..., description="临时文件 key，前端从 upload_temp_file 返回中获得"),
    current_user: User = Depends(get_current_user),
):
    """
    删除临时文件。
    """
    storage = get_storage()

    # 这里只做物理删除，不做用户 ID 校验（按需可增加前缀检查）
    ok = storage.delete_file(key)
    if not ok:
        raise HTTPException(status_code=404, detail="文件不存在或已删除")
    return success_response({"deleted": True})


@router.get("/temp", summary="获取临时文件访问地址")
async def download_temp_file(
    key: str = Query(..., description="临时文件 key"),
    current_user: User = Depends(get_current_user),
):
    """
    获取临时文件的访问 URL（用于调试或预览），不直接返回二进制。
    """
    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(status_code=404, detail="文件不存在")
    url = storage.get_url(key)
    return success_response({"key": key, "url": url})


@router.get("", summary="获取正式文件访问地址")
async def download_file(
    key: str = Query(..., description="正式文件 key，比如 models/...、avatars/... 等"),
    current_user: User = Depends(get_current_user),
):
    """
    获取正式文件访问 URL，不直接返回二进制。
    """
    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(status_code=404, detail="文件不存在")
    url = storage.get_url(key)
    return success_response({"key": key, "url": url})


@router.get("/preview", summary="正式文件预览（不暴露存储真实地址）")
async def preview_file(
    filepath: str = Query(..., description="正式文件 key，比如 alarm/...、models/... 等"),
    token: Optional[str] = Query(None, description="可选：通过 query 传递 access token（用于图片/视频标签预览）"),
    current_user: Optional[User] = Depends(get_current_user_optional),  # 兼容 header 鉴权
):
    """
    读取存储中的文件内容并以流方式返回。

    - 主要用途：前端通过 <img> 预览告警截图时不能设置 Authorization Header；
      因此允许通过 `token` query 参数传递 access token 来完成鉴权。
    - 如果前端已通过 Header 鉴权（例如 fetch 下载），也可以不传 token。
    """
    # 鉴权：优先使用 header（current_user 非空），否则要求 query token
    if current_user is None:
        auth_service = get_auth_service()
        if await auth_service.is_token_blacklisted(token or ""):
            raise HTTPException(status_code=401, detail="Token 已失效")
        # 黑名单校验需要调用 auth_service
        _validate_access_token_from_query(token)

    storage = get_storage()
    if not storage.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")

    data = storage.get_file(filepath)
    if data is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    content_type, _ = mimetypes.guess_type(filepath)
    return StreamingResponse(
        BytesIO(data),
        media_type=content_type or "application/octet-stream",
    )


@router.delete("", summary="删除正式文件")
async def delete_file(
    key: str = Query(..., description="正式文件 key，比如 models/...、avatars/... 等"),
    current_user: User = Depends(get_current_user),
):
    """
    删除正式文件（谨慎使用，一般通过业务逻辑触发）。
    """
    storage = get_storage()
    ok = storage.delete_file(key)
    if not ok:
        raise HTTPException(status_code=404, detail="文件不存在或已删除")
    return success_response({"deleted": True})

