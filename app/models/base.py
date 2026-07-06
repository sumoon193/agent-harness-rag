"""
SQLAlchemy 基础模型。

使用 SQLAlchemy 2.0 的 DeclarativeBase 和 Mapped 类型注解。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""
    pass


class TimestampMixin:
    """时间戳混入类，提供 created_at 和 updated_at 字段。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间（UTC）"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间（UTC）"
    )


class IDMixin:
    """ID 混入类，提供字符串主键。"""

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="主键 ID"
    )
