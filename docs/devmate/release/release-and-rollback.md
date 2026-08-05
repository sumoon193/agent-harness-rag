# DevMate 发布与回滚规范

- 每个发布候选必须绑定 `target_commit` 与 `rollback_commit`。
- 发布前必须运行回滚演练：所有 release steps 均执行且可回滚到 `rollback_commit`。
- 缺少 `rollback_commit` 时演练失败，候选不得发布。
- 未验证项（外部服务、真实模型、远端分支保护等）必须显式保留并列出，
  不得以本地 Fake/Recorded 结果冒充已验证。
- 真实性审计：所有验证门禁从 Git 重新计算，不信任模型自报。
