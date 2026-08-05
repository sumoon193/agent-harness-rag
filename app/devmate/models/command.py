"""Typed diagnosis command with explicit offline and real execution modes."""

from __future__ import annotations

from typing import Protocol

from app.devmate.models.parser import DiagnosisParseError, parse_typed_diagnosis
from app.devmate.models.types import DM07Input, DM07Result

DEFAULT_FAKE_RAW = (
    "summary=fake diagnosis\nseverity=warning\nrule=fake_rule\n"
    "confidence=0.8\nevidence=log,report\n"
)


class InvalidModeError(ValueError):
    """The requested model mode is not supported."""


class ModelUnavailableError(RuntimeError):
    """Real model execution requires an explicitly configured provider."""


class ModelProvider(Protocol):
    def generate(self, *, case_id: str, prompt: str) -> str: ...


class CaseCommand:
    def __init__(
        self,
        fake_raw: str = DEFAULT_FAKE_RAW,
        parser=parse_typed_diagnosis,
        model_provider: ModelProvider | None = None,
    ) -> None:
        self._fake_raw = fake_raw
        self._parser = parser
        self._model_provider = model_provider

    def execute(self, input_: DM07Input) -> DM07Result:
        if input_.mode == "fake":
            raw, actual_mode, degraded = self._fake_raw, "fake", False
        elif input_.mode == "recorded":
            raw = (input_.recorded or {}).get(input_.case_id)
            if raw is None:
                raw, actual_mode, degraded = self._fake_raw, "fake", True
            else:
                actual_mode, degraded = "recorded", False
        elif input_.mode == "real":
            if self._model_provider is None:
                raise ModelUnavailableError("real mode requires a configured model provider")
            raw = self._model_provider.generate(
                case_id=input_.case_id,
                prompt=(
                    "Return a typed DevMate diagnosis using summary, severity, rule, "
                    "confidence and evidence fields. Case: " + input_.case_id
                ),
            )
            actual_mode, degraded = "real", False
        else:
            raise InvalidModeError(input_.mode)

        try:
            diagnosis = self._parser(raw)
        except DiagnosisParseError:
            if input_.mode == "real":
                raise
            diagnosis = self._parser(self._fake_raw)
            degraded = True

        return DM07Result(
            case_id=input_.case_id,
            diagnosis=diagnosis,
            mode=actual_mode,
            degraded=degraded,
            audit={"requested_mode": input_.mode, "actual_mode": actual_mode},
        )
