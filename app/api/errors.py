"""
统一错误响应格式与异常处理器。

所有 API 错误返回统一 shape，不暴露内部异常堆栈。
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.exceptions import (
    AppError,
    NotFoundError,
    PermissionError,
    ValidationError,
)

logger = logging.getLogger(__name__)


# ── 统一错误响应 Schema ──────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """错误详情。"""
    code: str = Field(description="错误码")
    message: str = Field(description="用户可读错误信息")
    request_id: str = Field(description="请求 ID，用于链路追踪")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="附加信息"
    )


class ErrorResponse(BaseModel):
    """统一错误响应。"""
    error: ErrorDetail


# ── 异常 → HTTP 状态码映射 ────────────────────────────────────────────

_EXCEPTION_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: 404,
    PermissionError: 403,
    ValidationError: 422,
}


def build_error_response(
    code: str,
    message: str,
    request_id: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """构建统一 JSON 错误响应。"""
    body = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id,
            details=details or {},
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


# ── FastAPI 异常处理器 ────────────────────────────────────────────────

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """捕获 AppError 子类，返回统一错误格式。"""
    request_id = getattr(request.state, "request_id", uuid.uuid4().hex[:12])
    status_code = _EXCEPTION_STATUS_MAP.get(type(exc), 500)

    # 映射异常类型 → 错误码
    error_code_map: dict[type, str] = {
        NotFoundError: "not_found",
        PermissionError: "permission_denied",
        ValidationError: "validation_error",
    }
    code = error_code_map.get(type(exc), "internal_error")

    logger.warning(
        "api_error",
        extra={
            "error_code": code,
            "error_message": str(exc),
            "status": status_code,
            "request_id": request_id,
            "path": request.url.path,
        },
    )

    return build_error_response(
        code=code,
        message=str(exc),
        request_id=request_id,
        status_code=status_code,
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底处理器：捕获未预期异常，不暴露堆栈。"""
    request_id = getattr(request.state, "request_id", uuid.uuid4().hex[:12])

    logger.exception(
        "unhandled_error",
        extra={"request_id": request_id, "path": request.url.path},
    )

    return build_error_response(
        code="internal_error",
        message="服务器内部错误，请稍后重试",
        request_id=request_id,
        status_code=500,
    )
