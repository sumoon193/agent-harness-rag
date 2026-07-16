"""Case projection 与事件重放。"""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.schemas.enums import CaseStatus
from app.schemas.runtime import ExecutionManifest, HRCase, RunEventEnvelope


class CaseProjector:
    """将 append-only Case 事件投影为查询模型。"""

    def apply(self, current: HRCase | None, event: RunEventEnvelope) -> HRCase:
        """幂等应用单个事件。"""
        if current is not None and event.sequence <= current.version:
            return current

        if event.event_type == "case.created":
            if current is not None:
                raise ValidationError(f"Case already created: {event.aggregate_id}")
            return HRCase(
                id=event.aggregate_id,
                title=str(event.payload["title"]),
                tenant_id=str(event.payload["tenant_id"]),
                subject_user_id=str(event.payload["subject_user_id"]),
                status=CaseStatus.OPEN,
                version=event.sequence,
                execution_manifest=ExecutionManifest.model_validate(
                    event.payload["execution_manifest"]
                ),
                policy_versions=dict(event.payload.get("policy_versions", {})),
                working_memory={"messages": []},
                created_at=event.created_at,
                updated_at=event.created_at,
            )

        if current is None:
            raise ValidationError(
                f"Cannot project {event.event_type} before case.created: {event.aggregate_id}"
            )
        if event.sequence != current.version + 1:
            raise ValidationError(
                f"Projection sequence gap: expected {current.version + 1}, got {event.sequence}"
            )

        if event.event_type == "case.message_added":
            working_memory = dict(current.working_memory)
            messages = list(working_memory.get("messages", []))
            messages.append(
                {
                    "event_id": event.id,
                    "actor_id": event.actor_id,
                    "content": str(event.payload["message"]),
                    "created_at": event.created_at.isoformat(),
                }
            )
            working_memory["messages"] = messages
            return current.model_copy(
                update={
                    "version": event.sequence,
                    "working_memory": working_memory,
                    "updated_at": event.created_at,
                },
                deep=True,
            )

        if event.event_type == "run.started":
            working_memory = dict(current.working_memory)
            working_memory["phase"] = "researching_policy"
            updated = self._updated(current, event, working_memory=working_memory)
            return updated.model_copy(
                update={"active_run_id": str(event.payload["run_id"])},
                deep=True,
            )

        if event.event_type == "skill.loaded":
            working_memory = dict(current.working_memory)
            working_memory["skill"] = dict(event.payload)
            return self._updated(current, event, working_memory=working_memory)

        if event.event_type == "a2a.task.completed":
            working_memory = dict(current.working_memory)
            artifacts = list(working_memory.get("artifacts", []))
            artifacts.append(dict(event.payload))
            working_memory["artifacts"] = artifacts
            return self._updated(current, event, working_memory=working_memory)

        if event.event_type == "evidence.retrieved":
            working_memory = dict(current.working_memory)
            working_memory["evidence"] = list(event.payload.get("citations", []))
            working_memory["phase"] = "planning"
            return self._updated(current, event, working_memory=working_memory)

        if event.event_type in {"plan.created", "plan.revised"}:
            working_memory = dict(current.working_memory)
            working_memory["plan"] = dict(event.payload)
            working_memory["phase"] = "preparing_action"
            return self._updated(current, event, working_memory=working_memory)

        if event.event_type == "policy.stale_detected":
            working_memory = dict(current.working_memory)
            working_memory["phase"] = "refreshing_policy"
            working_memory["stale_policy"] = dict(event.payload)
            return self._updated(current, event, working_memory=working_memory)

        if event.event_type == "policy.refreshed":
            working_memory = dict(current.working_memory)
            policy_versions = dict(current.policy_versions)
            policy_versions["hr_policy"] = str(event.payload["policy_version"])
            working_memory["phase"] = "replanning"
            updated = self._updated(current, event, working_memory=working_memory)
            return updated.model_copy(update={"policy_versions": policy_versions}, deep=True)

        if event.event_type == "tool.call_prepared":
            working_memory = dict(current.working_memory)
            tool_calls = list(working_memory.get("tool_calls", []))
            tool_calls.append(dict(event.payload))
            working_memory["tool_calls"] = tool_calls
            return self._updated(current, event, working_memory=working_memory)

        if event.event_type == "approval.requested":
            working_memory = dict(current.working_memory)
            approvals = list(working_memory.get("approvals", []))
            approvals.append({**event.payload, "status": "pending"})
            working_memory["approvals"] = approvals
            working_memory["phase"] = "waiting_approval"
            return self._updated(
                current,
                event,
                status=CaseStatus.WAITING_APPROVAL,
                working_memory=working_memory,
            )

        if event.event_type == "approval.decided":
            working_memory = dict(current.working_memory)
            approval_id = event.payload.get("approval_id")
            approvals = [
                {
                    **approval,
                    **(
                        {
                            "status": event.payload.get("status"),
                            "decision": event.payload.get("decision"),
                            "decided_by": event.payload.get("decided_by"),
                            "effective_approval_id": event.payload.get(
                                "effective_approval_id", approval_id
                            ),
                        }
                        if approval.get("approval_id") == approval_id
                        else {}
                    ),
                }
                for approval in working_memory.get("approvals", [])
            ]
            working_memory["approvals"] = approvals
            decision = str(event.payload.get("decision", ""))
            working_memory["phase"] = (
                "executing_action" if decision in {"approve", "edit"} else "open"
            )
            return self._updated(
                current,
                event,
                status=(CaseStatus.OPEN if decision == "reject" else current.status),
                working_memory=working_memory,
            )

        if event.event_type == "tool.executed":
            working_memory = dict(current.working_memory)
            results = list(working_memory.get("tool_results", []))
            results.append(dict(event.payload))
            working_memory["tool_results"] = results
            working_memory["phase"] = "scheduling_follow_up"
            return self._updated(
                current,
                event,
                status=CaseStatus.OPEN,
                working_memory=working_memory,
            )

        if event.event_type == "memory.stored":
            working_memory = dict(current.working_memory)
            memories = list(working_memory.get("memories", []))
            memories.append(dict(event.payload))
            working_memory["memories"] = memories
            return self._updated(current, event, working_memory=working_memory)

        if event.event_type == "context.compacted":
            working_memory = dict(current.working_memory)
            working_memory["context_snapshot"] = dict(event.payload)
            return self._updated(current, event, working_memory=working_memory)

        if event.event_type == "timer.scheduled":
            working_memory = dict(current.working_memory)
            timers = list(working_memory.get("timers", []))
            timers.append(
                {
                    "timer_id": event.payload["timer_id"],
                    "timer_type": event.payload["timer_type"],
                    "due_at": event.payload["due_at"],
                    "status": "scheduled",
                }
            )
            working_memory["timers"] = timers
            return current.model_copy(
                update={
                    "status": CaseStatus.WAITING_TIMER,
                    "version": event.sequence,
                    "working_memory": working_memory,
                    "updated_at": event.created_at,
                },
                deep=True,
            )

        if event.event_type == "timer.fired":
            working_memory = dict(current.working_memory)
            timers = [
                {
                    **timer,
                    "status": (
                        "fired"
                        if timer.get("timer_id") == event.payload["timer_id"]
                        else timer.get("status")
                    ),
                }
                for timer in working_memory.get("timers", [])
            ]
            working_memory["timers"] = timers
            return current.model_copy(
                update={
                    "status": CaseStatus.OPEN,
                    "version": event.sequence,
                    "working_memory": working_memory,
                    "updated_at": event.created_at,
                },
                deep=True,
            )

        return current.model_copy(
            update={"version": event.sequence, "updated_at": event.created_at},
            deep=True,
        )

    @staticmethod
    def _updated(
        current: HRCase,
        event: RunEventEnvelope,
        *,
        working_memory: dict[str, object],
        status: CaseStatus | None = None,
    ) -> HRCase:
        """构造包含统一版本字段的 projection 更新。"""
        updates: dict[str, object] = {
            "version": event.sequence,
            "working_memory": working_memory,
            "updated_at": event.created_at,
        }
        if status is not None:
            updates["status"] = status
        return current.model_copy(update=updates, deep=True)

    def rebuild(self, events: list[RunEventEnvelope]) -> HRCase:
        """从完整事件流重建 Case projection。"""
        current: HRCase | None = None
        for event in events:
            current = self.apply(current, event)
        if current is None:
            raise ValidationError("Cannot rebuild case from an empty event stream")
        return current
