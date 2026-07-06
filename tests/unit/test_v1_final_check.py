"""
V1 收尾验收脚本测试。

这些测试只使用 fake socket/checker，不依赖 Docker、云 API 或真实网络。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def load_v1_final_check_module() -> ModuleType:
    """从 scripts 目录加载 v1_final_check.py。"""
    module_path = Path("scripts") / "v1_final_check.py"
    spec = importlib.util.spec_from_file_location("v1_final_check", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tcp_check_reports_down_port_without_throwing(monkeypatch: Any) -> None:
    """TCP 探测连接失败时返回 down，而不是抛异常。"""
    module = load_v1_final_check_module()

    def fake_create_connection(address: tuple[str, int], timeout: float) -> None:
        raise OSError("connection refused")

    monkeypatch.setattr(module.socket, "create_connection", fake_create_connection)

    result = module.tcp_check(
        module.ServiceEndpoint(name="Redis", host="localhost", port=6379),
        timeout_seconds=0.01,
    )

    assert result.name == "Redis"
    assert result.status == "down"
    assert "connection refused" in result.detail


def test_full_preflight_uses_injected_checker() -> None:
    """full preflight 应支持注入 checker，便于无网络单元测试。"""
    module = load_v1_final_check_module()
    endpoints = [
        module.ServiceEndpoint(name="PostgreSQL", host="localhost", port=5432),
        module.ServiceEndpoint(name="Redis", host="localhost", port=6379),
    ]

    def fake_checker(endpoint: Any, timeout_seconds: float) -> Any:
        status = "up" if endpoint.name == "PostgreSQL" else "down"
        return module.ServiceProbeResult(
            name=endpoint.name,
            host=endpoint.host,
            port=endpoint.port,
            status=status,
            detail=f"fake {status}",
        )

    results = module.run_full_preflight(
        endpoints=endpoints,
        checker=fake_checker,
        timeout_seconds=0.01,
    )

    assert [result.name for result in results] == ["PostgreSQL", "Redis"]
    assert [result.status for result in results] == ["up", "down"]
    assert module.has_down_service(results) is True


def test_main_keeps_default_exit_zero_when_full_services_are_down(monkeypatch: Any) -> None:
    """默认模式用于 V1 本地收尾，外部 full 服务未启动时只提示阻塞，不让脚本失败。"""
    module = load_v1_final_check_module()

    def fake_tcp_check(endpoint: Any, timeout_seconds: float) -> Any:
        return module.ServiceProbeResult(
            name=endpoint.name,
            host=endpoint.host,
            port=endpoint.port,
            status="down",
            detail="fake down",
        )

    monkeypatch.setattr(module, "tcp_check", fake_tcp_check)

    exit_code = module.main([])

    assert exit_code == 0


def test_main_require_full_exits_nonzero_when_service_is_down(monkeypatch: Any) -> None:
    """--require-full 应把外部 full 服务不可达视为失败。"""
    module = load_v1_final_check_module()

    def fake_tcp_check(endpoint: Any, timeout_seconds: float) -> Any:
        return module.ServiceProbeResult(
            name=endpoint.name,
            host=endpoint.host,
            port=endpoint.port,
            status="down",
            detail="fake down",
        )

    monkeypatch.setattr(module, "tcp_check", fake_tcp_check)

    exit_code = module.main(["--require-full"])

    assert exit_code == 1
