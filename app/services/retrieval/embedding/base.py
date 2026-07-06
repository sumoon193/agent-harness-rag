"""
Embedding Protocol。

定义文本向量化接口。
"""
from __future__ import annotations

from typing import Protocol


class Embedder(Protocol):
    """
    Embedding 接口。

    所有 embedder 必须实现此接口。
    """

    dimension: int  # 向量维度

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        批量 embed 文档。

        Args:
            texts: 文本列表

        Returns:
            向量列表，与输入文本一一对应
        """
        ...

    async def embed_query(self, query: str) -> list[float]:
        """
        Embed 查询文本。

        Args:
            query: 查询文本

        Returns:
            查询向量
        """
        ...
