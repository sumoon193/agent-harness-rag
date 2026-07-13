"""
文档相关 Schema。
"""
from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field

from app.schemas.enums import DocumentStatus, Visibility


class DocumentCreate(BaseModel):
    """创建文档的请求体。"""
    title: str = Field(description="文档标题")
    tenant_id: str = Field(description="租户 ID")
    department_id: str = Field(description="部门 ID")
    visibility: Visibility = Field(
        default=Visibility.DEPARTMENT,
        description="文档可见性"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="扩展元数据"
    )


class DocumentResponse(BaseModel):
    """文档响应体。"""
    id: str = Field(description="文档 ID，前缀 doc_")
    title: str = Field(description="文档标题")
    file_path: str = Field(description="MinIO 对象键")
    mime_type: str = Field(description="MIME 类型")
    status: DocumentStatus = Field(description="入库状态")
    tenant_id: str = Field(description="租户 ID")
    department_id: str = Field(description="部门 ID")
    visibility: Visibility = Field(description="文档可见性")
    metadata: dict = Field(
        validation_alias=AliasChoices("metadata_", "metadata"),
        description="扩展元数据"
    )
    created_at: datetime = Field(description="创建时间（UTC）")
    updated_at: datetime = Field(description="更新时间（UTC）")

    model_config = {"from_attributes": True}


class DocumentStatusResponse(BaseModel):
    """文档状态查询响应。"""
    id: str = Field(description="文档 ID")
    status: DocumentStatus = Field(description="当前状态")
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="进度百分比（0.0-1.0）"
    )
    error_message: str | None = Field(
        default=None,
        description="失败时的错误信息"
    )
    updated_at: datetime = Field(description="最后更新时间（UTC）")

    model_config = {"from_attributes": True}


class DocumentVersion(BaseModel):
    """不可变文档版本；active 切换不删除历史版本。"""

    id: str = Field(description="版本 ID，前缀 docver_")
    document_id: str
    version: int = Field(ge=1)
    content_hash: str
    is_active: bool = True
    supersedes_version_id: str | None = None
    created_at: datetime
