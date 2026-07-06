# Loop Engineering 设计

## 目标

把 Agent 的 plan、act、observe、reflect、repair 固化为 Harness 事件，而不是只在 prompt 里要求模型“思考”。

## 循环阶段

- `PLAN`：生成任务计划、工具候选和风险说明。
- `ACT`：执行只读工具或提交写工具审批。
- `OBSERVE`：记录 evidence、tool result、error 和 trace。
- `REFLECT`：判断是否证据不足、工具失败、权限不足、引用缺失。
- `REPAIR`：生成修复动作，例如重检索、缩小范围、请求人工审批或拒答。

## 边界

- Reflection 只能产生下一步建议，不能绕过审批直接执行写操作。
- Repair 必须保留前一次失败原因。
- 每个循环事件都要能关联 AgentRun 和 trace。
- 单元测试使用 fake LLM 和 fake tools。

## 验收样例

- evidence 不足时进入 `REPAIR` 并追加检索计划。
- 写工具未审批时停在 approval pending。
- tool adapter 失败时进入 `REFLECT` 并输出失败归因。
- citation 缺失时拒答或修复，不输出无证据答案。
