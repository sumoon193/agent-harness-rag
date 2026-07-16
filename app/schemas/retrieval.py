"""
检索结果 Schema。
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.enums import Visibility


class RetrievalResult(BaseModel):
    """
    检索单条结果。

    用于混合检索返回的分块列表。
    """
    chunk_id: str = Field(description="分块 ID")
    document_id: str = Field(description="文档 ID")
    document_version: str = Field(default="v1", description="不可变文档版本 ID")
    chunk_text: str = Field(description="分块文本")
    context_prefix: str = Field(
        default="",
        description="上下文前缀"
    )
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
        description="原始分数"
    )
    # 元数据
    document_name: str = Field(default="", description="文档名称")
    section: str = Field(default="", description="章节名称")
    page: int = Field(default=0, description="页码")
    heading_path: str = Field(default="", description="标题路径")
    tenant_id: str = Field(description="租户 ID")
    department_id: str = Field(description="部门 ID")
    visibility: Visibility = Field(description="可见性级别")

    model_config = {"from_attributes": True}
