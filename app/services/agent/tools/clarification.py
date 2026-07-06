"""
澄清问题工具。

当用户问题不够清晰时，生成澄清问题。
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.user import UserContext

logger = logging.getLogger(__name__)


class ClarificationHandler:
    """
    澄清问题工具处理器。

    当用户问题不够清晰时，生成澄清问题。
    """

    async def execute(
        self,
        parameters: dict[str, Any],
        user_context: UserContext
    ) -> dict[str, Any]:
        """
        生成澄清问题。

        Args:
            parameters: 工具参数
                - question: 原始问题
                - context: 上下文信息（可选）
            user_context: 用户上下文

        Returns:
            澄清问题
        """
        question = parameters.get("question", "")
        context = parameters.get("context", "")

        logger.info(
            "clarification_generated",
            extra={"question": question[:50], "user_id": user_context.user_id}
        )

        # 根据问题类型生成澄清问题
        clarification = self._generate_clarification(question, context)

        return {
            "original_question": question,
            "clarified_question": clarification,
            "context": context,
            "suggestion": "请提供更多细节以便我更好地回答您的问题。"
        }

    def _generate_clarification(self, question: str, context: str) -> str:
        """
        生成澄清问题。

        Args:
            question: 原始问题
            context: 上下文

        Returns:
            澄清问题
        """
        # 简单规则生成
        if "入职" in question and "材料" not in question:
            return "您是想了解入职需要准备哪些材料，还是入职后的流程？"
        elif "转正" in question and "条件" not in question:
            return "您是想了解转正的条件，还是转正的流程？"
        elif "报销" in question and "流程" not in question:
            return "您是想了解报销的流程，还是报销的标准？"
        elif "请假" in question and "天数" not in question:
            return "您是想了解请假的流程，还是各类假期的天数？"
        else:
            return f"关于「{question}」，您能提供更多信息吗？比如具体场景或时间范围。"
