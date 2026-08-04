# DevMate Enterprise Agent Runtime 完整实施计划

> 本文是开发执行合同，不是学习材料或完成证明。每一模块必须由独立任务分支按依赖顺序实施，先观察失败测试，再做最小实现。

## 全局精确路径与边界

- 生产代码根：`app/devmate`。
- 任务只能修改本模块 `source_paths/test_paths` 与任务包白名单；Runtime Kernel、秘密和其他模块默认只读或禁止。
- 接口签名、数据表、API、状态和错误语义以 `.agent-governance/module-contracts.json` 为机器真源。
- 每次激活任务时，主集成模型把任务 `base_sha` 重绑定为当前集成提交，再由实现模型创建精确分支。

## 公共接口签名、数据表与 API

### 接口签名
- `RuntimePort.handle(command: RuntimeCommand) -> RuntimeResult`
- `EvidencePort.collect(case_id: str) -> EvidenceBundle`

### 数据表
- `devmate_case`：必须有主键、版本/幂等键、创建更新时间与审计来源。
- `devmate_event`：必须有主键、版本/幂等键、创建更新时间与审计来源。
- `devmate_outbox`：必须有主键、版本/幂等键、创建更新时间与审计来源。
- `devmate_projection`：必须有主键、版本/幂等键、创建更新时间与审计来源。
- `devmate_side_effect`：必须有主键、版本/幂等键、创建更新时间与审计来源。

### API
- `POST /devmate/cases`：使用 typed request/response、稳定错误码、request/correlation ID 与权限校验。
- `POST /devmate/cases/{case_id}/commands`：使用 typed request/response、稳定错误码、request/correlation ID 与权限校验。
- `GET /devmate/cases/{case_id}/timeline`：使用 typed request/response、稳定错误码、request/correlation ID 与权限校验。

## 模块逐项执行

### DM-01 来源、许可证与 origin audit

