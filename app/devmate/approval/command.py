"""审批 typed command：决定绑定 patch、evidence、命令、主体与过期时间。

合同：``CaseCommand.execute(input: DM10Input) -> DM10Result``。
过期审批稳定拒绝；同一 approval_id 的重复决定幂等返回。
"""

from __future__ import annotations

from app.devmate.approval.store import ApprovalNotFoundError, ApprovalStore
from app.devmate.approval.types import (
    ApprovalRequest,
    DM10Input,
    DM10Result,
)

VALID_DECISIONS = ("approve", "reject")
STATUS_BY_DECISION = {"approve": "approved", "reject": "rejected"}


class InvalidDecisionError(ValueError):
    def __init__(self, decision: str) -> None:
        super().__init__(f"invalid decision: {decision}")
        self.decision = decision


class ApprovalExpiredError(ValueError):
    def __init__(self, approval_id: str) -> None:
        super().__init__(f"approval expired: {approval_id}")
        self.approval_id = approval_id


class CaseCommand:
    def __init__(self, store: ApprovalStore) -> None:
        self._store = store
        self._results: dict[str, DM10Result] = {}

    def execute(self, input_: DM10Input) -> DM10Result:
        if input_.approval_id in self._results:
            return self._results[input_.approval_id]
        request = self._store.get(input_.approval_id)
        if request is None:
            raise ApprovalNotFoundError(input_.approval_id)
        if input_.decision not in VALID_DECISIONS:
            raise InvalidDecisionError(input_.decision)
        if input_.decided_at > request.expires_at:
            raise ApprovalExpiredError(input_.approval_id)

        updated = ApprovalRequest(
            approval_id=request.approval_id,
            case_id=request.case_id,
            patch_id=request.patch_id,
            evidence_ids=request.evidence_ids,
            command=request.command,
            requested_by=request.requested_by,
            requested_at=request.requested_at,
            expires_at=request.expires_at,
            status=STATUS_BY_DECISION[input_.decision],
            decided_by=input_.decided_by,
        )
        self._store.decide(updated)
        result = DM10Result(
            approval_id=request.approval_id,
            case_id=request.case_id,
            patch_id=request.patch_id,
            evidence_ids=request.evidence_ids,
            command=request.command,
            decided_by=input_.decided_by,
            status=STATUS_BY_DECISION[input_.decision],
            expires_at=request.expires_at,
            audit={"requested_by": request.requested_by},
        )
        self._results[input_.approval_id] = result
        return result
