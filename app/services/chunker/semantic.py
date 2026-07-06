"""
Semantic Chunker。

按语义连贯性生成 child chunk。
"""
from __future__ import annotations

import logging
import re

from app.schemas.chunk import ChunkCreate
from app.services.chunker.base import ChunkConfig

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    语义分块器。

    在 parent chunk 内，按句子边界切分 child chunk。
    """

    async def chunk_parent(
        self,
        parent_chunk: ChunkCreate,
        config: ChunkConfig
    ) -> list[ChunkCreate]:
        """
        将 parent chunk 切分为 child chunks。

        Args:
            parent_chunk: Parent chunk
            config: 分块配置

        Returns:
            Child chunk 列表
        """
        logger.debug(
            "semantic_chunking",
            extra={"parent_id": parent_chunk.document_id, "heading_path": parent_chunk.heading_path}
        )

        # 按句子切分
        sentences = self._split_into_sentences(parent_chunk.chunk_text)

        # 合并句子为合适大小的 chunk
        child_chunks = self._merge_sentences_to_chunks(
            sentences=sentences,
            parent_chunk=parent_chunk,
            config=config
        )

        logger.debug(
            "semantic_chunking_complete",
            extra={"heading_path": parent_chunk.heading_path, "child_count": len(child_chunks)}
        )

        return child_chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        将文本切分为句子。

        Args:
            text: 输入文本

        Returns:
            句子列表
        """
        # 按中英文句号、问号、感叹号、分号切分
        pattern = r"([。！？；.!?;])"
        parts = re.split(pattern, text)

        sentences: list[str] = []
        current = ""

        for part in parts:
            if re.match(pattern, part):
                current += part
                if current.strip():
                    sentences.append(current.strip())
                current = ""
            else:
                current += part

        # 处理最后一个句子
        if current.strip():
            sentences.append(current.strip())

        # 过滤空句子
        return [s for s in sentences if s]

    def _merge_sentences_to_chunks(
        self,
        sentences: list[str],
        parent_chunk: ChunkCreate,
        config: ChunkConfig
    ) -> list[ChunkCreate]:
        """
        将句子合并为合适大小的 chunk。

        Args:
            sentences: 句子列表
            parent_chunk: Parent chunk（用于继承元数据）
            config: 分块配置

        Returns:
            Child chunk 列表
        """
        chunks: list[ChunkCreate] = []
        current_sentences: list[str] = []
        current_token_count = 0

        for sentence in sentences:
            sentence_tokens = len(sentence) // 2  # 简单估算

            # 检查是否需要开始新的 chunk
            if current_sentences and (current_token_count + sentence_tokens > config.max_child_tokens):
                # 保存当前 chunk
                chunk = self._create_child_chunk(
                    sentences=current_sentences,
                    parent_chunk=parent_chunk
                )
                chunks.append(chunk)

                # 开始新 chunk（保留 overlap）
                overlap_sentences = self._get_overlap_sentences(current_sentences, config.overlap_tokens)
                current_sentences = overlap_sentences
                current_token_count = sum(len(s) // 2 for s in overlap_sentences)

            current_sentences.append(sentence)
            current_token_count += sentence_tokens

        # 处理最后一个 chunk
        if current_sentences:
            # 检查是否达到最小长度
            if current_token_count >= config.min_child_tokens or not chunks:
                chunk = self._create_child_chunk(
                    sentences=current_sentences,
                    parent_chunk=parent_chunk
                )
                chunks.append(chunk)
            else:
                # 合并到上一个 chunk
                if chunks:
                    last_chunk = chunks[-1]
                    combined_text = last_chunk.chunk_text + "\n\n" + "\n".join(current_sentences)
                    chunks[-1] = ChunkCreate(
                        document_id=last_chunk.document_id,
                        chunk_text=combined_text,
                        context_prefix=last_chunk.context_prefix,
                        full_text=last_chunk.context_prefix + combined_text,
                        parent_id=last_chunk.parent_id,
                        chunk_type=last_chunk.chunk_type,
                        heading_path=last_chunk.heading_path,
                        page_numbers=last_chunk.page_numbers,
                        token_count=len(combined_text) // 2,
                        tenant_id=last_chunk.tenant_id,
                        department_id=last_chunk.department_id,
                        visibility=last_chunk.visibility,
                        acl_metadata=last_chunk.acl_metadata
                    )

        return chunks

    def _get_overlap_sentences(self, sentences: list[str], overlap_tokens: int) -> list[str]:
        """获取用于重叠的句子。"""
        overlap_sentences: list[str] = []
        token_count = 0

        # 从后往前取句子
        for sentence in reversed(sentences):
            sentence_tokens = len(sentence) // 2
            if token_count + sentence_tokens > overlap_tokens:
                break
            overlap_sentences.insert(0, sentence)
            token_count += sentence_tokens

        return overlap_sentences

    def _create_child_chunk(
        self,
        sentences: list[str],
        parent_chunk: ChunkCreate
    ) -> ChunkCreate:
        """
        创建 child chunk。

        Args:
            sentences: 句子列表
            parent_chunk: Parent chunk（用于继承元数据）

        Returns:
            Child chunk
        """
        chunk_text = "\n".join(sentences)
        token_count = len(chunk_text) // 2

        return ChunkCreate(
            document_id=parent_chunk.document_id,
            chunk_text=chunk_text,
            context_prefix="",
            full_text=chunk_text,
            parent_id=parent_chunk.document_id,  # 临时 ID，后续由 parent_child builder 替换
            chunk_type="child",
            heading_path=parent_chunk.heading_path,
            page_numbers=parent_chunk.page_numbers,
            token_count=token_count,
            tenant_id=parent_chunk.tenant_id,
            department_id=parent_chunk.department_id,
            visibility=parent_chunk.visibility,
            acl_metadata=parent_chunk.acl_metadata
        )
