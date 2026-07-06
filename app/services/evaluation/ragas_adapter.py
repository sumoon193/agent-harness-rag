"""
RAGAS 评测适配器。

V1 阶段使用确定性 fake 实现，计算简化的 RAG 指标。
真实版本后续替换为 RAGAS 库调用。
"""
from __future__ import annotations

import logging
import re
from typing import Protocol

logger = logging.getLogger(__name__)


class RAGASMetrics(Protocol):
    """
    RAGAS 指标计算协议。

    后续替换为真实 RAGAS 库。
    """

    def compute(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str,
    ) -> dict[str, float]:
        """
        计算 RAG 指标。

        Args:
            question: 用户问题
            answer: 生成的答案
            contexts: 检索到的上下文列表
            ground_truth: 标准答案

        Returns:
            指标字典：context_precision, context_recall, faithfulness, answer_relevancy
        """
        ...


def _keyword_overlap(text_a: str, text_b: str) -> float:
    """计算两段文本的关键词重叠率（简化版）。"""
    def _keywords(text: str) -> set[str]:
        cleaned = re.sub(r'[\s，。、；：“”‘’【】《》（）！？.,;:!?\(\)\[\]\{\}]', ' ', text)
        words: set[str] = set()
        for w in re.findall(r'[a-zA-Z]{2,}', cleaned):
            words.add(w.lower())
        for seg in re.findall(r'[一-鿿]+', cleaned):
            for i in range(max(len(seg) - 1, 0)):
                words.add(seg[i:i + 2])
            if len(seg) == 1:
                words.add(seg)
        return words

    kw_a = _keywords(text_a)
    kw_b = _keywords(text_b)
    if not kw_a or not kw_b:
        return 0.0
    return len(kw_a & kw_b) / min(len(kw_a), len(kw_b))


class FakeRAGASMetrics:
    """
    确定性 fake RAGAS 指标计算。

    基于关键词重叠率近似 RAGAS 指标，用于 V1 单元测试和本地开发。
    """

    def compute(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str,
    ) -> dict[str, float]:
        """
        计算简化 RAG 指标。

        Args:
            question: 用户问题
            answer: 生成的答案
            contexts: 检索到的上下文列表
            ground_truth: 标准答案

        Returns:
            指标字典
        """
        # context_precision: 上下文与问题的相关性
        context_scores = [_keyword_overlap(ctx, question) for ctx in contexts]
        context_precision = sum(context_scores) / len(context_scores) if context_scores else 0.0

        # context_recall: 上下文对标准答案的覆盖度
        all_context = ' '.join(contexts)
        context_recall = _keyword_overlap(all_context, ground_truth)

        # faithfulness: 答案是否忠实于上下文
        faithfulness = _keyword_overlap(answer, all_context)

        # answer_relevancy: 答案与问题的相关性
        answer_relevancy = _keyword_overlap(answer, question)

        metrics = {
            "context_precision": round(min(context_precision, 1.0), 3),
            "context_recall": round(min(context_recall, 1.0), 3),
            "faithfulness": round(min(faithfulness, 1.0), 3),
            "answer_relevancy": round(min(answer_relevancy, 1.0), 3),
        }

        logger.debug("ragas_metrics_computed", extra=metrics)
        return metrics


class RealRAGASMetrics:
    """
    基于 ragas 库的真实 RAGAS 指标计算。

    需要安装 ragas。不可用时自动降级到 FakeRAGASMetrics。
    """

    def __init__(self, llm_model: str = "qwen-plus", api_key: str = "") -> None:
        self._llm_model = llm_model
        self._api_key = api_key
        self._fallback = FakeRAGASMetrics()

    def compute(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str,
    ) -> dict[str, float]:
        """使用 ragas 库计算 RAG 指标，不可用时降级。"""
        try:
            return self._compute_ragas(question, answer, contexts, ground_truth)
        except ImportError:
            logger.warning("ragas_not_installed_falling_back")
            return self._fallback.compute(question, answer, contexts, ground_truth)
        except Exception as e:
            logger.error("ragas_compute_failed", extra={"error": str(e)})
            return self._fallback.compute(question, answer, contexts, ground_truth)

    def _compute_ragas(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str,
    ) -> dict[str, float]:
        """调用 ragas 库核心逻辑。"""
        from ragas import evaluate
        from ragas.dataset_schema import SingleTurnSample
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )

        sample = SingleTurnSample(
            user_input=question,
            response=answer,
            retrieved_contexts=contexts,
            reference=ground_truth,
        )

        result = evaluate(
            dataset=[sample],
            metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
        )

        scores = result.scores[0] if result.scores else {}
        return {
            "context_precision": round(float(scores.get("context_precision", 0.0)), 3),
            "context_recall": round(float(scores.get("context_recall", 0.0)), 3),
            "faithfulness": round(float(scores.get("faithfulness", 0.0)), 3),
            "answer_relevancy": round(float(scores.get("answer_relevancy", 0.0)), 3),
        }
