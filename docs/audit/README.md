# DevMate 审计输出

本目录保存 DM-W01-C1 的机器可校验审计事实，不是 Runtime Kernel 的实现目录。

`origin-map.jsonl` 每行对应一个仓库内相对路径，至少记录来源提交、许可证状态、领域分类、耦合标签、复用决定和证据引用。

复用决定含义：

- `allowed`：来源与许可证有明确证据，允许进入后续复用评审。
- `isolate`：来源可追溯，但属于 HR/RAG 领域，必须与 Runtime Kernel 隔离。
- `review`：证据不完整，需要人工复核。
- `blocked`：当前不能复用或发现硬性边界问题。

未知许可证或来源不明时，只能使用 `review` 或 `blocked`，不得推断为 `allowed`。
当前公开说明仅保留工程实施、验证和运维资料。
