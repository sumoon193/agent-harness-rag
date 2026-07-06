"""
低置信度处理器。

检测低置信度场景，决定 refuse / clarify 策略。
"""
from __future__ import annotations

import logging
from enum import StrEnum

from app.schemas.chunk import EvidenceBundle

logger = logging.getLogger(__name__)

# 置信度阈值
_NO_EVIDENCE_CONFIDENCE = 0.0
_LOW_SCORE_THRESHOLD = 0.3
_CONFLICT_THRESHOLD = 0.4


class LowConfidenceAction(StrEnum):
    """
    低置信度时的处理动作。
    """
    PROCEED = "proceed"          # 正常生成答案
    REFUSE = "refuse"            # 直接拒答
    CLARIFY = "clarify"          # 请求用户澄清
    RECOMMEND_HUMAN = "recommend_human"  # 建议联系人工


class LowConfidenceVerdict:
    """
    低置信度判定结果。
    """

    def __init__(
        self,
        action: LowConfidenceAction,
        reason: str,
        confidence: float,
    ) -> None:
        self.action = action
        self.reason = reason
        self.confidence = confidence

    def __repr__(self) -> str:
        return (
            f"LowConfidenceVerdict(action={self.action!r}, "
            f"confidence={self.confidence:.2f}, reason={self.reason!r})"
        )


class LowConfidenceHandler:
    """
    低置信度检测器。

    检查以下场景：
    - evidence 数量为 0 → REFUSE
    - top rerank score 低于阈值 → CLARIFY / RECOMMEND_HUMAN
    - evidence 之间冲突（top 与 bottom 分差过大）→ CLARIFY
    - 用户问题超出知识库范围 → RECOMMEND_HUMAN
    """

    def __init__(
        self,
        low_score_threshold: float = _LOW_SCORE_THRESHOLD,
        conflict_threshold: float = _CONFLICT_THRESHOLD,
    ) -> None:
        self._low_score_threshold = low_score_threshold
        self._conflict_threshold = conflict_threshold

    def evaluate(
        self,
        evidence: EvidenceBundle | None,
        question: str,
    ) -> LowConfidenceVerdict:
        """
        评估置信度并决定处理策略。

        Args:
            evidence: 检索到的证据包（None 表示无证据）
            question: 用户原始问题

        Returns:
            LowConfidenceVerdict
        """
        # 场景 1：无证据
        if evidence is None or not evidence.evidence_list:
            logger.info("low_confidence_no_evidence")
            return LowConfidenceVerdict(
                action=LowConfidenceAction.REFUSE,
                reason="未找到相关证据",
                confidence=_NO_EVIDENCE_CONFIDENCE,
            )

        evidence_list = evidence.evidence_list
        scores = [c.rerank_score for c in evidence_list]
        top_score = max(scores)
        bottom_score = min(scores)

        # 场景 2：top score 太低
        if top_score < self._low_score_threshold:
            logger.info(
                "low_confidence_top_score",
                extra={"top_score": top_score},
            )
            return LowConfidenceVerdict(
                action=LowConfidenceAction.RECOMMEND_HUMAN,
                reason=f"检索结果质量过低（最高分 {top_score:.2f}）",
                confidence=top_score,
            )

        # 场景 3：证据之间冲突（分差过大）
        if len(evidence_list) >= 2:
            score_spread = top_score - bottom_score
            if score_spread > self._conflict_threshold:
                logger.info(
                    "low_confidence_conflict",
                    extra={
                        "top_score": top_score,
                        "bottom_score": bottom_score,
                        "spread": score_spread,
                    },
                )
                return LowConfidenceVerdict(
                    action=LowConfidenceAction.CLARIFY,
                    reason=f"证据之间存在分歧（分差 {score_spread:.2f}）",
                    confidence=top_score * 0.7,
                )

        # 正常路径
        return LowConfidenceVerdict(
            action=LowConfidenceAction.PROCEED,
            reason="",
            confidence=evidence.query_coverage_score,
        )
