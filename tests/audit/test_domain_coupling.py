"""DevMate W1-C1 领域耦合扫描失败测试。

扫描器必须把 Runtime Kernel 范围内直接引用 HR/RAG schema、prompt、
API、配置或 reference workflow 的 Python 文件标为 blocked，且不触碰
runtime 范围之外的文件。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.scan_domain_coupling import scan_domain_coupling


def _git(repo: Path, *args: str) -> None:
    import subprocess

    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


@pytest.fixture()
def runtime_repo(tmp_path: Path) -> Path:
    """包含一个违规 runtime 文件、一个干净 runtime 文件和一个越界文件。"""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "audit@example.test")
    _git(tmp_path, "config", "user.name", "Audit Test")

    runtime = tmp_path / "runtime"
    runtime.mkdir()

    engine = runtime / "engine.py"
    engine.write_text(
        "from app.schemas.runtime import HRCase\n\n"
        "def start() -> HRCase:\n"
        "    return HRCase()\n",
        encoding="utf-8",
    )

    clean = runtime / "clean.py"
    clean.write_text(
        "from app.services.runtime.interfaces import EventStore\n\n"
        "def run(store: EventStore) -> None:\n"
        "    return None\n",
        encoding="utf-8",
    )

    outside = tmp_path / "outside.py"
    outside.write_text("import HRCase\n", encoding="utf-8")

    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "add runtime fixture")
    return tmp_path


def test_scan_flags_runtime_file_importing_hr_schema_as_blocked(runtime_repo: Path) -> None:
    records = {record["path"]: record for record in scan_domain_coupling(runtime_repo)}

    engine = records["runtime/engine.py"]
    assert engine["conclusion"] == "blocked"
    assert any(hit["rule"] == "schema-hr-case" for hit in engine["hits"])


def test_scan_keeps_clean_runtime_file_ok(runtime_repo: Path) -> None:
    records = {record["path"]: record for record in scan_domain_coupling(runtime_repo)}

    assert records["runtime/clean.py"]["conclusion"] == "ok"
    assert records["runtime/clean.py"]["hits"] == []


def test_scan_ignores_files_outside_runtime_scope(runtime_repo: Path) -> None:
    records = {record["path"]: record for record in scan_domain_coupling(runtime_repo)}

    assert "outside.py" not in records
