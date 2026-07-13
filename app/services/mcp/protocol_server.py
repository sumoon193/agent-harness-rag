"""MCP 2025-11-25 本地 Streamable HTTP 协议内核。"""
from __future__ import annotations

from typing import Any

from app.schemas.protocol import JsonRpcRequest, JsonRpcResponse
from app.schemas.user import UserContext
from app.services.mcp.adapter import McpToolAdapter

MCP_PROTOCOL_VERSION = "2025-11-25"


class LocalMcpProtocolServer:
    """暴露 tools/resources/prompts，工具执行仍交给 Harness。"""

    def __init__(
        self,
        *,
        tool_adapter: McpToolAdapter,
        resources: dict[str, dict[str, Any]],
        prompts: dict[str, str],
    ) -> None:
        self._tool_adapter = tool_adapter
        self._resources = resources
        self._prompts = prompts

    async def handle(
        self,
        request: JsonRpcRequest,
        *,
        run_id: str,
        user_context: UserContext,
    ) -> JsonRpcResponse:
        """处理单个 MCP JSON-RPC 请求。"""
        if request.method == "initialize":
            return self._result(
                request,
                {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "serverInfo": {"name": "EnterpriseMind MCP", "version": "1.0.0"},
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False},
                    },
                },
            )
        if request.method == "tools/list":
            return self._result(
                request,
                {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.parameters_schema,
                            "annotations": {
                                "readOnlyHint": not tool.requires_approval,
                                "destructiveHint": tool.requires_approval,
                                "idempotentHint": tool.idempotent,
                            },
                        }
                        for tool in self._tool_adapter.discover_tools()
                    ]
                },
            )
        if request.method == "tools/call":
            name = str(request.params.get("name", ""))
            arguments = request.params.get("arguments", {})
            if not isinstance(arguments, dict):
                return self._error(request, -32602, "arguments must be an object")
            tool_call = await self._tool_adapter.call(
                run_id=run_id,
                tool_name=name,
                parameters=arguments,
                user_context=user_context,
            )
            return self._result(
                request,
                {
                    "content": [],
                    "structuredContent": {
                        "toolCallId": tool_call.id,
                        "status": tool_call.status.value,
                        "approvalRequired": tool_call.approval_required,
                        "result": tool_call.result,
                    },
                    "isError": tool_call.status.value == "failed",
                },
            )
        if request.method == "resources/list":
            return self._result(
                request,
                {
                    "resources": [
                        {
                            "uri": uri,
                            "name": value["name"],
                            "mimeType": value.get("mimeType", "text/plain"),
                        }
                        for uri, value in self._resources.items()
                    ]
                },
            )
        if request.method == "resources/read":
            uri = str(request.params.get("uri", ""))
            resource = self._resources.get(uri)
            if resource is None:
                return self._error(request, -32002, f"resource not found: {uri}")
            return self._result(
                request,
                {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": resource.get("mimeType", "text/plain"),
                            "text": resource.get("text", ""),
                        }
                    ]
                },
            )
        if request.method == "prompts/list":
            return self._result(
                request,
                {
                    "prompts": [
                        {"name": name, "description": text[:120]}
                        for name, text in self._prompts.items()
                    ]
                },
            )
        if request.method == "prompts/get":
            name = str(request.params.get("name", ""))
            prompt = self._prompts.get(name)
            if prompt is None:
                return self._error(request, -32003, f"prompt not found: {name}")
            return self._result(
                request,
                {"description": prompt[:120], "messages": [{"role": "user", "content": {"type": "text", "text": prompt}}]},
            )
        return self._error(request, -32601, f"method not found: {request.method}")

    @staticmethod
    def _result(request: JsonRpcRequest, result: dict[str, Any]) -> JsonRpcResponse:
        return JsonRpcResponse(id=request.id, result=result)

    @staticmethod
    def _error(request: JsonRpcRequest, code: int, message: str) -> JsonRpcResponse:
        return JsonRpcResponse(id=request.id, error={"code": code, "message": message})
