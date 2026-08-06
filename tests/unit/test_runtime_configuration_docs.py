from pathlib import Path


def test_env_example_documents_graph_checkpointer_configuration() -> None:
    content = Path(".env.example").read_text(encoding="utf-8")

    assert "GRAPH_CHECKPOINTER_BACKEND=memory" in content
    assert "GRAPH_CHECKPOINTER_POSTGRES_URL=" in content


def test_readme_explains_checkpoint_event_store_projection_boundary() -> None:
    content = Path("README.md").read_text(encoding="utf-8")

    assert "Checkpoint、Event Store 与 Projection" in content
    assert "GRAPH_CHECKPOINTER_BACKEND=postgres" in content
    assert "Checkpoint 只保存执行位置" in content
