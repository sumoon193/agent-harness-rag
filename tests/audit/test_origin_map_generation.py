"""Origin map generation behavior for DevMate W1-C1."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.audit_origin_map import generate_origin_map


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "audit@example.test")
    _git(tmp_path, "config", "user.name", "Audit Test")
    tracked = tmp_path / "tracked.py"
    tracked.write_text("value = 1\n", encoding="utf-8")
    chinese = tmp_path / "开发规划.md"
    chinese.write_text("规划文档\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.py", "开发规划.md")
    _git(tmp_path, "commit", "-m", "add tracked source")
    (tmp_path / "untracked.py").write_text("value = 2\n", encoding="utf-8")
    (tmp_path / ".env").write_text("QWEN_API_KEY=do-not-leak\n", encoding="utf-8")
    return tmp_path


def test_generate_origin_map_tracks_history_and_keeps_relative_paths(git_repo: Path) -> None:
    records = generate_origin_map(git_repo)

    by_path = {record["path"]: record for record in records}
    assert set(by_path) == {"tracked.py", "开发规划.md", "untracked.py", ".env"}
    assert len(by_path["tracked.py"]["source_commit"]) == 40
    assert by_path["untracked.py"]["source_commit"] == "untracked"
    assert by_path["untracked.py"]["reuse_decision"] in {"review", "blocked"}


def test_generate_origin_map_keeps_non_ascii_paths_verbatim(git_repo: Path) -> None:
    records = generate_origin_map(git_repo)

    by_path = {record["path"]: record for record in records}
    assert "开发规划.md" in by_path
    record = by_path["开发规划.md"]
    assert record["source_commit"] != "untracked"
    assert len(record["source_commit"]) == 40
    assert record["reuse_decision"] in {"allowed", "isolate", "review", "blocked"}


def test_generate_origin_map_never_emits_env_contents(git_repo: Path) -> None:
    records = generate_origin_map(git_repo)

    serialized = json.dumps(records, ensure_ascii=False)
    assert "do-not-leak" not in serialized
    assert "QWEN_API_KEY" not in serialized
    env_record = next(record for record in records if record["path"] == ".env")
    assert env_record["license_status"] in {"unknown", "review"}
    assert env_record["reuse_decision"] in {"review", "blocked"}
