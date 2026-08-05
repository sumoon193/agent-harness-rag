"""Runtime 关键配置必须在公开文档中可发现。"""
from pathlib import Path


def test_env_example_documents_graph_checkpointer_configuration() -> None:
    """示例环境变量必须暴露 memory/postgres checkpointer 开关。"""
    content = Path(".env.example").read_text(encoding="utf-8")

    assert "GRAPH_CHECKPOINTER_BACKEND=memory" in content
    assert "GRAPH_CHECKPOINTER_POSTGRES_URL=" in content


def test_readme_explains_checkpoint_event_store_projection_boundary() -> None:
    """README 必须说明三种持久化职责，避免把 checkpoint 当业务事实库。"""
    content = Path("README.md").read_text(encoding="utf-8")

    assert "Checkpoint、Event Store 与 Projection" in content
    assert "GRAPH_CHECKPOINTER_BACKEND=postgres" in content
    assert "checkpoint 只保存执行位置" in content
