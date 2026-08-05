# Python 死代码扫描（2026-07-26）

- 命令：`.venv/Scripts/python.exe -m vulture app --min-confidence 80`
- 工具版本：`vulture 2.16`
- 范围：`app/`
- 原则：FastAPI dependency、Pydantic model、Protocol adapter、插件/反射入口先按误报复核，不自动删除。

## 原始输出

```text
(无输出)
```

退出码：`0`。

## 逐项判断

本次扫描没有产生 finding，因此没有需要分类为框架入口、扩展点或可删除符号的条目。

## 结论

本轮只允许移除同时满足“仓库内零引用、非框架入口、非公开 Protocol、现有全量测试覆盖”的符号。当前没有符号满足删除条件，未删除任何生产代码。
