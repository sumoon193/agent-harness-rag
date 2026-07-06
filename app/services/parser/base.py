"""
Parser 基础 Schema 和 Protocol。

定义文档解析的接口和输出格式。
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class BlockType(StrEnum):
    """
    Block 类型枚举。

    用于标识解析后的不同类型的内容块。
    """
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    IMAGE_CAPTION = "image_caption"
    CODE = "code"
    PAGE_BREAK = "page_break"


class Block(BaseModel):
    """
    解析后的单个内容块。

    包含文本内容、位置信息和元数据。
    """
    block_id: str = Field(description="Block 唯一 ID")
    block_type: BlockType = Field(description="Block 类型")
    text: str = Field(description="Block 文本内容")
    page_number: int = Field(default=1, description="所在页码")
    heading_path: str = Field(
        default="",
        description="标题路径，如 'HR制度 > 第三章 > 3.2 请假流程'"
    )
    order_index: int = Field(description="在文档中的顺序索引")
    source_bbox: dict[str, Any] | None = Field(
        default=None,
        description="源文档中的位置信息（可选）"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="扩展元数据"
    )

    model_config = {"from_attributes": True}


class ParsedDocument(BaseModel):
    """
    解析后的文档。

    包含文档的结构化内容和元数据。
    """
    document_id: str = Field(description="文档 ID")
    source_name: str = Field(description="原始文件名")
    title: str = Field(description="文档标题")
    blocks: list[Block] = Field(description="内容块列表")
    pages: list[int] = Field(description="页码列表")
    tables: list[Block] = Field(
        default_factory=list,
        description="表格类型的 block"
    )
    images: list[Block] = Field(
        default_factory=list,
        description="图片说明类型的 block"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="文档元数据"
    )
    parser_used: str = Field(description="使用的 parser 名称")
    total_pages: int = Field(default=1, description="总页数")

    model_config = {"from_attributes": True}


class Parser(Protocol):
    """
    Parser 接口。

    所有 parser 必须实现此接口。
    """

    supported_types: set[str]  # 支持的 MIME 类型

    async def parse(
        self,
        file_path: str,
        document_id: str,
        metadata: dict[str, Any]
    ) -> ParsedDocument:
        """
        解析文档。

        Args:
            file_path: 文件路径
            document_id: 文档 ID
            metadata: 文档元数据

        Returns:
            解析后的文档结构
        """
        ...