- 依赖：`无`。
- 精确路径：`docs/audit/**`, `scripts/audit_*.py`, `tests/audit/**`。
- 接口签名：`CaseCommand.execute(input: DM01Input) -> DM01Result`。
- 数据表：`devmate_case`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/audit/test_dm_01.py`，失败原因只能是目标行为未实现。
- 可观察结果：缺少来源或许可证的文件保持 review/blocked。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-02 领域隔离与端口合同

- 依赖：`DM-01`。
- 精确路径：`app/devmate/contracts/**`, `docs/devmate/contracts/**`, `tests/devmate/contracts/**`。
- 接口签名：`RuntimeEvent.execute(input: DM02Input) -> DM02Result`。
- 数据表：`devmate_event`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/contracts/test_dm_02.py`，失败原因只能是目标行为未实现。
- 可观察结果：Runtime 候选不直接依赖 HR/RAG 领域接口。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-03 Event Store、Projection 与 Outbox

- 依赖：`DM-02`。
- 精确路径：`app/devmate/runtime/**`, `migrations/devmate/**`, `tests/devmate/runtime/**`。
- 接口签名：`CheckpointPort.execute(input: DM03Input) -> DM03Result`。
- 数据表：`devmate_case`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/runtime/test_dm_03.py`，失败原因只能是目标行为未实现。
- 可观察结果：事件和 Outbox 同事务且 Projection 可重建。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-04 Case 状态机与 HTTP API

- 依赖：`DM-03`。
- 精确路径：`app/devmate/cases/**`, `app/api/devmate/**`, `tests/devmate/cases/**`, `tests/api/devmate/**`。
- 接口签名：`CaseCommand.execute(input: DM04Input) -> DM04Result`。
- 数据表：`devmate_event`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/cases/test_dm_04.py`，失败原因只能是目标行为未实现。
- 可观察结果：API 只能通过 command 推进合法 Case 状态。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-05 Webhook 与 evidence 摄取

- 依赖：`DM-04`。
- 精确路径：`app/devmate/ingestion/**`, `tests/devmate/ingestion/**`。
- 接口签名：`RuntimeEvent.execute(input: DM05Input) -> DM05Result`。
- 数据表：`devmate_case`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/ingestion/test_dm_05.py`，失败原因只能是目标行为未实现。
- 可观察结果：重复 webhook 幂等并固定 commit/CI evidence。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-06 确定性诊断 baseline

- 依赖：`DM-05`。
- 精确路径：`app/devmate/diagnostics/**`, `tests/devmate/diagnostics/**`。
- 接口签名：`CheckpointPort.execute(input: DM06Input) -> DM06Result`。
- 数据表：`devmate_event`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/diagnostics/test_dm_06.py`，失败原因只能是目标行为未实现。
- 可观察结果：固定日志和测试报告产生可重复 findings。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-07 模型 Fake/Recorded typed diagnosis

- 依赖：`DM-06`。
- 精确路径：`app/devmate/models/**`, `app/prompts/devmate/**`, `tests/devmate/models/**`。
- 接口签名：`CaseCommand.execute(input: DM07Input) -> DM07Result`。
- 数据表：`devmate_case`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/models/test_dm_07.py`，失败原因只能是目标行为未实现。
- 可观察结果：模型输出经过 typed parser 且可降级到 Fake/Recorded。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-08 修复计划与 patch 候选

- 依赖：`DM-07`。
- 精确路径：`app/devmate/repair/**`, `tests/devmate/repair/**`。
- 接口签名：`RuntimeEvent.execute(input: DM08Input) -> DM08Result`。
- 数据表：`devmate_event`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/repair/test_dm_08.py`，失败原因只能是目标行为未实现。
- 可观察结果：RepairPlan 只生成不可变 patch artifact。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-09 Sandbox 隔离执行

- 依赖：`DM-08`。
- 精确路径：`app/devmate/sandbox/**`, `tests/devmate/sandbox/**`。
- 接口签名：`CheckpointPort.execute(input: DM09Input) -> DM09Result`。
- 数据表：`devmate_case`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/sandbox/test_dm_09.py`，失败原因只能是目标行为未实现。
- 可观察结果：候选 patch 仅在资源受限 Sandbox 中执行声明命令。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-10 审批 capability 与 revision

- 依赖：`DM-09`。
- 精确路径：`app/devmate/approval/**`, `tests/devmate/approval/**`。
- 接口签名：`CaseCommand.execute(input: DM10Input) -> DM10Result`。
- 数据表：`devmate_event`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/approval/test_dm_10.py`，失败原因只能是目标行为未实现。
- 可观察结果：审批绑定 patch、evidence、命令、主体和过期时间。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-11 GitHub 副作用与 UNKNOWN 对账

- 依赖：`DM-10`。
- 精确路径：`app/devmate/git/**`, `tests/devmate/git/**`。
- 接口签名：`RuntimeEvent.execute(input: DM11Input) -> DM11Result`。
- 数据表：`devmate_case`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/git/test_dm_11.py`，失败原因只能是目标行为未实现。
- 可观察结果：重复发布不重复创建分支/PR且超时进入对账。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-12 并发、租约与崩溃恢复

- 依赖：`DM-11`。
- 精确路径：`app/devmate/recovery/**`, `tests/devmate/recovery/**`。
- 接口签名：`CheckpointPort.execute(input: DM12Input) -> DM12Result`。
- 数据表：`devmate_event`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/recovery/test_dm_12.py`，失败原因只能是目标行为未实现。
- 可观察结果：并发 resume 和过期 owner 不产生覆盖写或重复副作用。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-13 冻结评测、OTel、性能与成本

- 依赖：`DM-12`。
- 精确路径：`app/devmate/eval/**`, `app/devmate/observability/**`, `tests/devmate/eval/**`。
- 接口签名：`CaseCommand.execute(input: DM13Input) -> DM13Result`。
- 数据表：`devmate_case`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/eval/test_dm_13.py`，失败原因只能是目标行为未实现。
- 可观察结果：诊断、Sandbox、审批和副作用具有可复核指标。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### DM-14 发布、回滚与真实性审计

- 依赖：`DM-13`。
- 精确路径：`scripts/devmate/**`, `docs/devmate/release/**`, `tests/devmate/release/**`。
- 接口签名：`RuntimeEvent.execute(input: DM14Input) -> DM14Result`。
- 数据表：`devmate_event`；迁移必须向前/向后兼容并保留审计事实。
- API：`/devmate/cases`；禁止把领域决策写入控制器。
- 状态：`created -> running -> waiting_approval -> completed -> failed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/devmate/release/test_dm_14.py`，失败原因只能是目标行为未实现。
- 可观察结果：发布候选通过回滚演练且未验证项显式保留。
- 回归命令：`python -m pytest tests/devmate -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

## 跨模块集成与真实性门禁

- 按依赖拓扑合并；每次合并后运行合同测试、全回归、构建、安全、故障恢复与回滚演练。
- 对数据库、消息、缓存、外部副作用执行崩溃点测试，核对幂等键、租约、Outbox/Inbox、SideEffect Ledger 和 UNKNOWN 对账。
- 远端分支保护、真实外部服务、真实模型或真实数据未执行时必须列为 unverified，不能以本地 Fake 结果替代。
- 所有模块构建、主集成优化、Bug 修复和最终验证前，禁止生成任何学习解释、项目总结、面试或简历文档。
