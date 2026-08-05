"""公开工程文档的结构、真实性与清理边界。"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"

EXPECTED_SECTIONS = [
    "项目简介",
    "核心能力",
    "技术栈与架构",
    "本地启动",
    "主要 API",
    "离线测试",
    "真实服务验证",
    "安全与使用边界",
    "License",
]

REMOVED_PRESENTATION_FILES = [
    "README-DEVMATE.md",
    "RAG项目面试亮点.md",
    "项目亮点.md",
    "docs/面试高频问答与话术.md",
    "docs/agent-harness-deepening/05-metrics-and-resume-evidence.md",
    "docs/evidence/landing-narrative-design.md",
    "docs/superpowers/plans/2026-07-26-python-handoff-closure.md",
    "docs/superpowers/specs/2026-07-26-python-handoff-closure-design.md",
]

PROHIBITED_PUBLIC_TERMS = (
    "面试",
    "简历",
    "履历",
    "问答话术",
    "项目亮点",
    "学习证明",
    "完成证明",
    "学习材料",
)


def _read_utf8(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def _public_markdown_files() -> list[Path]:
    files = [
        README,
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / ".agent-governance" / "AGENT-ENTRY.md",
        ROOT / ".agent-governance" / "implementation-plan.md",
    ]
    files.extend((ROOT / "docs").rglob("*.md"))
    return sorted({path for path in files if path.is_file()})


def test_readme_uses_exact_chinese_engineering_structure() -> None:
    text = _read_utf8(README)
    headings = [
        line.removeprefix("## ").strip()
        for line in text.splitlines()
        if line.startswith("## ")
    ]

    assert headings == EXPECTED_SECTIONS
    assert text.startswith("# DevMate")
    assert not re.search(r"[銆锛鈥�]", text)
    assert "fake" not in text.casefold()


def test_readme_matches_runtime_commands_api_and_live_smoke_contract() -> None:
    text = _read_utf8(README)
    required_fragments = (
        "Python 3.12",
        "FastAPI",
        "Vue 3",
        "Qwen",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5173",
        "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload",
        "npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173",
        "POST /devmate/cases",
        "POST /devmate/cases/{case_id}/commands",
        "GET /devmate/cases/{case_id}/timeline",
        "POST /webhooks/github",
        "GET /health",
        "python -m pytest -q -p no:cacheprovider",
        "npm --prefix frontend run build",
        "scripts/devmate/live_smoke.py --component health",
        "scripts/devmate/live_smoke.py --component model",
        "DEVMATE_BASE_URL",
        "QWEN_API_KEY",
        "QWEN_CHAT_MODEL",
        "QWEN_BASE_URL",
        "退出码 `0`",
        "退出码 `1`",
        "退出码 `2`",
        "Apache License 2.0",
    )

    for fragment in required_fragments:
        assert fragment in text, f"README 缺少真实契约：{fragment}"


def test_readme_local_links_resolve() -> None:
    text = _read_utf8(README)
    targets = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)

    for target in targets:
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path_part = target.split("#", 1)[0]
        assert (ROOT / path_part).exists(), f"README 本地链接失效：{target}"


def test_presentation_materials_are_removed_and_deprotected() -> None:
    for relative_path in REMOVED_PRESENTATION_FILES:
        assert not (ROOT / relative_path).exists(), f"仍保留展示型文件：{relative_path}"

    manifest = json.loads(
        _read_utf8(ROOT / ".agent-governance" / "manifest.json")
    )
    for key in ("protected_paths", "sensitive_paths", "allowed_untracked_paths"):
        assert "README-DEVMATE.md" not in manifest[key]


def test_public_engineering_documents_exclude_presentation_language() -> None:
    violations: list[str] = []
    for path in _public_markdown_files():
        relative_path = path.relative_to(ROOT).as_posix()
        text = _read_utf8(path)
        for term in PROHIBITED_PUBLIC_TERMS:
            if term in relative_path or term in text:
                violations.append(f"{relative_path}: {term}")

    assert not violations, "公开工程文档仍有展示型措辞：\n" + "\n".join(violations)


def test_mutable_governance_uses_engineering_materials_rule() -> None:
    expected = "仅保留工程实施、验证和运维资料"
    paths = (
        ROOT / ".agent-governance" / "AGENT-ENTRY.md",
        ROOT / ".agent-governance" / "implementation-plan.md",
        ROOT / ".agent-governance" / "module-contracts.json",
    )

    for path in paths:
        assert expected in _read_utf8(path), f"当前治理说明未统一：{path.name}"
