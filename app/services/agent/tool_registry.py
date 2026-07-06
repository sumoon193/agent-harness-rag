"""
Tool Registry。

注册和管理工具定义及处理器。
"""
from __future__ import annotations

import logging

from app.core.exceptions import NotFoundError
from app.schemas.tool import ToolDefinition
from app.services.agent.tools.base import ToolHandler

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表。

    管理工具定义和对应的处理器。
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, tool: ToolDefinition, handler: ToolHandler) -> None:
        """
        注册工具。

        Args:
            tool: 工具定义
            handler: 工具处理器
        """
        if tool.name in self._tools:
            logger.warning(
                "overwriting_tool",
                extra={"tool_name": tool.name}
            )

        self._tools[tool.name] = tool
        self._handlers[tool.name] = handler

        logger.info(
            "tool_registered",
            extra={
                "tool_name": tool.name,
                "risk_level": tool.risk_level.value,
                "requires_approval": tool.requires_approval
            }
        )

    def get_tool(self, name: str) -> ToolDefinition:
        """
        获取工具定义。

        Args:
            name: 工具名称

        Returns:
            工具定义

        Raises:
            NotFoundError: 工具不存在
        """
        if name not in self._tools:
            raise NotFoundError(f"Tool not found: {name}")
        return self._tools[name]

    def get_handler(self, name: str) -> ToolHandler:
        """
        获取工具处理器。

        Args:
            name: 工具名称

        Returns:
            工具处理器

        Raises:
            NotFoundError: 工具不存在
        """
        if name not in self._handlers:
            raise NotFoundError(f"Tool handler not found: {name}")
        return self._handlers[name]

    def list_tools(self) -> list[ToolDefinition]:
        """
        列出所有工具。

        Returns:
            工具定义列表
        """
        return list(self._tools.values())

    def has_tool(self, name: str) -> bool:
        """
        检查工具是否存在。

        Args:
            name: 工具名称

        Returns:
            是否存在
        """
        return name in self._tools

    def get_read_tools(self) -> list[ToolDefinition]:
        """
        获取所有读取型工具。

        Returns:
            读取型工具列表
        """
        return [t for t in self._tools.values() if not t.requires_approval]

    def get_write_tools(self) -> list[ToolDefinition]:
        """
        获取所有写入型工具。

        Returns:
            写入型工具列表
        """
        return [t for t in self._tools.values() if t.requires_approval]
