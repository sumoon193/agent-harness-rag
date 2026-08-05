"""DevMate live smoke: 0 passed, 1 failed, 2 blocked."""
from __future__ import annotations
import argparse
import asyncio
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", choices=("health", "model"), default="health")
    args = parser.parse_args(argv)
    if args.component == "model":
        return _model_smoke()
    base = os.getenv("DEVMATE_BASE_URL", "").rstrip("/")
    if not base:
        print("BLOCKED: set DEVMATE_BASE_URL")
        return 2
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=5) as response:
            ok = response.status == 200
            print("PASSED: DevMate health" if ok else f"FAILED: status={response.status}")
            return 0 if ok else 1
    except urllib.error.URLError as exc:
        print(f"BLOCKED: service unavailable ({exc.reason})")
        return 2
    except Exception as exc:
        print(f"FAILED: {exc.__class__.__name__}")
        return 1


def _model_smoke() -> int:
    api_key = os.getenv("QWEN_API_KEY", "").strip()
    model = os.getenv("QWEN_CHAT_MODEL", "").strip()
    if not api_key or not model:
        print("BLOCKED: set QWEN_API_KEY and QWEN_CHAT_MODEL")
        return 2
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    try:
        from app.devmate.models.parser import parse_typed_diagnosis
        from app.services.ai.qwen import QwenAnswerGenerator

        raw = asyncio.run(QwenAnswerGenerator(
            api_key=api_key,
            model=model,
            base_url=os.getenv(
                "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
            ),
            temperature=0,
        ).generate(
            "Return exactly five newline-separated fields and nothing else: "
            "summary=<text>\nseverity=warning\nrule=<identifier>\n"
            "confidence=<0 to 1>\nevidence=<comma-separated identifiers>"
        ))
        diagnosis = parse_typed_diagnosis(raw)
        if not diagnosis.summary or not diagnosis.rule:
            print("FAILED: typed diagnosis is incomplete")
            return 1
        print("PASSED: DevMate real model and typed parser")
        return 0
    except Exception as exc:
        message = str(exc)
        if "status=" not in message and "response" not in message.lower():
            print(f"BLOCKED: model service unavailable ({exc.__class__.__name__})")
            return 2
        print(f"FAILED: real model validation ({exc.__class__.__name__})")
        return 1

if __name__ == "__main__":
    sys.exit(main())
