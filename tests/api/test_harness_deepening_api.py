"""
Agent Harness 深化 API 测试。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import reset_container
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    """每次测试重置容器，保证状态隔离。"""
    from app.api.documents import reset_documents_store

    reset_container()
    reset_documents_store()
    try:
        yield TestClient(create_app())
    finally:
        reset_container()
        reset_documents_store()


def test_agent_run_detail_returns_artifact_timeline(client: TestClient) -> None:
    """Agent Run 详情应返回可复盘 artifact timeline。"""
    create_resp = client.post(
        "/agent-runs",
        json={"query": "新员工入职到转正要办哪些事项？", "user_id": "user_001"},
    )
    assert create_resp.status_code == 201
    run_id = create_resp.json()["id"]

    detail_resp = client.get(f"/agent-runs/{run_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()

    assert "timeline" in detail
    event_types = [event["event_type"] for event in detail["timeline"]]
    assert "run_created" in event_types
    assert "evidence_retrieved" in event_types
    assert "plan_generated" in event_types
    assert "approval_requested" in event_types


def test_safety_eval_endpoint_returns_structured_report(client: TestClient) -> None:
    """安全评测端点应返回分类型通过率和失败样例。"""
    resp = client.post("/eval/safety", json={})

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cases"] >= 5
    assert "pass_rate_by_category" in data
    assert "missing_citation" in data["pass_rate_by_category"]
    assert isinstance(data["failed_case_ids"], list)
