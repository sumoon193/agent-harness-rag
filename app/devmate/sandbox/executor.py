"""资源受限的确定性 Sandbox 执行器。

合同：``CheckpointPort.execute(input: DM09Input) -> DM09Result``。
只执行 declared 命令；未声明命令与资源超限命令被拒绝；不发起任何
外部网络或进程调用，结果确定可复核。
"""

from __future__ import annotations

from typing import Protocol

from app.devmate.sandbox.types import DM09Input, DM09Result, SandboxCommand, SandboxRun

UNDECLARED_EXIT = 127
RESOURCE_EXIT = 137


class CheckpointPort(Protocol):
    def execute(self, input_: DM09Input) -> DM09Result: ...


class IsolatedSandbox:
    def execute(self, input_: DM09Input) -> DM09Result:
        runs: list[SandboxRun] = []
        exceeded = False
        for command in input_.commands:
            run = self._run(command, input_.cpu_limit, input_.memory_limit)
            if run.exit_code == RESOURCE_EXIT:
                exceeded = True
            runs.append(run)
        allowed = all(run.exit_code == 0 for run in runs)
        return DM09Result(
            case_id=input_.case_id,
            runs=tuple(runs),
            allowed=allowed,
            resource_exceeded=exceeded,
            audit={
                "sandbox": "isolated-in-memory",
                "commands": str(len(runs)),
                "allowed": str(allowed),
            },
        )

    def _run(
        self,
        command: SandboxCommand,
        cpu_limit: float,
        memory_limit: int,
    ) -> SandboxRun:
        if not command.declared:
            return SandboxRun(command.command, UNDECLARED_EXIT, "", "undeclared command")
        if command.cost_cpu > cpu_limit or command.cost_memory > memory_limit:
            return SandboxRun(command.command, RESOURCE_EXIT, "", "resource limit exceeded")
        args = " ".join(command.args)
        stdout = f"{command.command} {args}".strip() + " completed"
        return SandboxRun(command.command, 0, stdout, "")
