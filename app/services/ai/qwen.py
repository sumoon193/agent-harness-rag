"""Qwen / DashScope 真实 AI adapter。"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

from app.core.exceptions import ExternalServiceError, ValidationError
from app.schemas.retrieval import RetrievalResult

logger = logging.getLogger(__name__)

PostJson = Callable[[str, dict[str, str], dict[str, Any], float], Awaitable[dict[str, Any]]]

DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_QWEN_RERANK_BASE_URL = "https://dashscope.aliyuncs.com/compatible-api/v1"


class QwenAnswerGenerator:
    """基于 Qwen OpenAI-compatible Chat Completions 的答案生成器。"""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = DEFAULT_QWEN_BASE_URL,
        timeout_seconds: float = 30.0,
        temperature: float = 0.2,
        post_json: PostJson | None = None,
    ) -> None:
        self._api_key = _require_api_key(api_key)
        self._model = model
        self._base_url = _trim_url(base_url)
        self._timeout_seconds = timeout_seconds
        self._temperature = temperature
        self._post_json = post_json or _post_json

    async def generate(self, prompt: str) -> str:
        """调用 Qwen Chat Completions 生成答案文本。"""
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
        }
        data = await self._post_json(
            f"{self._base_url}/chat/completions",
            _auth_headers(self._api_key),
            payload,
            self._timeout_seconds,
        )

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ExternalServiceError("Qwen chat response format is invalid") from exc

        if not isinstance(content, str) or not content.strip():
            raise ExternalServiceError("Qwen chat response content is empty")
        return content.strip()


class QwenEmbedder:
    """基于 Qwen OpenAI-compatible Embeddings 的 Embedder。"""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimension: int,
        base_url: str = DEFAULT_QWEN_BASE_URL,
        timeout_seconds: float = 30.0,
        post_json: PostJson | None = None,
    ) -> None:
        self._api_key = _require_api_key(api_key)
        self._model = model
        self.dimension = dimension
        self._base_url = _trim_url(base_url)
        self._timeout_seconds = timeout_seconds
        self._post_json = post_json or _post_json

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量向量化文档文本。"""
        if not texts:
            return []

        payload = {
            "model": self._model,
            "input": texts,
            "dimensions": self.dimension,
            "encoding_format": "float",
        }
        data = await self._post_json(
            f"{self._base_url}/embeddings",
            _auth_headers(self._api_key),
            payload,
            self._timeout_seconds,
        )
        return self._parse_embeddings(data, expected_count=len(texts))

    async def embed_query(self, query: str) -> list[float]:
        """向量化单条查询。"""
        embeddings = await self.embed_documents([query])
        return embeddings[0]

    def _parse_embeddings(self, data: dict[str, Any], expected_count: int) -> list[list[float]]:
        raw_items = data.get("data")
        if not isinstance(raw_items, list) or len(raw_items) != expected_count:
            raise ExternalServiceError("Qwen embedding response count is invalid")

        ordered_items = sorted(
            raw_items,
            key=lambda item: item.get("index", 0) if isinstance(item, dict) else 0,
        )
        embeddings: list[list[float]] = []
        for item in ordered_items:
            if not isinstance(item, dict):
                raise ExternalServiceError("Qwen embedding response item is invalid")
            embedding = item.get("embedding")
            if not isinstance(embedding, list):
                raise ExternalServiceError("Qwen embedding vector is invalid")
            vector = [float(value) for value in embedding]
            if len(vector) != self.dimension:
                raise ExternalServiceError(
                    f"Qwen embedding dimension mismatch: expected {self.dimension}, got {len(vector)}"
                )
            embeddings.append(vector)

        return embeddings


class QwenReranker:
    """基于 Qwen qwen3-rerank OpenAI-compatible Reranks API 的 Reranker。"""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        rerank_base_url: str = DEFAULT_QWEN_RERANK_BASE_URL,
        timeout_seconds: float = 30.0,
        post_json: PostJson | None = None,
    ) -> None:
        self._api_key = _require_api_key(api_key)
        self._model = model
        self._rerank_base_url = _trim_url(rerank_base_url)
        self._timeout_seconds = timeout_seconds
        self._post_json = post_json or _post_json

    async def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """调用 Qwen rerank，并把 relevance_score 映射回 RetrievalResult。"""
        if not results:
            return []

        limit = min(top_k, len(results))
        payload = {
            "model": self._model,
            "query": query,
            "documents": [result.chunk_text for result in results],
            "top_n": limit,
        }
        data = await self._post_json(
            f"{self._rerank_base_url}/reranks",
            _auth_headers(self._api_key),
            payload,
            self._timeout_seconds,
        )

        raw_items = data.get("results") or data.get("output", {}).get("results")
        if not isinstance(raw_items, list):
            raise ExternalServiceError("Qwen rerank response format is invalid")

        reranked: list[RetrievalResult] = []
        for item in raw_items:
            if not isinstance(item, dict):
                raise ExternalServiceError("Qwen rerank response item is invalid")
            index = item.get("index")
            score = item.get("relevance_score")
            if not isinstance(index, int) or index < 0 or index >= len(results):
                raise ExternalServiceError("Qwen rerank response index is invalid")
            if not isinstance(score, int | float):
                raise ExternalServiceError("Qwen rerank response score is invalid")

            rerank_score = max(0.0, min(1.0, float(score)))
            reranked.append(results[index].model_copy(update={"rerank_score": rerank_score}))

        return reranked[:limit]


async def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    """发送 JSON POST 请求并统一转换外部服务错误。"""
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                text = await response.text()
                if response.status >= 400:
                    raise ExternalServiceError(
                        f"Qwen request failed: status={response.status}, body={_safe_error_body(text)}"
                    )
                try:
                    data = await response.json()
                except Exception as exc:
                    raise ExternalServiceError("Qwen response is not valid JSON") from exc
    except ExternalServiceError:
        raise
    except aiohttp.ClientError as exc:
        raise ExternalServiceError(f"Qwen request failed: {exc.__class__.__name__}") from exc

    if not isinstance(data, dict):
        raise ExternalServiceError("Qwen response JSON root is invalid")
    return data


def _auth_headers(api_key: str) -> dict[str, str]:
    """构造 Qwen/DashScope HTTP 请求头。"""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _require_api_key(api_key: str) -> str:
    """校验 API key 是否存在，避免 full mode 静默退化。"""
    key = api_key.strip()
    if not key:
        raise ValidationError("QWEN_API_KEY is required for Qwen AI adapters")
    return key


def _trim_url(url: str) -> str:
    """去掉 URL 尾部斜杠，避免拼接出双斜杠。"""
    return url.rstrip("/")


def _safe_error_body(text: str) -> str:
    """截断错误响应，避免日志或 API 错误中带出过多外部内容。"""
    return text[:500].replace("\n", " ")
