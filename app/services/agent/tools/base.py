"""
工具基类。

定义工具处理器接口。
"""
from __future__ import annotations

from typing import Any, Protocol

from app.schemas.user import UserContext


class ToolHandler(Protocol):
    """
    工具处理器接口。

    所有工具处理器必须实现此接口。
    """

    async def execute(
        self,
        parameters: dict[str, Any],
        user_context: UserContext
    ) -> dict[str, Any]:
        """
        执行工具。

        Args:
            parameters: 工具参数
            user_context: 用户上下文

        Returns:
            工具执行结果
        """
        ...
