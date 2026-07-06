"""
本地存储安全测试。
"""
from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.services.storage.local_storage import LocalFileStorage


def test_local_storage_rejects_path_traversal_key(tmp_path) -> None:
    """对象 key 不能通过 ../ 写出 storage 根目录。"""
    storage_dir = tmp_path / "storage"
    storage = LocalFileStorage(storage_dir)

    with pytest.raises(ValidationError):
        storage.put_object("../escape.txt", b"unsafe")

    assert not (tmp_path / "escape.txt").exists()
