"""
Exporter 接口。

定义 Trace 导出器接口。
"""
from __future__ import annotations

from typing import Protocol

from app.services.observability.context import TraceContext
from app.services.observability.span import Span


class TraceExporter(Protocol):
    """
    Trace 导出器接口。

    所有导出器必须实现此接口。
    """

    def export(self, spans: list[Span], context: TraceContext) -> None:
        """
        导出 Span。

        Args:
            spans: Span 列表
            context: Trace 上下文
        """
        ...
