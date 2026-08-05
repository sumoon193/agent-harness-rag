"""公开工程文档的结构、真实性与清理边界。"""

from __future__ import annotations

import json
import ast
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace


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
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--",
            "*.md",
            ":(exclude)_archive/**",
            ":(exclude).agent-governance/tasks/**",
            ":(exclude).agent-governance/handoffs/**",
            ":(exclude)tests/fixtures/**",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = result.stdout.decode("utf-8").split("\0")
    return [ROOT / path for path in paths if path and (ROOT / path).is_file()]


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


def test_public_markdown_inventory_covers_nested_engineering_documents() -> None:
    relative_paths = {
        path.relative_to(ROOT).as_posix() for path in _public_markdown_files()
    }

    assert "demo_docs/badcases/README.md" in relative_paths
    assert "frontend/README.md" not in relative_paths, "重复的前端模板 README 应删除"
    assert not any(path.startswith("_archive/") for path in relative_paths)
    assert not any(
        path.startswith(".agent-governance/tasks/") for path in relative_paths
    )
    assert not any(
        path.startswith(".agent-governance/handoffs/") for path in relative_paths
    )
    assert not any(path.startswith("tests/fixtures/") for path in relative_paths)


def test_public_markdown_does_not_reference_removed_presentation_files() -> None:
    violations: list[str] = []
    removed_names = {
        Path(relative_path).name for relative_path in REMOVED_PRESENTATION_FILES
    }

    for path in _public_markdown_files():
        relative_path = path.relative_to(ROOT).as_posix()
        text = _read_utf8(path)
        for removed_name in removed_names:
            if removed_name in text:
                violations.append(f"{relative_path}: {removed_name}")

    assert not violations, "公开 Markdown 仍引用已删除文件：\n" + "\n".join(violations)


def test_development_plan_uses_engineering_language_only() -> None:
    text = _read_utf8(ROOT / "开发规划.md")

    for term in (
        "项目亮点",
        "RAG项目面试亮点",
        "面试可演示",
        "前端演示台",
        "重点展示",
        "核心亮点",
        "对应亮点",
        "前端展示",
    ):
        assert term not in text, f"开发规划仍有展示型措辞：{term}"


def _load_runner_command_functions(platform_name: str, which):
    source = _read_utf8(ROOT / "tools" / "governance" / "run.py")
    tree = ast.parse(source)
    names = {"_strip_paired_quotes", "_split_command", "_resolve_command"}
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    assert {node.name for node in functions} == names, "治理运行器缺少命令解析函数"

    def blocked(message: str) -> None:
        raise SystemExit("blocked: " + message)

    namespace = {
        "os": SimpleNamespace(name=platform_name),
        "shlex": __import__("shlex"),
        "shutil": SimpleNamespace(which=which),
        "sys": SimpleNamespace(executable=r"D:\py\python.exe"),
        "blocked": blocked,
    }
    isolated_module = ast.Module(body=functions, type_ignores=[])
    ast.fix_missing_locations(isolated_module)
    exec(compile(isolated_module, "tools/governance/run.py", "exec"), namespace)
    return namespace


def test_governance_runner_preserves_windows_relative_venv_path() -> None:
    namespace = _load_runner_command_functions("nt", lambda command: None)

    arguments = namespace["_split_command"](
        r".\.venv\Scripts\python.exe -m pytest tests\governance"
    )

    assert arguments == [
        r".\.venv\Scripts\python.exe",
        "-m",
        "pytest",
        r"tests\governance",
    ]


def test_governance_runner_preserves_quoted_windows_path_with_spaces() -> None:
    namespace = _load_runner_command_functions("nt", lambda command: None)

    arguments = namespace["_split_command"](
        r'"D:\Code Space\.venv\Scripts\python.exe" -m pytest'
    )

    assert arguments == [r"D:\Code Space\.venv\Scripts\python.exe", "-m", "pytest"]


def test_governance_runner_resolves_windows_npm_cmd() -> None:
    calls: list[str] = []

    def which(command: str) -> str | None:
        calls.append(command)
        if command == "npm.cmd":
            return r"C:\Program Files\nodejs\npm.cmd"
        return None

    namespace = _load_runner_command_functions("nt", which)

    arguments = namespace["_resolve_command"](
        namespace["_split_command"]("npm --prefix frontend")
    )

    assert arguments == [
        r"C:\Program Files\nodejs\npm.cmd",
        "--prefix",
        "frontend",
    ]
    assert calls == ["npm", "npm.cmd"]


def test_governance_runner_uses_posix_tokens_on_linux() -> None:
    namespace = _load_runner_command_functions("posix", lambda command: None)

    arguments = namespace["_split_command"](
        'python -m pytest "tests/path with space/test_contract.py"'
    )

    assert arguments == [
        "python",
        "-m",
        "pytest",
        "tests/path with space/test_contract.py",
    ]


def test_governance_runner_blocks_empty_command() -> None:
    namespace = _load_runner_command_functions("nt", lambda command: None)

    try:
        namespace["_split_command"]("   ")
    except SystemExit as error:
        assert str(error) == "blocked: task command is empty"
    else:
        raise AssertionError("空命令必须明确 blocked")


def test_mutable_governance_uses_engineering_materials_rule() -> None:
    expected = "仅保留工程实施、验证和运维资料"
    paths = (
        ROOT / ".agent-governance" / "AGENT-ENTRY.md",
        ROOT / ".agent-governance" / "implementation-plan.md",
        ROOT / ".agent-governance" / "module-contracts.json",
    )

    for path in paths:
        assert expected in _read_utf8(path), f"当前治理说明未统一：{path.name}"
