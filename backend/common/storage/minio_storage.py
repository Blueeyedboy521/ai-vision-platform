# -*- coding: utf-8 -*-
"""
使用 MinIO (S3 协议) 的文件存储实现

提供与 StorageInterface 一致的增删改查能力：
- save_file / save_image
- get_file
- delete_file
- exists
- get_url
"""
from typing import Optional, BinaryIO, Union
from io import BytesIO
from datetime import timedelta

import cv2
import numpy as np
from minio import Minio
from minio.error import S3Error

from common.logging import logger
from .interface import StorageInterface


class MinIOStorage(StorageInterface):
    """
    基于 MinIO 的 S3 存储实现
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ):
        """
        初始化 MinIO 客户端

        Args:
            endpoint: MinIO 地址，如 "localhost:9000"
            access_key: Access Key
            secret_key: Secret Key
            bucket: 默认存储桶名称
            secure: 是否使用 HTTPS
        """
        self.endpoint = endpoint
        self.bucket = bucket
        self.secure = secure

        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

        # 确保存储桶存在
        try:
            found = self.client.bucket_exists(bucket)
            if not found:
                self.client.make_bucket(bucket)
                logger.info(f"MinIO 存储桶已创建: {bucket}")
            else:
                logger.info(f"MinIO 存储桶已存在: {bucket}")
        except S3Error as e:
            logger.error(f"检查/创建 MinIO 存储桶失败: {e}")
            raise

    def _put_object(
        self,
        object_name: str,
        data: Union[bytes, BinaryIO],
        content_type: Optional[str] = None,
    ) -> str:
        """
        封装 MinIO put_object 调用
        """
        try:
            if isinstance(data, bytes):
                body = BytesIO(data)
                length = len(data)
            else:
                raw = data.read()
                body = BytesIO(raw)
                length = len(raw)

            self.client.put_object(
                self.bucket,
                object_name,
                body,
                length,
                content_type=content_type or "application/octet-stream",
            )
            logger.debug(f"文件已上传到 MinIO: {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"上传文件到 MinIO 失败: {object_name}, 错误: {e}")
            raise

    def save_file(
        self,
        file_data: Union[bytes, BinaryIO],
        path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        保存文件到 MinIO
        """
        self._put_object(path, file_data, content_type)
        return path

    def save_image(
        self,
        image: np.ndarray,
        path: str,
        quality: int = 90,
    ) -> str:
        """
        保存图片 (从 numpy 数组) 到 MinIO
        """
        if image is None or image.size == 0:
            raise ValueError("图片数据为空")

        # 确保路径有扩展名
        if not path.lower().endswith((".jpg", ".jpeg", ".png")):
            path = f"{path}.jpg"

        # 根据扩展名选择编码参数
        if path.lower().endswith(".png"):
            encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
            mime = "image/png"
        else:
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            mime = "image/jpeg"

        success, buf = cv2.imencode(
            ".png" if mime == "image/png" else ".jpg", image, encode_params
        )
        if not success:
            raise RuntimeError("OpenCV 编码图片失败")

        self._put_object(path, buf.tobytes(), content_type=mime)
        return path

    def get_file(self, path: str) -> Optional[bytes]:
        """
        从 MinIO 获取文件内容
        """
        try:
            resp = self.client.get_object(self.bucket, path)
            try:
                data = resp.read()
            finally:
                resp.close()
                resp.release_conn()
            return data
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            logger.error(f"从 MinIO 读取文件失败: {path}, 错误: {e}")
            return None

    def delete_file(self, path: str) -> bool:
        """
        从 MinIO 删除文件
        """
        try:
            self.client.remove_object(self.bucket, path)
            logger.debug(f"从 MinIO 删除文件: {path}")
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return True
            logger.error(f"从 MinIO 删除文件失败: {path}, 错误: {e}")
            return False

    def exists(self, path: str) -> bool:
        """
        检查 MinIO 中对象是否存在
        """
        try:
            self.client.stat_object(self.bucket, path)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.error(f"检查 MinIO 对象是否存在失败: {path}, 错误: {e}")
            return False

    def get_url(self, path: str) -> str:
        """
        获取对象的访问 URL，使用 MinIO 预签名地址，避免直接暴露对象
        """
        try:
            return self.client.presigned_get_object(
                self.bucket,
                path,
                expires=timedelta(hours=1)
            )
        except S3Error as e:
            logger.error(f"生成 MinIO 预签名 URL 失败: {path}, 错误: {e}")
            # 回退到直连地址
            scheme = "https" if self.secure else "http"
            return f"{scheme}://{self.endpoint}/{self.bucket}/{path}"

    def download_file(self, path: str, download_path: str) -> bool:
        """
        下载文件
        """
        try:
            self.client.fget_object(self.bucket, path, download_path)
            return True
        except S3Error as e:
            logger.error(f"下载文件失败: {path}, 错误: {e}")
            return False
    
    def upload_file(self, path: str, upload_path: str) -> bool:
        """
        上传文件
        """
        try:
            # fput_object(bucket, object_name, file_path)
            self.client.fput_object(self.bucket, path, upload_path)
            return True
        except S3Error as e:
            logger.error(f"上传文件失败: {path} -> {upload_path}, 错误: {e}")
            return False
