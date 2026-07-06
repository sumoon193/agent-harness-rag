# MCP Adapter 落地证据

## 落地范围

- 新增 `app/services/mcp/fake_server.py`：本地 fake MCP server。
- 新增 `app/services/mcp/adapter.py`：`McpToolDiscovery`、`McpToolAdapter`、`McpApprovalBridge`。
- 第一阶段工具：
  - `list_hr_policy_documents`：只读。
  - `create_mock_hr_ticket`：写操作，必须审批。
  - `summarize_agent_run_artifacts`：只读。

## 已验证行为

- fake MCP server 可返回工具列表和 schema。
- schema 不匹配时拒绝调用，server 不收到请求。
- 写工具未审批前只创建 approval preview，不调用 server。
- 审批通过后由 bridge 恢复执行，server 只收到一次写调用。
- server 异常会归一化为 failed tool call。

## 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest tests\service\test_mcp_adapter.py -q -p no:cacheprovider
```

当前结果：`5 passed`。
