"""
分块与证据相关 Schema。
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.enums import Visibility


class ChunkCreate(BaseModel):
    """
    创建分块的内部 Schema。

    用于 chunker 输出，不对外暴露。
    """
    document_id: str = Field(description="所属文档 ID")
    chunk_text: str = Field(description="原始分块文本")
    context_prefix: str = Field(
        default="",
        description="生成的上下文前缀（50-100 token）"
    )
    full_text: str = Field(
        default="",
        description="context_prefix + chunk_text（用于 embedding）"
    )
    parent_id: str | None = Field(
        default=None,
        description="Parent chunk ID（parent 本身为 None）"
    )
    chunk_type: str = Field(
        default="child",
        description="分块类型：parent 或 child"
    )
    heading_path: str = Field(
        default="",
        description="标题路径"
    )
    page_numbers: list[int] = Field(
        default_factory=list,
        description="所在页码列表"
    )
    token_count: int = Field(
        default=0,
        description="分块 token 数量"
    )
    # ACL 元数据
    tenant_id: str = Field(description="租户 ID")
    department_id: str = Field(description="部门 ID")
    visibility: Visibility = Field(description="可见性级别")
    acl_metadata: dict = Field(
        default_factory=dict,
        description="扩展 ACL 元数据"
    )

    model_config = {"from_attributes": True}


class DocumentChunk(BaseModel):
    """
    文档分块。

    包含原始文本、上下文前缀、Parent-Child 关系和 ACL 元数据。
    """
    id: str = Field(description="分块 ID，前缀 chunk_")
    document_id: str = Field(description="所属文档 ID")
    chunk_text: str = Field(description="原始分块文本")
    context_prefix: str = Field(
        default="",
        description="生成的上下文前缀（50-100 token）"
    )
    full_text: str = Field(
        default="",
        description="context_prefix + chunk_text（用于 embedding）"
    )
    parent_id: str | None = Field(
        default=None,
        description="Parent chunk ID（parent 本身为 None）"
    )
    chunk_type: str = Field(
        default="child",
        description="分块类型：parent 或 child"
    )
    heading_path: str = Field(
        default="",
        description="标题路径，如 'HR制度 > 第三章 > 3.2 请假流程'"
    )
    page_numbers: list[int] = Field(
        default_factory=list,
        description="所在页码列表"
    )
    token_count: int = Field(
        default=0,
        description="分块 token 数量"
    )
    # ACL 元数据（从文档继承）
    tenant_id: str = Field(description="租户 ID")
    department_id: str = Field(description="部门 ID")
    visibility: Visibility = Field(description="可见性级别")
    acl_metadata: dict = Field(
        default_factory=dict,
        description="扩展 ACL 元数据"
    )

    model_config = {"from_attributes": True}


class Citation(BaseModel):
    """
    引用来源。

    用于答案生成时的证据引用标注。
    """
    id: int = Field(description="引用编号（答案中的 [1][2]）")
    document_name: str = Field(description="文档名称")
    section: str = Field(description="章节名称")
    page: int = Field(description="页码")
    chunk_text: str = Field(description="分块文本")
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="检索分数（0.0-1.0）"
    )
    rerank_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Rerank 分数（0.0-1.0）"
    )
    raw_score: float | None = Field(
        default=None,
        description="原始分数（未归一化）"
    )

    model_config = {"from_attributes": True}


class EvidenceBundle(BaseModel):
    """
    证据包。

    包含评分后的相关证据列表。
    """
    evidence_list: list[Citation] = Field(
        description="相关证据列表"
    )
    total_count: int = Field(
        description="总证据数量"
    )
    query_coverage_score: float = Field(
        ge=0.0,
        le=1.0,
        description="查询覆盖率分数（0.0-1.0）"
    )

    model_config = {"from_attributes": True}
