"""
MinIO 对象存储适配器。

实现 StorageBackend 协议，替代 LocalFileStorage。
"""
from __future__ import annotations

import io
import logging

from minio import Minio
from minio.error import S3Error

from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class MinIOStorage:
    """
    MinIO 对象存储。

    实现 StorageBackend 协议，用于 full 模式。
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        # endpoint 可能带 http:// 前缀，MinIO 客户端只需要 host:port
        clean_endpoint = endpoint.replace("http://", "").replace("https://", "")
        self._client = Minio(
            clean_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._bucket = bucket
        logger.info("minio_storage_init", extra={"endpoint": clean_endpoint, "bucket": bucket})

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logger.info("minio_object_stored", extra={"key": key, "size": len(data)})
        return key

    def get_object(self, key: str) -> bytes:
        try:
            response = self._client.get_object(self._bucket, key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                raise NotFoundError(f"对象不存在: {key}") from exc
            raise

    def object_exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self._bucket, key)
            return True
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                return False
            raise

    def delete_object(self, key: str) -> None:
        try:
            self._client.remove_object(self._bucket, key)
            logger.info("minio_object_deleted", extra={"key": key})
        except S3Error:
            logger.warning("minio_delete_failed", extra={"key": key})
