# V2 扩展：GraphRAG 与 MCP 开发规范

本模块是 V2 增强，不阻塞 V1。目标是在核心 Agent Harness + RAG 跑通后，增强多跳关系推理和标准化工具接口。

## GraphRAG / LightRAG 职责

- 从企业文档中抽取实体。
- 构建实体关系图。
- 支持 multi-hop intent。
- 图检索结果补充原文 evidence。

## 实体类型

- `department`
- `role`
- `policy`
- `process`
- `system`
- `approver`
- `task`
- `document`

## 关系类型

- `belongs_to`
- `requires`
- `approved_by`
- `uses_system`
- `defined_in`
- `precedes`
- `depends_on`

## Graph 检索流程

```text
question
  -> intent = multi_hop
  -> entity linking
  -> graph path search
  -> related document lookup
  -> hybrid retrieval for source evidence
  -> answer with citations
```

GraphRAG 结果不能单独作为最终答案，必须回查原文 evidence。

## MCP 职责

将企业知识能力暴露为 MCP Server：

- `resources`: 文档、章节、引用片段。
- `tools`: 检索、生成清单、创建模拟工单。
- `prompts`: 问答、流程规划、审批说明模板。

## MCP 设计规则

- 使用 JSON-RPC 协议模型。
- 遵循 client-host-server 架构。
- 支持 capability negotiation。
- 为 remote HTTP transport 预留 authorization。
- tool output 使用结构化结果。
- destructive / write tools 必须声明风险和审批要求。

## 不做什么

- V1 不实现完整 MCP Server。
- MCP 不绕过 Agent Harness 权限和审批。
- GraphRAG 不替代 hybrid retrieval。

## 测试要求

- `test_entity_extractor_finds_policy_process_approver`
- `test_graph_retriever_returns_relation_path`
- `test_graph_answer_requires_source_evidence`
- `test_mcp_tool_schema_marks_write_tool_as_destructive`
- `test_mcp_tool_call_goes_through_harness_approval`

## 验收标准

- 多跳 HR 问题能返回关系链和原文 citations。
- MCP tool 与内部 Tool Registry 字段一致。
- MCP 不能绕过 ACL、approval 和 audit。

