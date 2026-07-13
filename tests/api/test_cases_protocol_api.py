"""Case、MCP 与 A2A HTTP API 测试。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import reset_container
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    """每个测试使用独立 fallback service container。"""
    reset_container()
    with TestClient(create_app()) as test_client:
        yield test_client
    reset_container()


def _create_case(client: TestClient) -> dict:
    response = client.post(
        "/cases",
        json={
            "title": "新员工入职到转正",
            "tenant_id": "tenant_001",
            "subject_user_id": "user_employee",
            "actor_id": "user_hr",
            "command_id": "cmd_case_api_create",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_case_api_supports_versioned_messages_and_event_cursor(client: TestClient) -> None:
    """Case API 应通过 expected_version 与 sequence cursor 驱动长期会话。"""
    case = _create_case(client)

    message = client.post(
        f"/cases/{case['id']}/messages",
        json={
            "message": "员工已提交入职材料",
            "actor_id": "user_employee",
            "command_id": "cmd_case_api_message",
            "expected_version": 1,
        },
    )
    assert message.status_code == 200
    assert message.json()["version"] == 2

    events = client.get(f"/cases/{case['id']}/events", params={"after_sequence": 1})
    assert events.status_code == 200
    assert [item["sequence"] for item in events.json()["items"]] == [2]

    stream = client.get(f"/cases/{case['id']}/stream", params={"after_sequence": 0})
    assert stream.status_code == 200
    assert "id: 1" in stream.text
    assert "id: 2" in stream.text


def test_case_api_lists_query_projections_for_operations_queue(client: TestClient) -> None:
    """运维控制台应能读取按更新时间排序的 Case projection 队列。"""
    created = _create_case(client)

    response = client.get("/cases")

    assert response.status_code == 200
    items = response.json()
    assert [item["id"] for item in items] == [created["id"]]
    assert items[0]["status"] == "open"


def test_mcp_and_a2a_http_protocol_endpoints(client: TestClient) -> None:
    """本地 HTTP 应暴露 MCP capability negotiation 与 A2A read-only peer。"""
    initialized = client.post(
        "/mcp",
        params={"run_id": "run_protocol_api"},
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert initialized.status_code == 200
    assert initialized.json()["result"]["protocolVersion"] == "2025-11-25"

    card = client.get("/.well-known/agent-card.json")
    assert card.status_code == 200
    assert card.json()["capabilities"]["writeActions"] is False

    task = client.post(
        "/a2a/tasks",
        json={
            "context_id": "case_001",
            "text": "研究当前入职制度需要哪些材料",
            "user_id": "user_hr",
        },
    )
    assert task.status_code == 200
    assert task.json()["status"] == "completed"
    assert task.json()["artifacts"][0]["metadata"]["read_only"] is True


def test_runtime_metrics_endpoint_reports_case_events(client: TestClient) -> None:
    """控制台应能读取 Case/Event/Outbox 工程指标。"""
    _create_case(client)

    response = client.get("/metrics/runtime")

    assert response.status_code == 200
    data = response.json()
    assert data["counters"]["runtime.events.total"] == 1
    assert data["gauges"]["runtime.outbox.backlog"] == 1.0


def test_case_policy_refresh_api_creates_new_bound_approval(client: TestClient) -> None:
    """制度更新 API 应重建 evidence/plan 并回到 waiting_approval。"""
    case = _create_case(client)
    started = client.post(
        f"/cases/{case['id']}/start",
        json={
            "actor_id": "user_hr",
            "command_id": "cmd_policy_api_start",
            "expected_version": case["version"],
        },
    ).json()
    approval_id = started["working_memory"]["approvals"][-1]["approval_id"]
    waiting_timer = client.post(
        f"/cases/{case['id']}/approvals/{approval_id}",
        json={
            "decision": "approve",
            "actor_id": "user_manager",
            "command_id": "cmd_policy_api_approve",
            "expected_version": started["version"],
        },
    ).json()

    response = client.post(
        f"/cases/{case['id']}/policies/refresh",
        json={
            "policy_version": "v2",
            "actor_id": "user_hr",
            "command_id": "cmd_policy_api_refresh",
            "expected_version": waiting_timer["version"],
        },
    )

    assert response.status_code == 200
    refreshed = response.json()
    assert refreshed["status"] == "waiting_approval"
    assert refreshed["working_memory"]["evidence"][0]["document_version"] == "v2"


def test_case_workflow_api_exposes_governed_reference_scenario(client: TestClient) -> None:
    """Case API 应暴露可审批恢复的入职到转正 Reference Application。"""
    case = _create_case(client)

    started = client.post(
        f"/cases/{case['id']}/start",
        json={
            "actor_id": "user_hr",
            "command_id": "cmd_case_api_start",
            "expected_version": case["version"],
        },
    )

    assert started.status_code == 200
    waiting = started.json()
    assert waiting["status"] == "waiting_approval"
    approval_id = waiting["working_memory"]["approvals"][-1]["approval_id"]

    approved = client.post(
        f"/cases/{case['id']}/approvals/{approval_id}",
        json={
            "decision": "approve",
            "actor_id": "user_manager",
            "command_id": "cmd_case_api_approve",
            "expected_version": waiting["version"],
        },
    )

    assert approved.status_code == 200
    resumed = approved.json()
    assert resumed["status"] == "waiting_timer"
    assert resumed["working_memory"]["tool_results"][-1]["result"]["ticket_id"]

    metrics = client.get("/metrics/runtime").json()
    assert metrics["counters"]["runtime.cases.started"] == 1
    assert metrics["counters"]["runtime.protocol.a2a.success"] == 1
    assert metrics["counters"]["runtime.protocol.mcp.success"] == 1
    assert metrics["counters"]["runtime.approvals.decided"] == 1
    assert metrics["counters"]["runtime.side_effects.succeeded"] == 1
    assert metrics["counters"]["runtime.approval_bypass.total"] == 0
    assert metrics["counters"]["runtime.unsafe_tool_execution.total"] == 0
