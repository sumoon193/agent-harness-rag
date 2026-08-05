"""devmate 副作用台账：以 effect_id 幂等，UNKNOWN 可对账。"""

from __future__ import annotations

from app.devmate.git.types import SideEffect


class SideEffectLedger:
    def __init__(self) -> None:
        self._effects: dict[str, SideEffect] = {}
        self._by_release: dict[str, list[str]] = {}

    def add(self, effect: SideEffect) -> None:
        self._effects[effect.effect_id] = effect
        self._by_release.setdefault(effect.release_id, []).append(effect.effect_id)

    def effects_for(self, release_id: str) -> list[SideEffect]:
        return [self._effects[effect_id] for effect_id in self._by_release.get(release_id, [])]

    def needs_reconciliation(self, release_id: str) -> bool:
        return any(effect.status == "unknown" for effect in self.effects_for(release_id))

    def reconcile(self, release_id: str) -> list[SideEffect]:
        reconciled: list[SideEffect] = []
        for effect in self.effects_for(release_id):
            if effect.status == "unknown":
                effect = SideEffect(
                    effect_id=effect.effect_id,
                    release_id=effect.release_id,
                    kind=effect.kind,
                    target=effect.target,
                    status="reconciled",
                    created_at=effect.created_at,
                )
                self._effects[effect.effect_id] = effect
            reconciled.append(effect)
        return reconciled
