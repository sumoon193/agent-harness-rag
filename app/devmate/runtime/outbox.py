"""同事务 Outbox（内存实现），以 outbox_id 幂等去重。"""

from __future__ import annotations

from app.devmate.runtime.models import OutboxMessage


class Outbox:
    """追加式 Outbox；重复 outbox_id 静默忽略，保证重放安全。"""

    def __init__(self) -> None:
        self._messages: list[OutboxMessage] = []
        self._by_id: dict[str, OutboxMessage] = {}

    def enqueue(self, message: OutboxMessage) -> None:
        if message.outbox_id in self._by_id:
            return
        self._messages.append(message)
        self._by_id[message.outbox_id] = message

    def unread(self) -> list[OutboxMessage]:
        return list(self._messages)

    def size(self) -> int:
        return len(self._messages)
