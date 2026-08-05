"""devmate 租约与恢复领域类型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Lease:
    case_id: str
    owner: str
    acquired_at: int
    expires_at: int
    version: int


@dataclass(frozen=True)
class DM12Input:
    case_id: str
    owner: str
    action: str
    side_effect_id: str = ""
    now: int = 0


@dataclass(frozen=True)
class DM12Result:
    case_id: str
    lease: Lease | None
    owner: str
    side_effect_id: str | None
    duplicate: bool
    audit: dict[str, str] = field(default_factory=dict)
