"""
本地文件系统存储（fallback 模式）。

V1 阶段使用，不需要 Docker 或 MinIO。
文件保存在项目根目录的 storage/ 目录下。
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)

DEFAULT_STORAGE_DIR = Path(__file__).parent.parent.parent.parent / "storage"


class LocalFileStorage:
    """
    本地文件系统存储。

    实现 StorageBackend 协议，用于 V1 fallback 模式。
    """

    def __init__(self, base_dir: Path | str | None = None) -> None:
        self._base_dir = Path(base_dir) if base_dir else DEFAULT_STORAGE_DIR
        self._base_dir.mkdir(parents=True, exist_ok=True)
        logger.info("local_storage_init", extra={"base_dir": str(self._base_dir)})

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        file_path = self._resolve_key(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        logger.info(
            "object_stored",
            extra={"key": key, "size": len(data), "path": str(file_path)},
        )
        return str(file_path)

    def get_object(self, key: str) -> bytes:
        file_path = self._resolve_key(key)
        if not file_path.exists():
            raise NotFoundError(f"对象不存在: {key}")
        return file_path.read_bytes()

    def object_exists(self, key: str) -> bool:
        return self._resolve_key(key).exists()

    def delete_object(self, key: str) -> None:
        file_path = self._resolve_key(key)
        if file_path.exists():
            file_path.unlink()
            logger.info("object_deleted", extra={"key": key})

    def _resolve_key(self, key: str) -> Path:
        """解析对象 key，并确保最终路径仍在 storage 根目录内。"""
        if not key or key.strip() == "":
            raise ValidationError("对象 key 不能为空")

        relative_key = Path(key)
        if relative_key.is_absolute():
            raise ValidationError(f"非法对象 key: {key}")

        base_dir = self._base_dir.resolve()
        file_path = (base_dir / relative_key).resolve()

        try:
            file_path.relative_to(base_dir)
        except ValueError as exc:
            raise ValidationError(f"非法对象 key: {key}") from exc

        return file_path
