"""
Reranker Protocol。

定义重排序接口。
"""
from __future__ import annotations

from typing import Protocol

from app.schemas.retrieval import RetrievalResult


class Reranker(Protocol):
    """
    Reranker 接口。

    所有 reranker 必须实现此接口。
    """

    async def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        top_k: int = 10
    ) -> list[RetrievalResult]:
        """
        对检索结果进行重排序。

        Args:
            query: 查询文本
            results: 检索结果列表
            top_k: 返回结果数量

        Returns:
            重排序后的结果列表
        """
        ...
