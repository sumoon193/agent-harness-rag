"""
用户上下文 Schema。
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """
    用户上下文，用于 ACL 权限控制和审计。

    包含用户身份、租户、部门和权限信息。
    """
    user_id: str = Field(description="用户 ID，前缀 user_")
    tenant_id: str = Field(description="租户 ID")
    department_ids: list[str] = Field(
        default_factory=list,
        description="用户所属部门 ID 列表"
    )
    role: str = Field(description="用户角色（如 admin, hr, employee）")
    permissions: list[str] = Field(
        default_factory=list,
        description="用户权限列表（如 hr.document.read, hr.ticket.write）"
    )

    model_config = {"from_attributes": True}
