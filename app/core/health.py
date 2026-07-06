"""
基础设施健康检查。

fallback mode 不访问真实服务；full mode 只做轻量探测，连接失败以 down 返回。
"""
from __future__ import annotations

import socket
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from app.config import Settings

INFRA_SERVICES = (
    "postgres",
    "redis",
    "milvus",
    "elasticsearch",
    "minio",
)


def check_infrastructure_health(settings: Settings) -> dict[str, dict[str, Any]]:
    """根据当前模式返回基础设施健康状态。"""
    if settings.app_mode == "fallback":
        return {
            service: {"status": "skipped"}
            for service in INFRA_SERVICES
        }

    timeout = settings.health_probe_timeout_seconds
    return {
        "postgres": _check_tcp_from_url(settings.postgres_url, 5432, timeout),
        "redis": _check_tcp_from_url(settings.redis_url, 6379, timeout),
        "milvus": _check_tcp(settings.milvus_host, settings.milvus_port, timeout),
        "elasticsearch": _check_http(f"{settings.es_url.rstrip('/')}/_cluster/health", timeout),
        "minio": _check_http(f"{settings.minio_endpoint.rstrip('/')}/minio/health/live", timeout),
    }


def _check_tcp_from_url(url: str, default_port: int, timeout: float) -> dict[str, Any]:
    """从 URL 解析 host/port 并做 TCP 探测。"""
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or default_port
    return _check_tcp(host, port, timeout)


def _check_tcp(host: str, port: int, timeout: float) -> dict[str, Any]:
    """TCP 端口探测。"""
    started = perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError as exc:
        return _down(started, str(exc))
    return _up(started)


def _check_http(url: str, timeout: float) -> dict[str, Any]:
    """HTTP 探测；401/403 也说明服务已响应。"""
    started = perf_counter()
    try:
        with urlopen(url, timeout=timeout) as response:  # noqa: S310
            status_code = response.status
    except HTTPError as exc:
        status_code = exc.code
    except URLError as exc:
        return _down(started, str(exc.reason))
    except OSError as exc:
        return _down(started, str(exc))

    return {**_up(started), "status_code": status_code}


def _up(started: float) -> dict[str, Any]:
    """构造 up 状态。"""
    return {
        "status": "up",
        "latency_ms": round((perf_counter() - started) * 1000, 2),
    }


def _down(started: float, error: str) -> dict[str, Any]:
    """构造 down 状态。"""
    return {
        "status": "down",
        "latency_ms": round((perf_counter() - started) * 1000, 2),
        "error": error,
    }
