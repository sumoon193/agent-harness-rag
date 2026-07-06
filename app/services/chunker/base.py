"""
Chunker 基础 Protocol 和配置。

定义文档分块的接口和配置。
"""
from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from app.schemas.chunk import ChunkCreate
from app.services.parser.base import ParsedDocument


class ChunkConfig(BaseModel):
    """
    分块配置。

    控制分块行为的参数。
    """
    max_parent_tokens: int = Field(
        default=1000,
        description="Parent chunk 最大 token 数"
    )
    max_child_tokens: int = Field(
        default=400,
        description="Child chunk 目标 token 数"
    )
    min_child_tokens: int = Field(
        default=100,
        description="Child chunk 最小 token 数"
    )
    overlap_tokens: int = Field(
        default=50,
        description="重叠 token 数"
    )
    preserve_tables: bool = Field(
        default=True,
        description="表格是否作为原子单元"
    )


class Chunker(Protocol):
    """
    Chunker 接口。

    所有 chunker 必须实现此接口。
    """

    async def chunk(
        self,
        parsed_doc: ParsedDocument,
        config: ChunkConfig
    ) -> list[ChunkCreate]:
        """
        对解析后的文档进行分块。

        Args:
            parsed_doc: 解析后的文档
            config: 分块配置

        Returns:
            分块列表
        """
        ...
