"""
In-Memory BM25 Store。

使用 TF-IDF 简化实现，构建倒排索引支持关键词检索。
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter, defaultdict

from app.schemas.chunk import ChunkCreate
from app.schemas.enums import Visibility
from app.schemas.retrieval import RetrievalResult
from app.services.ingestion.identity import stable_chunk_id
from app.services.retrieval.store.base import ACLFilter

logger = logging.getLogger(__name__)


class InMemoryBM25Store:
    """
    In-Memory BM25 存储。

    使用 TF-IDF 简化实现，支持中文分词（简单按字符切分）。
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """
        初始化 BM25 存储。

        Args:
            k1: BM25 参数 k1
            b: BM25 参数 b
        """
        self._k1 = k1
        self._b = b
        self._chunks: list[ChunkCreate] = []
        self._doc_lengths: list[int] = []
        self._avg_doc_length: float = 0.0
        self._inverted_index: dict[str, list[tuple[int, int]]] = defaultdict(list)  # token -> [(doc_idx, tf)]
        self._doc_count: int = 0
        self._idf_cache: dict[str, float] = {}

    async def add_chunks(self, chunks: list[ChunkCreate]) -> None:
        """
        添加 chunks 到 BM25 存储。

        Args:
            chunks: 分块列表
        """
        logger.info(
            "adding_chunks_to_bm25_store",
            extra={"count": len(chunks)}
        )

        for ordinal, chunk in enumerate(chunks, start=1):
            stored_chunk = chunk
            if not chunk.id:
                stored_chunk = chunk.model_copy(
                    update={
                        "id": stable_chunk_id(
                            document_id=chunk.document_id,
                            document_version=chunk.document_version,
                            heading_path=chunk.heading_path,
                            ordinal=ordinal,
                            chunk_text=chunk.chunk_text,
                        )
                    }
                )
            doc_idx = len(self._chunks)
            self._chunks.append(stored_chunk)

            # 分词
            tokens = self._tokenize(stored_chunk.full_text or stored_chunk.chunk_text)
            self._doc_lengths.append(len(tokens))

            # 统计词频
            token_counts = Counter(tokens)

            # 更新倒排索引
            for token, tf in token_counts.items():
                self._inverted_index[token].append((doc_idx, tf))

        # 更新统计信息
        self._doc_count = len(self._chunks)
        if self._doc_count > 0:
            self._avg_doc_length = sum(self._doc_lengths) / self._doc_count

        # 清除 IDF 缓存
        self._idf_cache.clear()

        logger.info(
            "bm25_store_updated",
            extra={"doc_count": self._doc_count, "avg_doc_length": self._avg_doc_length}
        )

    async def search(
        self,
        query: str,
        acl_filter: ACLFilter,
        top_k: int = 10
    ) -> list[RetrievalResult]:
        """
        BM25 检索。

        Args:
            query: 查询文本
            acl_filter: ACL 过滤器
            top_k: 返回结果数量

        Returns:
            检索结果列表（按 BM25 分数降序）
        """
        logger.info(
            "bm25_search",
            extra={"query": query[:50], "top_k": top_k, "doc_count": self._doc_count}
        )

        # 分词
        query_tokens = self._tokenize(query)

        # 计算每个文档的 BM25 分数
        scores: dict[int, float] = defaultdict(float)

        for token in query_tokens:
            if token not in self._inverted_index:
                continue

            idf = self._get_idf(token)

            for doc_idx, tf in self._inverted_index[token]:
                doc_length = self._doc_lengths[doc_idx]

                # BM25 公式
                numerator = tf * (self._k1 + 1)
                denominator = tf + self._k1 * (1 - self._b + self._b * doc_length / self._avg_doc_length)
                scores[doc_idx] += idf * numerator / denominator

        # 按分数降序排序
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # 取 top_k（考虑 ACL 过滤）
        results: list[RetrievalResult] = []
        for doc_idx, score in sorted_docs:
            if len(results) >= top_k:
                break

            chunk = self._chunks[doc_idx]

            # ACL 过滤
            if not self._check_acl(chunk, acl_filter):
                continue

            # 归一化分数到 [0, 1]
            normalized_score = min(score / (score + 1), 1.0)

            result = RetrievalResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_version=chunk.document_version,
                chunk_text=chunk.chunk_text,
                context_prefix=chunk.context_prefix,
                score=normalized_score,
                rerank_score=0.0,
                raw_score=score,
                document_name="",
                section="",
                page=chunk.page_numbers[0] if chunk.page_numbers else 0,
                heading_path=chunk.heading_path,
                tenant_id=chunk.tenant_id,
                department_id=chunk.department_id,
                visibility=chunk.visibility
            )
            results.append(result)

        logger.info(
            "bm25_search_complete",
            extra={"returned": len(results)}
        )

        return results

    async def delete_by_document(self, document_id: str) -> None:
        """
        删除指定文档的所有 chunks。

        Args:
            document_id: 文档 ID
        """
        logger.info(
            "deleting_bm25_chunks_by_document",
            extra={"document_id": document_id}
        )

        # 找到需要删除的索引
        indices_to_remove = [
            i for i, chunk in enumerate(self._chunks)
            if chunk.document_id == document_id
        ]

        if not indices_to_remove:
            return

        # 重建索引（简单实现）
        remaining_chunks = [
            chunk for i, chunk in enumerate(self._chunks)
            if i not in indices_to_remove
        ]

        # 清空并重新添加
        self._chunks.clear()
        self._doc_lengths.clear()
        self._inverted_index.clear()
        self._doc_count = 0
        self._avg_doc_length = 0.0
        self._idf_cache.clear()

        if remaining_chunks:
            await self.add_chunks(remaining_chunks)

        logger.info(
            "deleted_bm25_chunks",
            extra={"document_id": document_id, "count": len(indices_to_remove)}
        )

    def _tokenize(self, text: str) -> list[str]:
        """
        分词（简单实现）。

        支持中文（按字符切分）和英文（按空格切分）。

        Args:
            text: 输入文本

        Returns:
            token 列表
        """
        # 转小写
        text = text.lower()

        # 提取中文字符和英文单词
        tokens = []

        # 中文字符
        chinese_chars = re.findall(r"[一-鿿]", text)
        tokens.extend(chinese_chars)

        # 英文单词
        english_words = re.findall(r"[a-z]+", text)
        tokens.extend(english_words)

        # 数字
        numbers = re.findall(r"\d+", text)
        tokens.extend(numbers)

        return tokens

    def _get_idf(self, token: str) -> float:
        """
        计算 IDF 值。

        Args:
            token: token

        Returns:
            IDF 值
        """
        if token in self._idf_cache:
            return self._idf_cache[token]

        # 包含该 token 的文档数
        df = len(self._inverted_index.get(token, []))

        # IDF 公式（带平滑）
        idf = math.log((self._doc_count - df + 0.5) / (df + 0.5) + 1)

        self._idf_cache[token] = idf
        return idf

    def _check_acl(self, chunk: ChunkCreate, acl_filter: ACLFilter) -> bool:
        """
        检查 chunk 是否满足 ACL 过滤条件。

        Args:
            chunk: 分块
            acl_filter: ACL 过滤器

        Returns:
            是否满足过滤条件
        """
        # 检查租户
        if chunk.tenant_id != acl_filter.tenant_id:
            return False

        # 检查可见性
        if chunk.visibility not in acl_filter.allowed_visibility:
            return False

        # public 表示同租户公开，不受部门过滤限制
        if chunk.visibility == Visibility.PUBLIC:
            return True

        # 检查部门
        if chunk.department_id not in acl_filter.department_ids:
            return False

        return True
