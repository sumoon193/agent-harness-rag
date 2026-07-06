"""
Parser Registry。

管理多个 parser 实例，根据 MIME 类型路由到合适的 parser。
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.exceptions import NotFoundError

if TYPE_CHECKING:
    from app.services.parser.base import Parser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """
    Parser 注册表。

    支持按 MIME 类型注册和查找 parser。
    """

    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {}

    def register(self, parser: Parser) -> None:
        """
        注册 parser。

        Args:
            parser: Parser 实例
        """
        for mime_type in parser.supported_types:
            if mime_type in self._parsers:
                logger.warning(
                    "overwriting parser for mime_type",
                    extra={"mime_type": mime_type, "old_parser": type(self._parsers[mime_type]).__name__, "new_parser": type(parser).__name__}
                )
            self._parsers[mime_type] = parser
            logger.info(
                "parser_registered",
                extra={"mime_type": mime_type, "parser": type(parser).__name__}
            )

    def get_parser(self, mime_type: str) -> Parser:
        """
        根据 MIME 类型获取 parser。

        Args:
            mime_type: MIME 类型（如 "text/markdown", "text/plain"）

        Returns:
            匹配的 Parser 实例

        Raises:
            NotFoundError: 找不到支持该 MIME 类型的 parser
        """
        if mime_type not in self._parsers:
            raise NotFoundError(
                f"No parser registered for MIME type: {mime_type}"
            )
        return self._parsers[mime_type]

    def list_parsers(self) -> list[str]:
        """
        列出所有支持的 MIME 类型。

        Returns:
            MIME 类型列表
        """
        return list(self._parsers.keys())

    def has_parser(self, mime_type: str) -> bool:
        """
        检查是否有支持该 MIME 类型的 parser。

        Args:
            mime_type: MIME 类型

        Returns:
            是否有支持的 parser
        """
        return mime_type in self._parsers
