"""
Structural Chunker。

按标题层级切分 parent chunk。
"""
from __future__ import annotations

import logging

from app.schemas.chunk import ChunkCreate
from app.schemas.enums import Visibility
from app.services.chunker.base import ChunkConfig
from app.services.parser.base import Block, BlockType, ParsedDocument

logger = logging.getLogger(__name__)


class StructuralChunker:
    """
    结构化分块器。

    按标题层级切分 parent chunk，保留文档结构。
    """

    async def chunk(
        self,
        parsed_doc: ParsedDocument,
        config: ChunkConfig
    ) -> list[ChunkCreate]:
        """
        按结构分块。

        Args:
            parsed_doc: 解析后的文档
            config: 分块配置

        Returns:
            Parent chunk 列表
        """
        logger.info(
            "structural_chunking",
            extra={"document_id": parsed_doc.document_id, "block_count": len(parsed_doc.blocks)}
        )

        chunks: list[ChunkCreate] = []
        current_section: list[Block] = []
        current_heading_path = ""

        for block in parsed_doc.blocks:
            # 遇到标题时，保存之前的 section
            if block.block_type == BlockType.HEADING and current_section:
                chunk = self._create_parent_chunk(
                    document_id=parsed_doc.document_id,
                    heading_path=current_heading_path,
                    blocks=current_section,
                    metadata=parsed_doc.metadata
                )
                chunks.append(chunk)
                current_section = []

            # 更新标题路径
            if block.block_type == BlockType.HEADING:
                current_heading_path = block.heading_path

            current_section.append(block)

        # 处理最后一个 section
        if current_section:
            chunk = self._create_parent_chunk(
                document_id=parsed_doc.document_id,
                heading_path=current_heading_path,
                blocks=current_section,
                metadata=parsed_doc.metadata
            )
            chunks.append(chunk)

        logger.info(
            "structural_chunking_complete",
            extra={"document_id": parsed_doc.document_id, "parent_count": len(chunks)}
        )

        return chunks

    def _create_parent_chunk(
        self,
        document_id: str,
        heading_path: str,
        blocks: list[Block],
        metadata: dict
    ) -> ChunkCreate:
        """
        创建 parent chunk。

        Args:
            document_id: 文档 ID
            heading_path: 标题路径
            blocks: 内容块列表
            metadata: 文档元数据

        Returns:
            Parent chunk
        """
        # 合并所有 block 的文本
        chunk_text = "\n\n".join(block.text for block in blocks)

        # 收集页码
        page_numbers = sorted(set(block.page_number for block in blocks))

        # 估算 token 数（简单按字符数 / 2）
        token_count = len(chunk_text) // 2

        # 从 metadata 提取 ACL 信息
        tenant_id = metadata.get("tenant_id", "default")
        department_id = metadata.get("department_id", "default")
        visibility_str = metadata.get("visibility", "department")
        visibility = Visibility(visibility_str) if visibility_str in Visibility.__members__.values() else Visibility.DEPARTMENT

        return ChunkCreate(
            document_id=document_id,
            chunk_text=chunk_text,
            context_prefix="",
            full_text=chunk_text,
            parent_id=None,
            chunk_type="parent",
            heading_path=heading_path,
            page_numbers=page_numbers,
            token_count=token_count,
            tenant_id=tenant_id,
            department_id=department_id,
            visibility=visibility,
            acl_metadata=metadata
        )
