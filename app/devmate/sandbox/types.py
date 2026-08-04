"""devmate Sandbox 隔离执行领域类型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SandboxCommand:
    command: str
    args: tuple[str, ...] = ()
    declared: bool = True
    cost_cpu: float = 0.1
    cost_memory: int = 8


@dataclass(frozen=True)
class SandboxRun:
    command: str
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class DM09Input:
    case_id: str
    commands: tuple[SandboxCommand, ...]
    cpu_limit: float = 1.0
    memory_limit: int = 64


@dataclass(frozen=True)
class DM09Result:
    case_id: str
    runs: tuple[SandboxRun, ...]
    allowed: bool
    resource_exceeded: bool
    audit: dict[str, str] = field(default_factory=dict)
