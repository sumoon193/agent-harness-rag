"""
RRF Fusion。

Reciprocal Rank Fusion 算法，用于合并多个检索器的结果。
"""
from __future__ import annotations

import logging

from app.schemas.retrieval import RetrievalResult

logger = logging.getLogger(__name__)


class RRFFuser:
    """
    Reciprocal Rank Fusion。

    公式：score = 1 / (k + rank)
    其中 k 是常数（默认 60），rank 是排名（从 1 开始）。
    """

    def __init__(self, k: int = 60) -> None:
        """
        初始化 RRF Fuser。

        Args:
            k: RRF 常数，默认 60
        """
        self._k = k
        logger.info("rrf_fuser_initialized", extra={"k": k})

    def fuse(
        self,
        *result_lists: list[RetrievalResult],
        top_k: int = 10
    ) -> list[RetrievalResult]:
        """
        融合多个检索结果列表。

        Args:
            result_lists: 多个检索结果列表
            top_k: 返回结果数量

        Returns:
            融合后的结果列表（按 RRF 分数降序）
        """
        logger.info(
            "rrf_fusion",
            extra={"list_count": len(result_lists), "top_k": top_k}
        )

        # 收集所有 chunk 及其 RRF 分数
        chunk_scores: dict[str, float] = {}  # chunk_key -> rrf_score
        chunk_map: dict[str, RetrievalResult] = {}  # chunk_key -> result

        for result_list in result_lists:
            for rank, result in enumerate(result_list, start=1):
                # 使用 chunk_id 作为 key
                chunk_key = result.chunk_id

                # 计算 RRF 分数
                rrf_score = 1.0 / (self._k + rank)

                # 累加分数
                chunk_scores[chunk_key] = chunk_scores.get(chunk_key, 0.0) + rrf_score

                # 保存结果（使用第一次出现的）
                if chunk_key not in chunk_map:
                    chunk_map[chunk_key] = result

        # 按 RRF 分数降序排序
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)

        # 取 top_k
        results: list[RetrievalResult] = []
        for chunk_key, rrf_score in sorted_chunks[:top_k]:
            original = chunk_map[chunk_key]

            # 创建新的结果，更新分数
            fused = RetrievalResult(
                chunk_id=original.chunk_id,
                document_id=original.document_id,
                chunk_text=original.chunk_text,
                context_prefix=original.context_prefix,
                score=rrf_score,  # 使用 RRF 分数作为主分数
                rerank_score=original.rerank_score,
                raw_score=original.raw_score,
                document_name=original.document_name,
                section=original.section,
                page=original.page,
                heading_path=original.heading_path,
                tenant_id=original.tenant_id,
                department_id=original.department_id,
                visibility=original.visibility
            )
            results.append(fused)

        logger.info(
            "rrf_fusion_complete",
            extra={"returned": len(results)}
        )

        return results
