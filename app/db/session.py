"""
数据库会话管理。

提供 async engine、session 工厂和生命周期方法。
仅在 app_mode=full 时使用；fallback 模式不依赖此模块。
"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.models.base import Base

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_url(raw_url: str) -> str:
    """将 postgresql:// 转换为 postgresql+asyncpg://。"""
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw_url


async def init_db() -> None:
    """初始化数据库引擎并创建所有表。"""
    global _engine, _session_factory

    settings = get_settings()
    url = _build_url(settings.postgres_url)

    _engine = create_async_engine(url, echo=False, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

    import app.models  # noqa: F401

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database_initialized", extra={"url": url.split("@")[-1]})


async def close_db() -> None:
    """关闭数据库引擎。"""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("database_closed")


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取 session 工厂（供 Manager 层使用）。"""
    if _session_factory is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：获取数据库 session。"""
    factory = get_session_factory()
    async with factory() as session:
        yield session
