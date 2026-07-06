"""
Storage Protocol。

统一对象存储接口，V1 用本地文件系统 fallback，后续替换为 MinIO。
"""
from __future__ import annotations

from typing import Protocol


class StorageBackend(Protocol):
    """
    对象存储后端协议。

    所有存储后端必须实现此接口。
    """

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        保存对象。

        Args:
            key: 对象键（如 tenant_id/2026/05/doc_xxx/filename.pdf）
            data: 文件内容
            content_type: MIME 类型

        Returns:
            存储后的实际路径或键
        """
        ...

    def get_object(self, key: str) -> bytes:
        """
        读取对象。

        Args:
            key: 对象键

        Returns:
            文件内容

        Raises:
            NotFoundError: 对象不存在
        """
        ...

    def object_exists(self, key: str) -> bool:
        """
        检查对象是否存在。

        Args:
            key: 对象键

        Returns:
            是否存在
        """
        ...

    def delete_object(self, key: str) -> None:
        """
        删除对象。

        Args:
            key: 对象键
        """
        ...
