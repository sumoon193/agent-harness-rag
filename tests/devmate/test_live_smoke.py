import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "devmate" / "live_smoke.py"


def _module():
    spec = importlib.util.spec_from_file_location("devmate_live_smoke", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_model_smoke_is_blocked_without_real_credentials(monkeypatch):
    module = _module()
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_CHAT_MODEL", raising=False)

    assert module.main(["--component", "model"]) == 2


def test_ragas_smoke_is_blocked_without_real_credentials(monkeypatch):
    module = _module()
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    assert module.main(["--component", "ragas"]) == 2


def test_ragas_smoke_uses_unicode_safe_fixture() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "\\u4f01\\u4e1a" in source


def test_queue_component_is_dispatchable(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module, "_queue_smoke", lambda: 0, raising=False)

    assert module.main(["--component", "queue"]) == 0


def test_otel_component_is_dispatchable(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module, "_otel_smoke", lambda: 0, raising=False)

    assert module.main(["--component", "otel"]) == 0


def test_mcp_component_is_dispatchable(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module, "_mcp_smoke", lambda: 0, raising=False)

    assert module.main(["--component", "mcp"]) == 0
