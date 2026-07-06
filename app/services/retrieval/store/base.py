"""
Store Protocol 和 ACLFilter。

定义向量存储和 BM25 存储接口。
"""
from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from app.schemas.chunk import ChunkCreate
from app.schemas.enums import Visibility
from app.schemas.retrieval import RetrievalResult


class ACLFilter(BaseModel):
    """
    ACL 过滤器。

    用于检索前过滤无权限的 chunk。
    """
    tenant_id: str = Field(description="租户 ID")
    department_ids: list[str] = Field(description="部门 ID 列表")
    allowed_visibility: list[Visibility] = Field(
        description="允许的可见性级别列表"
    )


class VectorStore(Protocol):
    """
    向量存储接口。

    所有向量存储必须实现此接口。
    """

    async def add_chunks(
        self,
        chunks: list[ChunkCreate],
        embeddings: list[list[float]]
    ) -> None:
        """
        添加 chunks 到向量存储。

        Args:
            chunks: 分块列表
            embeddings: 对应的向量列表
        """
        ...

    async def search(
        self,
        query_embedding: list[float],
        acl_filter: ACLFilter,
        top_k: int = 10
    ) -> list[RetrievalResult]:
        """
        向量检索。

        Args:
            query_embedding: 查询向量
            acl_filter: ACL 过滤器
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        ...

    async def delete_by_document(self, document_id: str) -> None:
        """
        删除指定文档的所有 chunks。

        Args:
            document_id: 文档 ID
        """
        ...


class BM25Store(Protocol):
    """
    BM25 存储接口。

    所有 BM25 存储必须实现此接口。
    """

    async def add_chunks(self, chunks: list[ChunkCreate]) -> None:
        """
        添加 chunks 到 BM25 存储。

        Args:
            chunks: 分块列表
        """
        ...

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
            检索结果列表
        """
        ...

    async def delete_by_document(self, document_id: str) -> None:
        """
        删除指定文档的所有 chunks。

        Args:
            document_id: 文档 ID
        """
        ...
