-- devmate_case：主键、版本/幂等键、创建更新时间与审计来源。
-- 向前/向后兼容：IF NOT EXISTS 幂等创建，不删除或改动既有列。
CREATE TABLE IF NOT EXISTS devmate_case (
    case_id       TEXT PRIMARY KEY,
    version       INTEGER NOT NULL,
    checkpoint_id TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'created',
    payload_json  TEXT NOT NULL DEFAULT '{}',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    audit_source  TEXT NOT NULL
);
