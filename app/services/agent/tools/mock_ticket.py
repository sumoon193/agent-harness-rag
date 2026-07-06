"""
模拟工单创建工具。

创建模拟的 HR 工单（写入型，必须审批）。
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from app.schemas.user import UserContext

logger = logging.getLogger(__name__)


class MockTicketHandler:
    """
    模拟工单创建工具处理器。

    创建模拟的 HR 工单，用于测试写入型工具的审批流程。
    """

    async def execute(
        self,
        parameters: dict[str, Any],
        user_context: UserContext
    ) -> dict[str, Any]:
        """
        创建模拟工单。

        Args:
            parameters: 工具参数
                - title: 工单标题
                - description: 工单描述
                - priority: 优先级（low/medium/high）
                - category: 类别（入职/转正/报销/请假/其他）
            user_context: 用户上下文

        Returns:
            工单信息
        """
        title = parameters.get("title", "未命名工单")
        description = parameters.get("description", "")
        priority = parameters.get("priority", "medium")
        category = parameters.get("category", "其他")

        logger.info(
            "mock_ticket_created",
            extra={
                "title": title,
                "priority": priority,
                "category": category,
                "user_id": user_context.user_id
            }
        )

        # 生成模拟工单 ID
        ticket_id = f"TK-{uuid.uuid4().hex[:8].upper()}"

        return {
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "priority": priority,
            "category": category,
            "status": "已创建",
            "created_by": user_context.user_id,
            "created_at": "2024-01-15T10:00:00Z",
            "estimated_completion": "3-5 个工作日",
            "message": f"工单 {ticket_id} 已成功创建，HR 团队将尽快处理。"
        }
