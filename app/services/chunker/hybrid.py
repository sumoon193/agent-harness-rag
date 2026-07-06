"""
Hybrid Chunker。

编排 Structural → Semantic → Contextual 流程。
"""
from __future__ import annotations

import logging
import uuid

from app.schemas.chunk import ChunkCreate
from app.services.chunker.base import ChunkConfig
from app.services.chunker.context_enricher import ContextEnricher
from app.services.chunker.semantic import SemanticChunker
from app.services.chunker.structural import StructuralChunker
from app.services.parser.base import ParsedDocument

logger = logging.getLogger(__name__)


class HybridChunker:
    """
    混合分块器。

    编排完整的分块流程：
    1. Structural Chunking（按标题切分 parent chunk）
    2. Semantic Chunking（按语义切分 child chunk）
    3. Contextual Enrichment（生成上下文前缀）
    4. Parent-Child Relationship（建立父子关系）
    """

    def __init__(self) -> None:
        self._structural = StructuralChunker()
        self._semantic = SemanticChunker()
        self._enricher = ContextEnricher()

    async def chunk(
        self,
        parsed_doc: ParsedDocument,
        config: ChunkConfig | None = None
    ) -> list[ChunkCreate]:
        """
        执行完整的分块流程。

        Args:
            parsed_doc: 解析后的文档
            config: 分块配置（可选，使用默认值）

        Returns:
            Parent 和 Child chunk 列表
        """
        if config is None:
            config = ChunkConfig()

        logger.info(
            "hybrid_chunking_start",
            extra={"document_id": parsed_doc.document_id, "source_name": parsed_doc.source_name}
        )

        # Step 1: Structural Chunking（生成 parent chunks）
        parent_chunks = await self._structural.chunk(parsed_doc, config)

        logger.info(
            "structural_chunking_done",
            extra={"parent_count": len(parent_chunks)}
        )

        # Step 2: Semantic Chunking（生成 child chunks）
        all_chunks: list[ChunkCreate] = []

        for parent in parent_chunks:
            # 为 parent 生成唯一 ID
            parent_id = f"chunk_{uuid.uuid4().hex[:12]}"

            # 更新 parent chunk
            parent_with_id = ChunkCreate(
                document_id=parent.document_id,
                chunk_text=parent.chunk_text,
                context_prefix="",
                full_text=parent.chunk_text,
                parent_id=None,
                chunk_type="parent",
                heading_path=parent.heading_path,
                page_numbers=parent.page_numbers,
                token_count=parent.token_count,
                tenant_id=parent.tenant_id,
                department_id=parent.department_id,
                visibility=parent.visibility,
                acl_metadata=parent.acl_metadata
            )

            # 生成 child chunks
            child_chunks = await self._semantic.chunk_parent(parent, config)

            # 设置 child 的 parent_id
            children_with_parent = [
                ChunkCreate(
                    document_id=child.document_id,
                    chunk_text=child.chunk_text,
                    context_prefix="",
                    full_text=child.chunk_text,
                    parent_id=parent_id,
                    chunk_type="child",
                    heading_path=child.heading_path,
                    page_numbers=child.page_numbers,
                    token_count=child.token_count,
                    tenant_id=child.tenant_id,
                    department_id=child.department_id,
                    visibility=child.visibility,
                    acl_metadata=child.acl_metadata
                )
                for child in child_chunks
            ]

            all_chunks.append(parent_with_id)
            all_chunks.extend(children_with_parent)

        logger.info(
            "semantic_chunking_done",
            extra={"total_chunks": len(all_chunks)}
        )

        # Step 3: Contextual Enrichment
        enriched_chunks = self._enricher.enrich(
            chunks=all_chunks,
            document_name=parsed_doc.source_name
        )

        logger.info(
            "hybrid_chunking_complete",
            extra={
                "document_id": parsed_doc.document_id,
                "total_chunks": len(enriched_chunks),
                "parent_count": sum(1 for c in enriched_chunks if c.chunk_type == "parent"),
                "child_count": sum(1 for c in enriched_chunks if c.chunk_type == "child")
            }
        )

        return enriched_chunks
