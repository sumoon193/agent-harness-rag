"""devmate 审批存储：请求登记与决定落库。"""

from __future__ import annotations

from app.devmate.approval.types import ApprovalRequest


class ApprovalNotFoundError(KeyError):
    def __init__(self, approval_id: str) -> None:
        super().__init__(f"approval not found: {approval_id}")
        self.approval_id = approval_id


class DuplicateApprovalError(ValueError):
    def __init__(self, approval_id: str) -> None:
        super().__init__(f"approval already exists: {approval_id}")
        self.approval_id = approval_id


class ApprovalStore:
    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRequest] = {}

    def request(self, request: ApprovalRequest) -> None:
        if request.approval_id in self._approvals:
            raise DuplicateApprovalError(request.approval_id)
        self._approvals[request.approval_id] = request

    def get(self, approval_id: str) -> ApprovalRequest | None:
        return self._approvals.get(approval_id)

    def decide(self, request: ApprovalRequest) -> None:
        self._approvals[request.approval_id] = request
