"""
Prompt Injection 防护。

检测并拦截 Prompt Injection 攻击。
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


class PromptGuard:
    """
    Prompt Injection 防护器。

    检测常见的 Prompt Injection 模式。
    """

    # 常见的 Prompt Injection 模式
    INJECTION_PATTERNS: list[tuple[str, str]] = [
        # 直接指令注入
        (r"ignore\s+(previous|above|all)\s+(instructions?|prompts?)", "Direct instruction override"),
        (r"disregard\s+(previous|above|all)\s+(instructions?|prompts?)", "Direct instruction override"),
        (r"forget\s+(previous|above|all)\s+(instructions?|prompts?)", "Direct instruction override"),

        # 角色注入
        (r"you\s+are\s+now\s+", "Role injection"),
        (r"act\s+as\s+", "Role injection"),
        (r"pretend\s+(you\s+are|to\s+be)\s+", "Role injection"),
        (r"system\s*:\s*", "System prompt injection"),

        # 输出控制
        (r"output\s+(only|just)\s+", "Output control"),
        (r"respond\s+(only|just)\s+with\s+", "Output control"),
        (r"do\s+not\s+(include|mention|say)\s+", "Output restriction"),

        # 提示泄露
        (r"(show|reveal|display|print)\s+(your|the)\s+(system\s+)?(prompt|instructions?)", "Prompt leakage attempt"),
        (r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?)", "Prompt leakage attempt"),
        (r"repeat\s+(the\s+)?(system\s+)?(prompt|instructions?)", "Prompt leakage attempt"),

        # 编码绕过
        (r"(base64|hex|rot13|url)\s*(encode|decode)", "Encoding bypass attempt"),
        (r"\\x[0-9a-fA-F]{2}", "Hex encoding detected"),
        (r"&#\d+;", "HTML entity encoding detected"),

        # 特殊标记
        (r"\[INST\]", "Special tag injection"),
        (r"\[/INST\]", "Special tag injection"),
        (r"<\|im_start\|>", "Special tag injection"),
        (r"<\|im_end\|>", "Special tag injection"),
        (r"###\s*(System|Human|Assistant)\s*:", "Role tag injection"),
    ]

    def __init__(self, min_confidence: float = 0.7) -> None:
        """
        初始化 Prompt Guard。

        Args:
            min_confidence: 最小置信度阈值
        """
        self._min_confidence = min_confidence

    def detect_injection(self, text: str) -> tuple[bool, str]:
        """
        检测 Prompt Injection。

        Args:
            text: 输入文本

        Returns:
            (is_injection, reason)
        """
        text_lower = text.lower()

        for pattern, reason in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(
                    "prompt_injection_detected",
                    extra={"reason": reason, "text_preview": text[:100]}
                )
                return True, reason

        return False, ""

    def sanitize_input(self, text: str) -> str:
        """
        清理输入文本。

        移除或转义潜在的危险内容。

        Args:
            text: 输入文本

        Returns:
            清理后的文本
        """
        # 移除特殊标记
        sanitized = text
        for pattern, _ in self.INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[FILTERED]", sanitized, flags=re.IGNORECASE)

        return sanitized

    def check_and_sanitize(self, text: str) -> tuple[bool, str, str]:
        """
        检测并清理输入。

        Args:
            text: 输入文本

        Returns:
            (is_injection, reason, sanitized_text)
        """
        is_injection, reason = self.detect_injection(text)
        sanitized = self.sanitize_input(text) if is_injection else text

        return is_injection, reason, sanitized
