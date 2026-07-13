"""
Citation Builder。

从 EvidenceBundle 构建结构化引用列表，供答案生成和前端展示使用。
"""
from __future__ import annotations

import logging

from app.schemas.chunk import Citation, EvidenceBundle

logger = logging.getLogger(__name__)

# 单次回答最多引用数
MAX_CITATIONS = 5


class CitationBuilder:
    """
    引用构建器。

    从 EvidenceBundle 提取前 N 条高分证据，
    生成带编号的 Citation 列表。
    """

    def build(
        self,
        evidence: EvidenceBundle,
        max_citations: int = MAX_CITATIONS,
    ) -> list[Citation]:
        """
        从 EvidenceBundle 构建引用列表。

        Args:
            evidence: 检索到的证据包
            max_citations: 最大引用数

        Returns:
            带编号的 Citation 列表（编号从 1 开始）
        """
        if not evidence.evidence_list:
            logger.info("citation_builder_empty_evidence")
            return []

        # 按 rerank_score 降序排列，取前 max_citations 条
        sorted_evidence = sorted(
            evidence.evidence_list,
            key=lambda c: c.rerank_score,
            reverse=True,
        )[:max_citations]

        # 重新编号（从 1 开始）
        citations: list[Citation] = []
        for idx, item in enumerate(sorted_evidence, start=1):
            citation = Citation(
                id=idx,
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                document_version=item.document_version,
                document_name=item.document_name,
                section=item.section,
                page=item.page,
                chunk_text=item.chunk_text,
                score=item.score,
                rerank_score=item.rerank_score,
                raw_score=item.raw_score,
            )
            citations.append(citation)

        logger.info(
            "citation_built",
            extra={"count": len(citations)},
        )
        return citations

    def format_for_prompt(self, citations: list[Citation]) -> list[dict[str, object]]:
        """
        将 Citation 列表格式化为 Prompt 模板可消费的 dict 列表。

        Args:
            citations: 引用列表

        Returns:
            dict 列表，字段名与 answer_prompt 模板一致
        """
        return [
            {
                "document_name": c.document_name,
                "section": c.section,
                "page": c.page,
                "text": c.chunk_text,
            }
            for c in citations
        ]
