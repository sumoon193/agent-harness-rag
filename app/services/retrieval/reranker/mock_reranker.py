"""
Mock Reranker。

简单按原始分数排序，便于测试。
"""
from __future__ import annotations

import logging

from app.schemas.retrieval import RetrievalResult

logger = logging.getLogger(__name__)


class MockReranker:
    """
    Mock Reranker 实现。

    简单按原始分数排序，为每个结果生成 rerank_score（基于原始分数）。
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
        logger.info(
            "mock_reranking",
            extra={"query": query[:50], "input_count": len(results), "top_k": top_k}
        )

        # 按原始分数降序排序
        sorted_results = sorted(
            results,
            key=lambda r: r.raw_score if r.raw_score is not None else r.score,
            reverse=True
        )

        # 取 top_k
        top_results = sorted_results[:top_k]

        # 生成 rerank_score（基于原始分数）
        reranked: list[RetrievalResult] = []
        for result in top_results:
            # 使用原始分数作为 rerank_score（简单实现）
            raw = result.raw_score if result.raw_score is not None else result.score
            # 归一化到 [0, 1] 范围
            if raw < 0:
                rerank_score = 0.0
            elif raw > 1:
                rerank_score = 1.0
            else:
                rerank_score = raw

            reranked_result = RetrievalResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                document_version=result.document_version,
                chunk_text=result.chunk_text,
                context_prefix=result.context_prefix,
                score=result.score,
                rerank_score=rerank_score,
                raw_score=result.raw_score,
                document_name=result.document_name,
                section=result.section,
                page=result.page,
                heading_path=result.heading_path,
                tenant_id=result.tenant_id,
                department_id=result.department_id,
                visibility=result.visibility
            )
            reranked.append(reranked_result)

        logger.info(
            "mock_reranking_complete",
            extra={"returned": len(reranked)}
        )

        return reranked
