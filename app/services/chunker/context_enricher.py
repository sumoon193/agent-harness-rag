"""
Contextual Prefix Generator。

为每个 chunk 生成检索增强前缀。
"""
from __future__ import annotations

import logging
import re

from app.schemas.chunk import ChunkCreate

logger = logging.getLogger(__name__)


class ContextEnricher:
    """
    上下文前缀生成器。

    为每个 chunk 生成包含文档名、章节路径和片段主题的前缀。
    """

    def enrich(
        self,
        chunks: list[ChunkCreate],
        document_name: str
    ) -> list[ChunkCreate]:
        """
        为所有 chunks 生成上下文前缀。

        Args:
            chunks: 分块列表
            document_name: 文档名称

        Returns:
            带有 context_prefix 的分块列表
        """
        logger.info(
            "enriching_context",
            extra={"chunk_count": len(chunks), "document_name": document_name}
        )

        enriched_chunks: list[ChunkCreate] = []

        for chunk in chunks:
            context_prefix = self._generate_prefix(
                document_name=document_name,
                heading_path=chunk.heading_path,
                chunk_text=chunk.chunk_text
            )

            enriched_chunk = ChunkCreate(
                document_id=chunk.document_id,
                chunk_text=chunk.chunk_text,
                context_prefix=context_prefix,
                full_text=context_prefix + " " + chunk.chunk_text,
                parent_id=chunk.parent_id,
                chunk_type=chunk.chunk_type,
                heading_path=chunk.heading_path,
                page_numbers=chunk.page_numbers,
                token_count=chunk.token_count + len(context_prefix) // 2,
                tenant_id=chunk.tenant_id,
                department_id=chunk.department_id,
                visibility=chunk.visibility,
                acl_metadata=chunk.acl_metadata
            )
            enriched_chunks.append(enriched_chunk)

        logger.info(
            "enriching_context_complete",
            extra={"chunk_count": len(enriched_chunks)}
        )

        return enriched_chunks

    def _generate_prefix(
        self,
        document_name: str,
        heading_path: str,
        chunk_text: str
    ) -> str:
        """
        生成单个 chunk 的上下文前缀。

        Args:
            document_name: 文档名称
            heading_path: 标题路径
            chunk_text: 分块文本

        Returns:
            上下文前缀
        """
        # 提取主题描述
        topic = self._extract_topic(chunk_text)

        # 构建前缀
        parts = [f"本片段来自《{document_name}》"]

        if heading_path:
            parts.append(heading_path)

        if topic:
            parts.append(f"，{topic}")

        prefix = "".join(parts) + "。"

        # 限制前缀长度（50-100 tokens，约 100-200 字符）
        if len(prefix) > 200:
            prefix = prefix[:197] + "..."

        return prefix

    def _extract_topic(self, text: str) -> str:
        """
        从文本中提取主题。

        V1 版本使用简单规则，后续可接入 LLM。

        Args:
            text: 文本内容

        Returns:
            主题描述
        """
        # 取前 50 个字符作为主题
        first_sentence = text.split("。")[0] if "。" in text else text[:50]

        # 清理换行和多余空格
        topic = re.sub(r"\s+", " ", first_sentence).strip()

        # 截断到 50 个字符
        if len(topic) > 50:
            topic = topic[:47] + "..."

        return topic
