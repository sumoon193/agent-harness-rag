"""Skill 生命周期、供应链校验和评测晋级。"""
from __future__ import annotations

import hashlib
import uuid

from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.enums import SkillStatus
from app.schemas.skill import SkillManifest
from app.services.runtime.clock import Clock, SystemClock


class SkillRegistry:
    """维护 draft/active/deprecated/revoked Skill 版本。"""

    def __init__(
        self,
        *,
        allowed_source_prefixes: list[str],
        activation_threshold: float,
        clock: Clock | None = None,
    ) -> None:
        self._allowed_sources = allowed_source_prefixes
        self._activation_threshold = activation_threshold
        self._clock = clock or SystemClock()
        self._skills: dict[str, SkillManifest] = {}

    def register(
        self,
        *,
        name: str,
        version: str,
        content: str,
        source_uri: str,
        allowed_tools: list[str],
        required_permissions: list[str],
    ) -> SkillManifest:
        """从白名单来源注册 draft Skill。"""
        if not any(source_uri.startswith(prefix) for prefix in self._allowed_sources):
            raise ValidationError(f"Skill source is not allowlisted: {source_uri}")
        if any(item.name == name and item.version == version for item in self._skills.values()):
            raise ValidationError(f"Skill version already registered: {name}@{version}")
        now = self._clock.now()
        skill = SkillManifest(
            id=f"skill_{uuid.uuid4().hex[:12]}",
            name=name,
            version=version,
            content=content,
            checksum=self._checksum(content),
            source_uri=source_uri,
            allowed_tools=allowed_tools,
            required_permissions=required_permissions,
            created_at=now,
            updated_at=now,
        )
        self._skills[skill.id] = skill
        return skill.model_copy(deep=True)

    def activate(self, skill_id: str, *, eval_score: float) -> SkillManifest:
        """通过评测门槛后激活 Skill，并废弃同名旧 active 版本。"""
        skill = self._get(skill_id)
        if eval_score < self._activation_threshold:
            raise ValidationError(
                f"Skill eval gate failed: {eval_score} < {self._activation_threshold}"
            )
        self.verify_content(skill.id, skill.content)
        for candidate in self._skills.values():
            if candidate.name == skill.name and candidate.status == SkillStatus.ACTIVE:
                candidate.status = SkillStatus.DEPRECATED
                candidate.updated_at = self._clock.now()
        skill.status = SkillStatus.ACTIVE
        skill.eval_score = eval_score
        skill.updated_at = self._clock.now()
        return skill.model_copy(deep=True)

    def verify_content(self, skill_id: str, content: str) -> None:
        """验证运行时 Skill 内容未被篡改。"""
        skill = self._get(skill_id)
        if self._checksum(content) != skill.checksum:
            raise ValidationError(f"Skill checksum mismatch: {skill_id}")

    def revoke(self, skill_id: str, *, reason: str) -> SkillManifest:
        """立即撤销 Skill。"""
        skill = self._get(skill_id)
        skill.status = SkillStatus.REVOKED
        skill.revoke_reason = reason
        skill.updated_at = self._clock.now()
        return skill.model_copy(deep=True)

    def resolve(self, name: str) -> SkillManifest | None:
        """解析同名 active Skill。"""
        active = [
            item for item in self._skills.values()
            if item.name == name and item.status == SkillStatus.ACTIVE
        ]
        if not active:
            return None
        return max(active, key=lambda item: item.updated_at).model_copy(deep=True)

    def _get(self, skill_id: str) -> SkillManifest:
        skill = self._skills.get(skill_id)
        if skill is None:
            raise NotFoundError(f"Skill not found: {skill_id}")
        return skill

    @staticmethod
    def _checksum(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
