"""FastAPI lifespan 对 graph checkpointer 的资源回收契约。"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI

import app.api.dependencies as dependencies
import app.main as app_main


@pytest.mark.asyncio
async def test_lifespan_tears_down_postgres_checkpointer_when_app_body_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """请求处理阶段异常也必须关闭 postgres checkpointer 连接池。"""
    calls: list[str] = []

    class FakeManager:
        async def setup(self) -> None:
            calls.append("setup")

        async def teardown(self) -> None:
            calls.append("teardown")

    settings = SimpleNamespace(
        app_mode="fallback",
        graph_checkpointer_backend="postgres",
    )
    monkeypatch.setattr(app_main, "get_settings", lambda: settings)
    monkeypatch.setattr(
        dependencies,
        "get_container",
        lambda: SimpleNamespace(graph_checkpointer=FakeManager()),
    )

    with pytest.raises(RuntimeError, match="boom"):
        async with app_main.lifespan(FastAPI()):
            raise RuntimeError("boom")

    assert calls == ["setup", "teardown"]
