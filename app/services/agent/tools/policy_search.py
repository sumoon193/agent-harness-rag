"""
政策检索工具。

模拟检索 HR 制度文档并返回相关引用。
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.user import UserContext

logger = logging.getLogger(__name__)


class PolicySearchHandler:
    """
    政策检索工具处理器。

    模拟检索 HR 制度文档，返回相关引用和摘要。
    """

    async def execute(
        self,
        parameters: dict[str, Any],
        user_context: UserContext
    ) -> dict[str, Any]:
        """
        执行政策检索。

        Args:
            parameters: 工具参数
                - query: 查询文本
                - top_k: 返回结果数量（可选，默认 3）
            user_context: 用户上下文

        Returns:
            检索结果
        """
        query = parameters.get("query", "")
        top_k = parameters.get("top_k", 3)

        logger.info(
            "policy_search_executed",
            extra={"query": query, "user_id": user_context.user_id}
        )

        # 模拟检索结果
        mock_citations = [
            {
                "id": 1,
                "document_name": "员工入职与转正管理制度",
                "section": "第二章 入职材料",
                "page": 3,
                "chunk_text": "新员工入职需提交以下材料：1. 身份证复印件；2. 学历证明；3. 离职证明。",
                "score": 0.92,
                "rerank_score": 0.95
            },
            {
                "id": 2,
                "document_name": "员工入职与转正管理制度",
                "section": "第三章 试用期管理",
                "page": 5,
                "chunk_text": "试用期为 3 个月，特殊情况可延长至 6 个月。",
                "score": 0.88,
                "rerank_score": 0.90
            }
        ]

        mock_answer = "根据公司制度，新员工入职需要提交身份证复印件、学历证明和离职证明。试用期为 3 个月。"

        return {
            "citations": mock_citations[:top_k],
            "answer_snippet": mock_answer,
            "query": query,
            "total_results": len(mock_citations)
        }
