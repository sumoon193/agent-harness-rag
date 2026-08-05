"""GitHub 副作用 typed 入口。

合同：``RuntimeEvent.execute(input: DM11Input) -> DM11Result``。
重复发布不重复创建分支/PR；调用超时进入 UNKNOWN 并可对账。
"""

from __future__ import annotations

from app.devmate.git.ledger import SideEffectLedger
from app.devmate.git.types import DM11Input, DM11Result, SideEffect

CREATED_AT = "2026-08-04T00:00:00Z"


class RuntimeEvent:
    def __init__(self, ledger: SideEffectLedger | None = None) -> None:
        self.ledger = ledger or SideEffectLedger()

    def execute(self, input_: DM11Input) -> DM11Result:
        existing = self.ledger.effects_for(input_.release_id)
        if existing:
            return DM11Result(
                release_id=input_.release_id,
                effects=tuple(existing),
                duplicated=True,
                reconciliation_required=self.ledger.needs_reconciliation(input_.release_id),
                audit={"duplicate": "true"},
            )
        status = "unknown" if input_.timeout else "created"
        effects = (
            SideEffect(
                effect_id=f"branch-{input_.release_id}",
                release_id=input_.release_id,
                kind="branch",
                target=input_.branch,
                status=status,
                created_at=CREATED_AT,
            ),
            SideEffect(
                effect_id=f"pr-{input_.release_id}",
                release_id=input_.release_id,
                kind="pull_request",
                target=input_.pr_title,
                status=status,
                created_at=CREATED_AT,
            ),
        )
        for effect in effects:
            self.ledger.add(effect)
        return DM11Result(
            release_id=input_.release_id,
            effects=effects,
            duplicated=False,
            reconciliation_required=input_.timeout,
            audit={"timeout": str(input_.timeout)},
        )

    def reconcile(self, release_id: str) -> DM11Result:
        effects = self.ledger.reconcile(release_id)
        return DM11Result(
            release_id=release_id,
            effects=tuple(effects),
            duplicated=False,
            reconciliation_required=False,
            audit={"reconciled": "true"},
        )
