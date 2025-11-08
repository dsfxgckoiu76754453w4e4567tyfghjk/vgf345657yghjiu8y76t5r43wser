"""Langfuse evaluation and scoring service for LLM quality assessment."""

from typing import Any, Optional, Literal
from uuid import UUID

from app.core.config import settings
from app.core.logging import get_logger
from app.core.langfuse_client import score_trace, score_observation

logger = get_logger(__name__)


class EvaluationService:
    """
    Service for evaluating LLM responses using various methods.

    Supports:
    - User feedback scoring
    - LLM-as-a-judge evaluation
    - Custom evaluation metrics
    - Langfuse score tracking
    """

    def __init__(self):
        """Initialize evaluation service."""
        self.langfuse_enabled = settings.langfuse_enabled
        logger.info("evaluation_service_initialized", langfuse_enabled=self.langfuse_enabled)

    async def evaluate_response_quality(
        self,
        response: str,
        question: str,
        reference_answer: Optional[str] = None,
        context: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Evaluate response quality using multiple metrics.

        Args:
            response: The LLM response to evaluate
            question: The original question
            reference_answer: Optional reference answer for comparison
            context: Optional context used to generate the response
            trace_id: Optional Langfuse trace ID to attach scores

        Returns:
            Dictionary with evaluation scores and details
        """
        scores = {}

        # 1. Length-based heuristics
        scores["length_score"] = self._evaluate_length(response)

        # 2. Citation quality (for RAG responses)
        if context:
            scores["citation_score"] = self._evaluate_citations(response, context)

        # 3. Coherence score (simple heuristic)
        scores["coherence_score"] = self._evaluate_coherence(response)

        # 4. Relevance score (keyword matching)
        scores["relevance_score"] = self._evaluate_relevance(response, question)

        # 5. Reference comparison (if available)
        if reference_answer:
            scores["similarity_score"] = self._evaluate_similarity(response, reference_answer)

        # Calculate overall quality score (weighted average)
        weights = {
            "length_score": 0.15,
            "coherence_score": 0.25,
            "relevance_score": 0.30,
            "citation_score": 0.20 if context else 0,
            "similarity_score": 0.30 if reference_answer else 0,
        }

        # Normalize weights
        total_weight = sum(weights.values())
        normalized_weights = {k: v / total_weight for k, v in weights.items() if v > 0}

        overall_score = sum(
            scores.get(metric, 0) * weight
            for metric, weight in normalized_weights.items()
        )

        scores["overall_quality"] = round(overall_score, 2)

        # Send to Langfuse if trace_id provided
        if trace_id and self.langfuse_enabled:
            try:
                score_trace(
                    trace_id=trace_id,
                    name="response-quality",
                    value=scores["overall_quality"],
                    comment=f"Automated quality evaluation. Metrics: {scores}",
                )
                logger.info(
                    "quality_score_sent_to_langfuse",
                    trace_id=trace_id,
                    score=scores["overall_quality"],
                )
            except Exception as e:
                logger.error(
                    "failed_to_send_quality_score",
                    trace_id=trace_id,
                    error=str(e),
                )

        return scores

    def _evaluate_length(self, response: str) -> float:
        """
        Evaluate response length (too short = bad, extremely long = potentially bad).

        Returns score 0.0-1.0
        """
        length = len(response)

        if length < 20:
            return 0.3  # Too short
        elif length < 50:
            return 0.6  # Short but acceptable
        elif length < 2000:
            return 1.0  # Good length
        elif length < 5000:
            return 0.9  # Long but acceptable
        else:
            return 0.7  # Very long, might be verbose

    def _evaluate_citations(self, response: str, context: str) -> float:
        """
        Evaluate if response properly cites the context.

        Returns score 0.0-1.0
        """
        # Simple heuristic: check for common citation patterns
        citation_patterns = [
            "according to",
            "based on",
            "as mentioned",
            "as stated",
            "source:",
            "[",
            "]",
        ]

        citations_found = sum(1 for pattern in citation_patterns if pattern.lower() in response.lower())

        if citations_found >= 2:
            return 1.0
        elif citations_found == 1:
            return 0.7
        else:
            return 0.4

    def _evaluate_coherence(self, response: str) -> float:
        """
        Evaluate response coherence using simple heuristics.

        Returns score 0.0-1.0
        """
        # Check for complete sentences
        sentences = response.split(".")
        complete_sentences = len([s for s in sentences if len(s.strip()) > 10])

        if complete_sentences < 1:
            return 0.4
        elif complete_sentences < 3:
            return 0.7
        else:
            return 1.0

    def _evaluate_relevance(self, response: str, question: str) -> float:
        """
        Evaluate response relevance to question using keyword matching.

        Returns score 0.0-1.0
        """
        # Extract keywords from question (simple approach)
        question_words = set(
            word.lower().strip("?!.,")
            for word in question.split()
            if len(word) > 3  # Ignore short words
        )

        # Count how many question keywords appear in response
        response_lower = response.lower()
        keywords_found = sum(1 for word in question_words if word in response_lower)

        if not question_words:
            return 1.0  # No keywords to match

        relevance = keywords_found / len(question_words)
        return min(relevance, 1.0)

    def _evaluate_similarity(self, response: str, reference: str) -> float:
        """
        Evaluate similarity between response and reference answer.

        Uses simple Jaccard similarity (can be upgraded to embeddings).

        Returns score 0.0-1.0
        """
        # Tokenize both texts
        response_tokens = set(response.lower().split())
        reference_tokens = set(reference.lower().split())

        # Calculate Jaccard similarity
        intersection = response_tokens.intersection(reference_tokens)
        union = response_tokens.union(reference_tokens)

        if not union:
            return 0.0

        similarity = len(intersection) / len(union)
        return min(similarity * 2, 1.0)  # Scale up and cap at 1.0

    async def evaluate_hallucination(
        self,
        response: str,
        context: str,
        trace_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Detect potential hallucinations in RAG responses.

        Args:
            response: The LLM response
            context: The RAG context used
            trace_id: Optional Langfuse trace ID

        Returns:
            Hallucination detection results
        """
        # Simple heuristic: check if response contains information not in context
        response_words = set(response.lower().split())
        context_words = set(context.lower().split())

        # Calculate how many response words are NOT in context
        unsupported_words = response_words - context_words

        # Calculate hallucination risk
        total_words = len(response_words)
        unsupported_ratio = len(unsupported_words) / total_words if total_words > 0 else 0

        hallucination_score = 1.0 - min(unsupported_ratio * 2, 1.0)  # Invert and cap

        result = {
            "hallucination_score": round(hallucination_score, 2),
            "grounded_in_context": hallucination_score > 0.7,
            "unsupported_ratio": round(unsupported_ratio, 2),
        }

        # Send to Langfuse
        if trace_id and self.langfuse_enabled:
            try:
                score_trace(
                    trace_id=trace_id,
                    name="hallucination-check",
                    value=hallucination_score,
                    comment=f"Hallucination detection. Grounded: {result['grounded_in_context']}",
                )
            except Exception as e:
                logger.error(
                    "failed_to_send_hallucination_score",
                    trace_id=trace_id,
                    error=str(e),
                )

        return result

    async def evaluate_toxicity(
        self,
        text: str,
        trace_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Evaluate text for potential toxicity/inappropriate content.

        Args:
            text: Text to evaluate
            trace_id: Optional Langfuse trace ID

        Returns:
            Toxicity evaluation results
        """
        # Simple keyword-based toxicity detection
        # In production, use a proper toxicity detection model
        toxic_keywords = [
            "hate", "violence", "offensive", "inappropriate",
            # Add more as needed
        ]

        text_lower = text.lower()
        toxic_found = sum(1 for keyword in toxic_keywords if keyword in text_lower)

        toxicity_score = 1.0 - min(toxic_found * 0.3, 1.0)  # Invert score

        result = {
            "toxicity_score": round(toxicity_score, 2),
            "is_safe": toxicity_score > 0.8,
            "toxic_keywords_found": toxic_found,
        }

        # Send to Langfuse
        if trace_id and self.langfuse_enabled:
            try:
                score_trace(
                    trace_id=trace_id,
                    name="toxicity-check",
                    value=toxicity_score,
                    comment=f"Toxicity check. Safe: {result['is_safe']}",
                )
            except Exception as e:
                logger.error(
                    "failed_to_send_toxicity_score",
                    trace_id=trace_id,
                    error=str(e),
                )

        return result

    async def score_custom_metric(
        self,
        trace_id: str,
        metric_name: str,
        value: float,
        comment: Optional[str] = None,
        data_type: Literal["NUMERIC", "CATEGORICAL", "BOOLEAN"] = "NUMERIC",
    ) -> bool:
        """
        Send a custom metric score to Langfuse.

        Args:
            trace_id: Langfuse trace ID
            metric_name: Name of the metric
            value: Metric value
            comment: Optional comment
            data_type: Type of score

        Returns:
            Success status
        """
        if not self.langfuse_enabled:
            logger.debug("langfuse_disabled_skipping_custom_metric")
            return False

        try:
            score_trace(
                trace_id=trace_id,
                name=metric_name,
                value=value,
                comment=comment,
                data_type=data_type,
            )
            logger.info(
                "custom_metric_sent",
                trace_id=trace_id,
                metric_name=metric_name,
                value=value,
            )
            return True
        except Exception as e:
            logger.error(
                "failed_to_send_custom_metric",
                trace_id=trace_id,
                metric_name=metric_name,
                error=str(e),
            )
            return False


# Global evaluation service instance
evaluation_service = EvaluationService()
