"""程序性 Skill manifest Schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.enums import SkillStatus


class SkillManifest(BaseModel):
    """可校验、可晋级、可撤销的 Skill 版本。"""

    id: str = Field(description="Skill ID，前缀 skill_")
    name: str
    version: str
    content: str = Field(exclude=True)
    checksum: str
    source_uri: str
    allowed_tools: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    status: SkillStatus = SkillStatus.DRAFT
    eval_score: float | None = Field(default=None, ge=0.0, le=1.0)
    revoke_reason: str | None = None
    created_at: datetime
    updated_at: datetime
