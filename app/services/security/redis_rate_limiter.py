"""
Redis 速率限制器。

替代基于 dict 的内存速率限制器，使用 Redis 有序集合实现滑动窗口。
"""
from __future__ import annotations

import logging
import time

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Redis 速率限制器。

    使用有序集合（ZSET）实现滑动窗口算法。
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        logger.info(
            "redis_rate_limiter_init",
            extra={"max_requests": max_requests, "window_seconds": window_seconds},
        )

    def _key(self, user_id: str, action: str) -> str:
        return f"rate_limit:{user_id}:{action}"

    async def check(self, user_id: str, action: str = "default") -> bool:
        key = self._key(user_id, action)
        now = time.time()
        window_start = now - self._window_seconds

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, self._window_seconds)
        results = await pipe.execute()

        current_count = results[1]  # zcard 结果

        if current_count >= self._max_requests:
            # 超限，移除刚添加的记录
            await self._redis.zrem(key, str(now))
            logger.warning(
                "rate_limit_exceeded",
                extra={"user_id": user_id, "action": action, "count": current_count},
            )
            return False

        return True

    async def get_remaining(self, user_id: str, action: str = "default") -> int:
        key = self._key(user_id, action)
        now = time.time()
        window_start = now - self._window_seconds

        await self._redis.zremrangebyscore(key, 0, window_start)
        count = await self._redis.zcard(key)
        return max(0, self._max_requests - count)

    async def reset(self, user_id: str, action: str = "default") -> None:
        key = self._key(user_id, action)
        await self._redis.delete(key)

    async def close(self) -> None:
        """关闭 Redis 连接。"""
        close = getattr(self._redis, "aclose", None)
        if close is None:
            close = self._redis.close
        await close()
