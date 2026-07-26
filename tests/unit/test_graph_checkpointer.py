"""
Graph checkpointer 工厂与生命周期测试。

覆盖：
1. settings 驱动的后端选择（postgres → AsyncPostgresSaver）
2. 默认/无连接串时回退 MemorySaver
3. postgres 后端 setup/teardown 生命周期（幂等，不真连库）
4. 依赖缺失时的清晰报错
"""
from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.services.graph.checkpointer import (
    GraphCheckpointerManager,
    create_checkpointer_manager,
)


def _settings(**overrides: object) -> SimpleNamespace:
    """构造最小可用的 settings 兼容对象。"""
    base: dict[str, object] = {
        "graph_checkpointer_backend": "memory",
        "graph_checkpointer_postgres_url": "",
        "postgres_url": "",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class TestCheckpointerFactory:
    """工厂根据配置选择后端。"""

    def test_default_backend_falls_back_to_memory_saver(self) -> None:
        """默认配置回退进程内 MemorySaver，测试环境无需 Postgres。"""
        manager = create_checkpointer_manager(_settings())

        assert manager.backend == "memory"
        assert isinstance(manager.checkpointer, MemorySaver)

    def test_settings_default_checkpointer_backend_is_memory(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """真实 Settings 的默认 checkpointer 后端必须是 memory。"""
        from app.config import Settings

        monkeypatch.delenv("GRAPH_CHECKPOINTER_BACKEND", raising=False)
        settings = Settings(_env_file=None)

        assert settings.graph_checkpointer_backend == "memory"
        assert settings.graph_checkpointer_postgres_url == ""

    @pytest.mark.asyncio
    async def test_postgres_backend_with_conn_string_builds_async_postgres_saver(self) -> None:
        """postgres 后端 + 连接串 → AsyncPostgresSaver（连接池延迟打开，不连库）。

        AsyncPostgresSaver 构造时绑定当前事件循环，故须在异步上下文中调用工厂
        （与生产路径一致：容器在 FastAPI lifespan 内首次构建）。
        """
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        manager = create_checkpointer_manager(
            _settings(
                graph_checkpointer_backend="postgres",
                graph_checkpointer_postgres_url="postgresql://u:p@localhost:5432/db",
            )
        )

        assert manager.backend == "postgres"
        assert isinstance(manager.checkpointer, AsyncPostgresSaver)

    @pytest.mark.asyncio
    async def test_postgres_backend_conn_string_falls_back_to_postgres_url(self) -> None:
        """graph_checkpointer_postgres_url 为空时回退 postgres_url。"""
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        manager = create_checkpointer_manager(
            _settings(
                graph_checkpointer_backend="postgres",
                postgres_url="postgresql://u:p@localhost:5432/db",
            )
        )

        assert manager.backend == "postgres"
        assert isinstance(manager.checkpointer, AsyncPostgresSaver)

    def test_postgres_backend_in_sync_context_raises_clear_error(self) -> None:
        """纯同步上下文（无事件循环）构建 postgres checkpointer → 清晰报错。"""
        with pytest.raises(RuntimeError, match="事件循环"):
            create_checkpointer_manager(
                _settings(
                    graph_checkpointer_backend="postgres",
                    postgres_url="postgresql://u:p@localhost:5432/db",
                )
            )

    def test_postgres_backend_without_conn_string_falls_back_to_memory(self) -> None:
        """postgres 后端但连接串为空 → 回退 MemorySaver。"""
        manager = create_checkpointer_manager(
            _settings(graph_checkpointer_backend="postgres")
        )

        assert manager.backend == "memory"
        assert isinstance(manager.checkpointer, MemorySaver)

    def test_postgres_backend_missing_dependency_raises_clear_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """langgraph-checkpoint-postgres 缺失时报出含安装指引的错误。"""
        # sys.modules 中的 None 会让 import 直接抛 ImportError，模拟依赖缺失
        monkeypatch.setitem(sys.modules, "langgraph.checkpoint.postgres.aio", None)

        with pytest.raises(RuntimeError, match="langgraph-checkpoint-postgres"):
            create_checkpointer_manager(
                _settings(
                    graph_checkpointer_backend="postgres",
                    postgres_url="postgresql://u:p@localhost:5432/db",
                )
            )


class TestCheckpointerLifecycle:
    """setup/teardown 生命周期。"""

    @pytest.mark.asyncio
    async def test_memory_manager_setup_teardown_are_noops(self) -> None:
        """memory 后端 setup/teardown 为 no-op，可安全调用。"""
        manager = create_checkpointer_manager(_settings())

        await manager.setup()
        await manager.teardown()

    @pytest.mark.asyncio
    async def test_postgres_manager_setup_opens_pool_and_creates_tables(self) -> None:
        """postgres 后端 setup 打开连接池并建表，teardown 关闭连接池，且幂等。"""
        calls: list[str] = []

        class FakePool:
            async def open(self) -> None:
                calls.append("pool_open")

            async def close(self) -> None:
                calls.append("pool_close")

        class FakeSaver:
            async def setup(self) -> None:
                calls.append("saver_setup")

        manager = GraphCheckpointerManager(
            checkpointer=FakeSaver(),  # type: ignore[arg-type]
            backend="postgres",
            pool=FakePool(),
        )

        await manager.setup()
        await manager.setup()  # 幂等：第二次调用不重复打开
        await manager.teardown()
        await manager.teardown()  # 幂等：第二次调用不重复关闭

        assert calls == ["pool_open", "saver_setup", "pool_close"]
