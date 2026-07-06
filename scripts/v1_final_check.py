"""
V1 最终收尾检查脚本。

默认用于本地 V1 closure：列出必须跑通的代码验收命令，并探测 full mode
外部服务端口。外部服务未启动会标记为 blocked，但默认不让脚本失败；
只有传入 --require-full 时，full mode 端口不可达才返回非零退出码。
"""
from __future__ import annotations

import argparse
import socket
import sys
from collections.abc import Callable, Sequence
from typing import Literal, NamedTuple

ProbeStatus = Literal["up", "down"]


class ServiceEndpoint(NamedTuple):
    """full mode 本地服务端点。"""

    name: str
    host: str
    port: int


class ServiceProbeResult(NamedTuple):
    """full mode 本地服务探测结果。"""

    name: str
    host: str
    port: int
    status: ProbeStatus
    detail: str


ProbeChecker = Callable[[ServiceEndpoint, float], ServiceProbeResult]

DEFAULT_FULL_ENDPOINTS: tuple[ServiceEndpoint, ...] = (
    ServiceEndpoint(name="PostgreSQL", host="localhost", port=5432),
    ServiceEndpoint(name="Redis", host="localhost", port=6379),
    ServiceEndpoint(name="MinIO", host="localhost", port=9000),
    ServiceEndpoint(name="Elasticsearch", host="localhost", port=9201),
    ServiceEndpoint(name="Milvus", host="localhost", port=19530),
)

V1_CODE_CHECK_COMMANDS: tuple[tuple[str, str], ...] = (
    (
        "Backend unit/service/api baseline",
        r".\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider",
    ),
    (
        "Quality gate",
        r".\.venv\Scripts\python.exe scripts\quality_gate.py",
    ),
    (
        "Python compile check",
        r".\.venv\Scripts\python.exe -m compileall -q app tests scripts",
    ),
    (
        "Frontend build",
        "cd frontend && npm run build",
    ),
    (
        "Frontend fallback E2E",
        "cd frontend && npm run test:e2e",
    ),
)

V2_NON_GOALS: tuple[str, ...] = (
    "GraphRAG / LightRAG",
    "MCP Server",
    "真实 HR 系统",
    "完整生产多租户 RBAC",
)


def tcp_check(endpoint: ServiceEndpoint, timeout_seconds: float = 0.5) -> ServiceProbeResult:
    """探测一个 TCP 端口，连接失败时返回 down。"""
    try:
        with socket.create_connection((endpoint.host, endpoint.port), timeout=timeout_seconds):
            return ServiceProbeResult(
                name=endpoint.name,
                host=endpoint.host,
                port=endpoint.port,
                status="up",
                detail="tcp reachable",
            )
    except OSError as exc:
        return ServiceProbeResult(
            name=endpoint.name,
            host=endpoint.host,
            port=endpoint.port,
            status="down",
            detail=str(exc),
        )


def run_full_preflight(
    endpoints: Sequence[ServiceEndpoint] = DEFAULT_FULL_ENDPOINTS,
    checker: ProbeChecker | None = None,
    timeout_seconds: float = 0.5,
) -> list[ServiceProbeResult]:
    """执行 full mode 外部服务预检。"""
    selected_checker = checker or tcp_check
    return [selected_checker(endpoint, timeout_seconds) for endpoint in endpoints]


def has_down_service(results: Sequence[ServiceProbeResult]) -> bool:
    """判断是否存在不可达的 full mode 服务。"""
    return any(result.status == "down" for result in results)


def print_header() -> None:
    """打印脚本标题。"""
    print("=" * 72)
    print("EnterpriseMind V1 Final Check")
    print("=" * 72)


def print_v1_scope() -> None:
    """打印 V1 收尾范围。"""
    print("\n[V1 scope]")
    print("- V1 closure focuses on fallback demo, full-mode adapters, AI/Celery links, trace, tests.")
    print("- V2 is intentionally frozen for this pass.")
    print("- V2 non-goals:")
    for item in V2_NON_GOALS:
        print(f"  - {item}")


def print_code_checklist() -> None:
    """打印 V1 代码验收命令。"""
    print("\n[V1 code checks]")
    print("Run these commands for code-level acceptance:")
    for label, command in V1_CODE_CHECK_COMMANDS:
        print(f"- {label}: {command}")


def print_full_preflight_report(
    results: Sequence[ServiceProbeResult],
    require_full: bool,
) -> None:
    """打印 full mode 预检报告。"""
    print("\n[Full-mode external service preflight]")
    for result in results:
        status = "OK" if result.status == "up" else "BLOCKED"
        endpoint = f"{result.host}:{result.port}"
        print(f"- [{status}] {result.name} {endpoint} - {result.detail}")

    if has_down_service(results):
        if require_full:
            print("\nFull mode is required, and at least one external service is down.")
        else:
            print(
                "\nExternal services are blocked/down. This does not fail default V1 closure; "
                "start them before full-mode integration or full E2E validation."
            )
    else:
        print("\nAll full-mode external service ports are reachable.")


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="EnterpriseMind V1 final closure helper.")
    parser.add_argument(
        "--require-full",
        action="store_true",
        help="Treat unavailable full-mode external services as a failed check.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=0.5,
        help="TCP probe timeout per service. Default: 0.5",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """脚本入口，返回进程退出码。"""
    args = build_parser().parse_args(argv)

    print_header()
    print_v1_scope()
    print_code_checklist()

    results = run_full_preflight(timeout_seconds=args.timeout_seconds)
    print_full_preflight_report(results=results, require_full=args.require_full)

    if args.require_full and has_down_service(results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
