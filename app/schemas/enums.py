"""
核心枚举定义。

所有枚举继承 StrEnum，便于 JSON 序列化。
"""
from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
    """
    Agent Run 状态机。

    状态流转：
    CREATED -> RUNNING -> RETRIEVING_EVIDENCE -> PLANNING -> AWAITING_APPROVAL -> RESUMED -> COMPLETED
                                                |-> FAILED
                                                |-> CANCELLED
    """
    CREATED = "created"
    RUNNING = "running"
    RETRIEVING_EVIDENCE = "retrieving_evidence"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    RESUMED = "resumed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CaseStatus(StrEnum):
    """跨轮次、跨天业务 Case 状态。"""

    OPEN = "open"
    WAITING_APPROVAL = "waiting_approval"
    WAITING_TIMER = "waiting_timer"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentStatus(StrEnum):
    """
    文档入库状态。

    状态流转：
    QUEUED -> PARSING -> CHUNKING -> EMBEDDING -> INDEXING -> READY
                                                      |-> FAILED
    """
    QUEUED = "queued"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class ToolRiskLevel(StrEnum):
    """
    工具风险等级。

    - READ: 只读，自动执行
    - WRITE: 写入型，必须审批
    - ADMIN: 管理级，必须审批
    """
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class ToolCallStatus(StrEnum):
    """
    工具调用状态。

    用于约束工具调用生命周期，避免自由字符串造成状态漂移。
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalStatus(StrEnum):
    """
    审批请求状态。

    pending 表示等待人工处理，approved/rejected/edited 表示审批结果。
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class ApprovalDecisionType(StrEnum):
    """
    审批决策类型。

    用户只能选择 approve、edit 或 reject。
    """
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"


class SideEffectStatus(StrEnum):
    """副作用账本状态。"""

    RESERVED = "reserved"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class TimerStatus(StrEnum):
    """持久化定时器状态。"""

    SCHEDULED = "scheduled"
    CLAIMED = "claimed"
    FIRED = "fired"
    CANCELLED = "cancelled"


class MemoryStatus(StrEnum):
    """长期记忆治理状态。"""

    ACTIVE = "active"
    QUARANTINED = "quarantined"
    DELETED = "deleted"
    EXPIRED = "expired"


class SkillStatus(StrEnum):
    """程序性 Skill 生命周期。"""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


class Visibility(StrEnum):
    """
    文档可见性级别。

    用于 ACL 权限控制。
    """
    PUBLIC = "public"
    DEPARTMENT = "department"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"
