# devmate 运行时端口契约

`app/devmate/contracts/` 是 Runtime 候选的依赖边界，只定义领域中性的
端口与 typed command，不引用任何 HR/RAG 领域接口。

- `state.py`：Case 状态机 `created -> running -> waiting_approval ->
  completed -> failed`；非法转换抛 `IllegalTransitionError`。
- `ports.py`：`EventStreamPort` / `CaseStorePort` / `ClockPort` Protocol，
  供 Runtime 候选接入外部存储与时间。
- `commands.py`：typed 入口 `RuntimeEvent.execute(DM02Input) -> DM02Result`，
  返回状态事件与审计信息。

接口签名、状态机与数据表语义以 `.agent-governance/module-contracts.json`
为机器真源。
