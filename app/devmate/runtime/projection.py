"""可从事件流重建的确定性投影。"""

from __future__ import annotations

from typing import Any

from app.devmate.runtime.models import StoredEvent


class Projection:
    """按 aggregate 聚合事件；从空状态重放全部事件即可重建。"""

    def reduce(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        item = state.setdefault(
            event.aggregate_id,
            {"event_count": 0, "types": [], "last_version": 0, "last_updated_at": ""},
        )
        item["event_count"] += 1
        item["types"].append(event.event_type)
        item["last_version"] = event.version
        item["last_updated_at"] = event.created_at
        return state

    def rebuild(self, events: list[StoredEvent]) -> dict[str, Any]:
        state: dict[str, Any] = {}
        for event in events:
            self.reduce(state, event)
        return state
