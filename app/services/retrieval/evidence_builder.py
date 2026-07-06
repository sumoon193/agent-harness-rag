"""
EvidenceBuilder。

将 RetrievalResult 转换为 Citation 和 EvidenceBundle。
"""
from __future__ import annotations

import logging

from app.schemas.chunk import Citation, EvidenceBundle
from app.schemas.retrieval import RetrievalResult

logger = logging.getLogger(__name__)


class EvidenceBuilder:
    """
    证据构建器。

    将检索结果转换为证据包，用于答案生成。
    """

    def build(
        self,
        results: list[RetrievalResult],
        query: str
    ) -> EvidenceBundle:
        """
        构建证据包。

        Args:
            results: 检索结果列表（已 rerank）
            query: 查询文本

        Returns:
            证据包
        """
        logger.info(
            "building_evidence_bundle",
            extra={"result_count": len(results), "query": query[:50]}
        )

        # 转换为 Citation
        citations: list[Citation] = []
        for i, result in enumerate(results, start=1):
            citation = Citation(
                id=i,
                document_name=result.document_name or result.document_id,
                section=result.heading_path or result.section,
                page=result.page,
                chunk_text=result.chunk_text,
                score=result.score,
                rerank_score=result.rerank_score,
                raw_score=result.raw_score
            )
            citations.append(citation)

        # 计算 query_coverage_score
        query_coverage = self._calculate_query_coverage(results, query)

        # 构建 EvidenceBundle
        bundle = EvidenceBundle(
            evidence_list=citations,
            total_count=len(citations),
            query_coverage_score=query_coverage
        )

        logger.info(
            "evidence_bundle_built",
            extra={
                "citation_count": len(citations),
                "query_coverage": query_coverage
            }
        )

        return bundle

    def _calculate_query_coverage(
        self,
        results: list[RetrievalResult],
        query: str
    ) -> float:
        """
        计算查询覆盖率。

        基于检索结果覆盖查询关键词的程度。

        Args:
            results: 检索结果列表
            query: 查询文本

        Returns:
            查询覆盖率（0.0-1.0）
        """
        if not results:
            return 0.0

        # 提取查询关键词
        query_tokens = set(query.lower().split())
        if not query_tokens:
            return 0.5  # 默认值

        # 检查结果中包含多少查询关键词
        covered_tokens: set[str] = set()
        for result in results:
            text = (result.chunk_text + " " + result.context_prefix).lower()
            for token in query_tokens:
                if token in text:
                    covered_tokens.add(token)

        # 计算覆盖率
        coverage = len(covered_tokens) / len(query_tokens)

        # 限制在 [0, 1] 范围内
        return min(max(coverage, 0.0), 1.0)
