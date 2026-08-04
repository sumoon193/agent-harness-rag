"""DevMate DM-04 HTTP API 失败测试。

POST /devmate/cases、POST /devmate/cases/{case_id}/commands、
GET /devmate/cases/{case_id}/timeline：typed request/response、稳定错误码、
request/correlation ID 与权限校验；控制器不包含领域状态机逻辑。
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.devmate import create_devmate_router
from app.devmate.cases import CaseStore


@pytest.fixture()
def client() -> TestClient:
    store = CaseStore()
    app = FastAPI()
    app.include_router(create_devmate_router(store))
    with TestClient(app) as test_client:
        yield test_client


def _create_case(client: TestClient) -> str:
    response = client.post(
        "/devmate/cases",
        json={
            "case_id": "case-1",
            "actor_id": "u-1",
            "command_id": "cmd-create-1",
            "payload": {"subject": "s1"},
        },
    )
    assert response.status_code == 201
    return response.json()["case_id"]


def test_create_case_endpoint(client: TestClient) -> None:
    response = client.post(
        "/devmate/cases",
        json={
            "case_id": "case-1",
            "actor_id": "u-1",
            "command_id": "cmd-create-1",
            "payload": {"subject": "s1"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["case_id"] == "case-1"
    assert body["status"] == "created"


def test_command_endpoint_advances_status(client: TestClient) -> None:
    case_id = _create_case(client)

    response = client.post(
        f"/devmate/cases/{case_id}/commands",
        json={
            "command_id": "cmd-2",
            "event_type": "case.start",
            "target_status": "running",
            "actor_id": "u-1",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_illegal_transition_returns_stable_error(client: TestClient) -> None:
    case_id = _create_case(client)

    response = client.post(
        f"/devmate/cases/{case_id}/commands",
        json={
            "command_id": "cmd-2",
            "event_type": "case.skip",
            "target_status": "completed",
            "actor_id": "u-1",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "illegal_transition"


def test_unknown_case_returns_404(client: TestClient) -> None:
    response = client.post(
        "/devmate/cases/missing/commands",
        json={
            "command_id": "cmd-2",
            "event_type": "case.start",
            "target_status": "running",
            "actor_id": "u-1",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "case_not_found"


def test_missing_actor_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/devmate/cases",
        json={"case_id": "case-1", "command_id": "cmd-create-1"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "unauthorized"


def test_timeline_endpoint_returns_events(client: TestClient) -> None:
    case_id = _create_case(client)
    client.post(
        f"/devmate/cases/{case_id}/commands",
        json={
            "command_id": "cmd-2",
            "event_type": "case.start",
            "target_status": "running",
            "actor_id": "u-1",
        },
    )

    response = client.get(f"/devmate/cases/{case_id}/timeline")

    assert response.status_code == 200
    events = response.json()["events"]
    assert len(events) == 1
    assert events[0]["to_status"] == "running"


def test_request_id_is_echoed(client: TestClient) -> None:
    response = client.post(
        "/devmate/cases",
        json={
            "case_id": "case-1",
            "actor_id": "u-1",
            "command_id": "cmd-create-1",
        },
        headers={"X-Request-ID": "req-abc"},
    )

    assert response.status_code == 201
    assert response.headers.get("X-Request-ID") == "req-abc"
