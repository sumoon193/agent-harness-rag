"""
速率限制器。

限制用户操作频率，防止滥用。
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    速率限制器。

    使用滑动窗口算法限制用户操作频率。
    """

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60
    ) -> None:
        """
        初始化速率限制器。

        Args:
            max_requests: 窗口内最大请求数
            window_seconds: 窗口大小（秒）
        """
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, user_id: str, action: str = "default") -> bool:
        """
        检查是否超过速率限制。

        Args:
            user_id: 用户 ID
            action: 操作类型

        Returns:
            是否允许（True = 允许，False = 超限）
        """
        key = f"{user_id}:{action}"
        now = time.time()

        # 清理过期记录
        self._requests[key] = [
            t for t in self._requests[key]
            if now - t < self._window_seconds
        ]

        # 检查是否超限
        if len(self._requests[key]) >= self._max_requests:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "user_id": user_id,
                    "action": action,
                    "current_count": len(self._requests[key]),
                    "max_requests": self._max_requests
                }
            )
            return False

        # 记录请求
        self._requests[key].append(now)

        return True

    def get_remaining(self, user_id: str, action: str = "default") -> int:
        """
        获取剩余请求次数。

        Args:
            user_id: 用户 ID
            action: 操作类型

        Returns:
            剩余次数
        """
        key = f"{user_id}:{action}"
        now = time.time()

        # 清理过期记录
        self._requests[key] = [
            t for t in self._requests[key]
            if now - t < self._window_seconds
        ]

        return max(0, self._max_requests - len(self._requests[key]))

    def reset(self, user_id: str, action: str = "default") -> None:
        """
        重置用户的速率限制。

        Args:
            user_id: 用户 ID
            action: 操作类型
        """
        key = f"{user_id}:{action}"
        if key in self._requests:
            del self._requests[key]
