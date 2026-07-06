# ACL 与安全开发规范

本模块负责企业权限隔离和 LLM / Agent 安全防护。

## 模块职责

- UserContext 与 PermissionFilter。
- 文档级 ACL metadata。
- 检索前过滤。
- 生成前 citation 二次校验。
- Prompt Injection 防护。
- PII 脱敏。
- 工具权限校验。
- 速率限制。

## ACL 元数据

文档和 chunk 必须包含：

- `tenant_id`
- `department_id`
- `allowed_roles`
- `visibility`
- `classification`
- `owner_user_id`

`visibility`：

- `public`
- `department`
- `private`
- `confidential`

## 三层权限控制

1. 入库时写入 ACL metadata。
2. 检索前生成 Milvus / Elasticsearch filter。
3. 答案生成前校验 citations 和 tool permission。

## 工具权限

每个 tool 定义：

- `permission_scope`
- `risk_level`
- `requires_approval`

执行前检查：

- 用户角色是否允许。
- 工具是否需要审批。
- 审批是否已通过。
- 参数是否越权。

## OWASP 风险覆盖

- Prompt Injection。
- Sensitive Information Disclosure。
- System Prompt Leakage。
- Vector and Embedding Weaknesses。
- Excessive Agency。
- Unbounded Consumption。

## 日志安全

- 不记录 API key。
- 不记录完整 system prompt。
- PII 默认脱敏。
- 无权限 evidence 不写入可见 trace payload。

## 不做什么

- V1 不做完整企业 IAM。
- 不把权限只放在前端。
- 不依赖 LLM 自己判断权限。

## 测试要求

- `test_acl_filter_excludes_other_department_chunks`
- `test_private_document_visible_only_to_owner`
- `test_confidential_document_requires_role`
- `test_unauthorized_tool_call_is_rejected`
- `test_prompt_injection_pattern_is_flagged`
- `test_pii_is_redacted_in_logs`

## 验收标准

- 无权限内容不会进入 retrieval hits、rerank input、answer prompt。
- 写入型工具同时满足权限和审批才执行。
- 安全事件可审计。

