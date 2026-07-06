"""
用户档案查询工具。

模拟查询用户档案信息。
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.user import UserContext

logger = logging.getLogger(__name__)


class UserProfileHandler:
    """
    用户档案查询工具处理器。

    模拟查询用户档案信息。
    """

    async def execute(
        self,
        parameters: dict[str, Any],
        user_context: UserContext
    ) -> dict[str, Any]:
        """
        查询用户档案。

        Args:
            parameters: 工具参数
                - user_id: 用户 ID（可选，默认当前用户）
            user_context: 用户上下文

        Returns:
            用户档案信息
        """
        user_id = parameters.get("user_id", user_context.user_id)

        logger.info(
            "user_profile_queried",
            extra={"queried_user_id": user_id, "requester_id": user_context.user_id}
        )

        # 模拟用户档案
        mock_profile = {
            "user_id": user_id,
            "name": "张三",
            "department": "技术部",
            "position": "高级工程师",
            "entry_date": "2024-01-15",
            "probation_end_date": "2024-04-15",
            "status": "在职",
            "manager": "李四",
            "hr_contact": "王五"
        }

        return {
            "user_info": mock_profile,
            "user_id": user_id
        }
