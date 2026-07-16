"""执行和回答前的 evidence version 新鲜度校验。"""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.schemas.chunk import Citation


class EvidenceFreshnessValidator:
    """拒绝已被新制度版本替代的引用。"""

    def validate(
        self,
        citations: list[Citation],
        *,
        active_versions: dict[str, str],
    ) -> None:
        """校验每条 citation 仍指向文档 active version。"""
        stale = [
            citation
            for citation in citations
            if citation.document_id in active_versions
            and active_versions[citation.document_id] != citation.document_version
        ]
        if stale:
            refs = ", ".join(
                f"{item.document_id}:{item.document_version}" for item in stale
            )
            raise ValidationError(f"stale evidence requires retrieval refresh: {refs}")
