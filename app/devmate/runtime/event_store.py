"""追加式、带版本与幂等键的事件存储（内存实现）。"""

from __future__ import annotations

from app.devmate.runtime.models import StoredEvent


class ConcurrentVersionError(Exception):
    """期望版本与当前版本冲突。"""


class EventStore:
    """按 aggregate 追加事件，event_id 幂等去重，乐观版本控制。"""

    def __init__(self) -> None:
        self._streams: dict[str, list[StoredEvent]] = {}
        self._by_event_id: dict[str, StoredEvent] = {}
        self._order: list[StoredEvent] = []

    def append(self, event: StoredEvent, *, expected_version: int) -> None:
        if event.event_id in self._by_event_id:
            return
        stream = self._streams.setdefault(event.aggregate_id, [])
        if len(stream) != expected_version:
            raise ConcurrentVersionError(
                f"expected version {expected_version}, current {len(stream)}"
            )
        stream.append(event)
        self._by_event_id[event.event_id] = event
        self._order.append(event)

    def load_stream(self, aggregate_id: str) -> list[StoredEvent]:
        return list(self._streams.get(aggregate_id, []))

    def all_events(self) -> list[StoredEvent]:
        return list(self._order)

    def size(self) -> int:
        return len(self._order)
