"""版本化文档和 chunk 的稳定身份生成。"""
from __future__ import annotations

import hashlib


def stable_chunk_id(
    *,
    document_id: str,
    document_version: str,
    heading_path: str,
    ordinal: int,
    chunk_text: str,
) -> str:
    """根据不可变文档版本和内容生成跨进程稳定 chunk ID。"""
    canonical = "\x1f".join(
        [document_id, document_version, heading_path, str(ordinal), chunk_text]
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"chunk_{digest}"
