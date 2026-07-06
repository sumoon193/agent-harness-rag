"""
Fact Checker。

校验生成的答案是否被 evidence 支持。
V1 采用基于关键词重叠的简化实现，真实版本后续替换为 LLM-based check。
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.schemas.chunk import Citation

logger = logging.getLogger(__name__)

# 关键词重叠率低于此阈值视为不支持
_SUPPORT_THRESHOLD = 0.15


@dataclass
class FactCheckResult:
    """
    事实核查结果。
    """
    is_supported: bool
    unsupported_claims: list[str] = field(default_factory=list)
    supported_claims: list[str] = field(default_factory=list)
    support_ratio: float = 0.0


def _extract_keywords(text: str) -> set[str]:
    """
    从文本中提取关键词（中文 2-gram + 英文单词）。

    简化实现：去除标点后按空格/字符切分。
    """
    # 移除标点符号
    cleaned = re.sub(r'[，。、；：“”‘’【】《》（）！？\s.,;:!?\(\)\[\]\{\}]', ' ', text)
    keywords: set[str] = set()

    # 英文单词（2 字符以上）
    english_words = re.findall(r'[a-zA-Z]{2,}', cleaned)
    keywords.update(w.lower() for w in english_words)

    # 中文连续字符（取 2-gram）
    chinese_chars = re.findall(r'[一-鿿]+', cleaned)
    for segment in chinese_chars:
        if len(segment) >= 2:
            for i in range(len(segment) - 1):
                keywords.add(segment[i:i + 2])
        elif len(segment) == 1:
            keywords.add(segment)

    return keywords


def _extract_claims(answer: str) -> list[str]:
    """
    从答案中提取关键断言句。

    简化实现：按句号、分号、换行拆分。
    """
    sentences = re.split(r'[。\n；;]', answer)
    claims = [s.strip() for s in sentences if len(s.strip()) >= 4]
    return claims


class FactChecker:
    """
    事实核查器。

    检查答案中的关键断言是否在提供的 evidence 中有支撑。
    """

    def check(
        self,
        answer: str,
        citations: list[Citation],
        support_threshold: float = _SUPPORT_THRESHOLD,
    ) -> FactCheckResult:
        """
        校验答案是否被 evidence 支持。

        Args:
            answer: 生成的答案文本
            citations: 引用来源列表
            support_threshold: 支持率阈值

        Returns:
            FactCheckResult
        """
        if not citations:
            logger.info("fact_check_no_citations")
            return FactCheckResult(
                is_supported=False,
                unsupported_claims=["答案无引用来源"],
                support_ratio=0.0,
            )

        # 合并所有 evidence 关键词
        evidence_keywords: set[str] = set()
        for c in citations:
            evidence_keywords.update(_extract_keywords(c.chunk_text))

        if not evidence_keywords:
            return FactCheckResult(
                is_supported=False,
                unsupported_claims=["无法提取 evidence 关键词"],
                support_ratio=0.0,
            )

        # 提取答案断言，逐条检查
        claims = _extract_claims(answer)
        supported: list[str] = []
        unsupported: list[str] = []

        for claim in claims:
            claim_keywords = _extract_keywords(claim)
            if not claim_keywords:
                continue
            overlap = claim_keywords & evidence_keywords
            ratio = len(overlap) / len(claim_keywords)
            if ratio >= support_threshold:
                supported.append(claim)
            else:
                unsupported.append(claim)

        total = len(supported) + len(unsupported)
        support_ratio = len(supported) / total if total > 0 else 0.0

        result = FactCheckResult(
            is_supported=(len(unsupported) == 0),
            unsupported_claims=unsupported,
            supported_claims=supported,
            support_ratio=support_ratio,
        )

        logger.info(
            "fact_check_complete",
            extra={
                "supported": len(supported),
                "unsupported": len(unsupported),
                "support_ratio": round(support_ratio, 2),
            },
        )
        return result
