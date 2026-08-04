"""模型 typed diagnosis command：Fake/Recorded 可降级。

合同：``CaseCommand.execute(input: DM07Input) -> DM07Result``。
模型输出经 typed parser；模型不可用（real 模式，网络禁用）或输出非法
时降级到确定性 Fake/Recorded 结果。
"""

from __future__ import annotations

from app.devmate.models.parser import DiagnosisParseError, parse_typed_diagnosis
from app.devmate.models.types import DM07Input, DM07Result

DEFAULT_FAKE_RAW = (
    "summary=fake diagnosis\nseverity=warning\nrule=fake_rule\n"
    "confidence=0.8\nevidence=log,report\n"
)


class InvalidModeError(ValueError):
    """未知模型模式。"""


class CaseCommand:
    def __init__(self, fake_raw: str = DEFAULT_FAKE_RAW, parser=parse_typed_diagnosis) -> None:
        self._fake_raw = fake_raw
        self._parser = parser

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
            # 网络禁用：真实模型不可用，固定降级到 Fake。
            raw, actual_mode, degraded = self._fake_raw, "fake", True
        else:
            raise InvalidModeError(input_.mode)

        try:
            diagnosis = self._parser(raw)
        except DiagnosisParseError:
            diagnosis = self._parser(self._fake_raw)
            degraded = True

        return DM07Result(
            case_id=input_.case_id,
            diagnosis=diagnosis,
            mode=actual_mode,
            degraded=degraded,
            audit={"requested_mode": input_.mode, "actual_mode": actual_mode},
        )
