# MCP Server / Adapter 设计

## 目标

实现 MCP 风格工具适配层，统一外部工具的发现、schema、调用、审批和审计。第一阶段优先本地 fake adapter，不把远程 MCP 生态作为运行前提。

## 组件

- `McpToolDiscovery`：发现工具列表和 schema。
- `McpToolAdapter`：把 Harness tool call 转成 MCP 风格调用。
- `McpResultNormalizer`：统一结果、错误和元数据。
- `McpApprovalBridge`：把写工具接入现有 approval gate。

## 边界

- MCP adapter 不能直接绕过 Tool Registry。
- 写工具仍默认需要审批。
- 工具 schema 必须在调用前校验。
- 失败结果必须进入 AgentRun artifact 和 trace。
- 单元测试使用 fake MCP server。

## 第一阶段工具

- `list_hr_policy_documents`：只读。
- `create_mock_hr_ticket`：写操作，必须审批。
- `summarize_agent_run_artifacts`：只读，用于复盘。

## 验收样例

- fake MCP server 返回工具列表。
- schema 不匹配时拒绝调用。
- 写工具未审批时不调用 server。
- server 失败时记录 normalized error。
