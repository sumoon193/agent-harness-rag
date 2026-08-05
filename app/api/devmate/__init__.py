"""devmate CI/CD HTTP API 路由包。

暴露模块级 ``router``（挂载 /devmate/cases）和 ``webhook_router``
（挂载 /webhooks/github），两者共享进程内 ``CaseStore`` 与
``IngestionStore`` 单例。fallback 模式下使用内存确定性实现，不接真实
GitHub/Docker/LLM。
"""

from __future__ import annotations

from app.api.devmate.router import create_devmate_router
from app.api.devmate.webhook import create_webhook_router
from app.devmate.cases import CaseStore
from app.devmate.ingestion import IngestionStore

# 进程内单例：fallback 模式下整个进程共享同一 Case/Ingestion store。
# full 模式应替换为持久化 adapter（见 app/devmate/runtime 的 projection/event_store）。
_case_store = CaseStore()
_ingestion_store = IngestionStore()

router = create_devmate_router(_case_store)
webhook_router = create_webhook_router(
    case_store=_case_store,
    ingestion_store=_ingestion_store,
)

__all__ = ["router", "webhook_router"]