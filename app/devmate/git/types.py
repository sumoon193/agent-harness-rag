"""devmate GitHub 副作用领域类型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SideEffect:
    effect_id: str
    release_id: str
    kind: str
    target: str
    status: str
    created_at: str


@dataclass(frozen=True)
class DM11Input:
    release_id: str
    branch: str
    pr_title: str
    timeout: bool = False


@dataclass(frozen=True)
class DM11Result:
    release_id: str
    effects: tuple[SideEffect, ...]
    duplicated: bool
    reconciliation_required: bool
    audit: dict[str, str] = field(default_factory=dict)
