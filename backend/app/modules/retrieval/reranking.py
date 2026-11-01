from dataclasses import dataclass
from functools import lru_cache
from math import isfinite
from typing import Protocol

from app.core.config import get_settings
from app.modules.retrieval.fusion import FusedSearchResult


class PairScorer(Protocol):
    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
    ) -> list[float]:
        """Return exactly one relevance score for every input pair."""


@dataclass(frozen=True)
class RerankedSearchResult:
    candidate: FusedSearchResult
    rerank_score: float | None
    rerank_position: int | None


def rrf_fallback_results(
    candidates: list[FusedSearchResult],
    *,
    limit: int,
) -> list[RerankedSearchResult]:
    """Preserve safe RRF ordering when the optional reranker is unavailable."""
    if not 1 <= limit <= 50:
        raise ValueError("Rerank limit must be between 1 and 50.")

    return [
        RerankedSearchResult(
            candidate=candidate,
            rerank_score=None,
            rerank_position=None,
        )
        for candidate in candidates[:limit]
    ]


class CrossEncoderPairScorer:

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2",
        *,
        batch_size: int = 16,
        max_length: int = 512,
    ) -> None:
        # Import the ML runtime only when a process actually creates a scorer.
        from sentence_transformers import CrossEncoder


        if batch_size < 1:
            raise ValueError("Reranker batch size must be positive.")

        if max_length < 32:
            raise ValueError("Reranker max length is too small.")

        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length

        self._model = CrossEncoder(
            model_name,
            max_length=max_length,
        )

    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
    ) -> list[float]:
        if not pairs:
            return []

        scores = self._model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        return [float(score) for score in scores]


@lru_cache
def get_reranker() -> CrossEncoderPairScorer:
    """One loaded model per Python process, never one model per request."""
    settings = get_settings()
    return CrossEncoderPairScorer(
        model_name=settings.reranker_model,
        batch_size=settings.reranker_batch_size,
        max_length=settings.reranker_max_length,
    )

def rerank_candidates(
    query_text: str,
    candidates: list[FusedSearchResult],
    scorer: PairScorer,
    *,
    limit: int = 5,
) -> list[RerankedSearchResult]:

    query_text = query_text.strip()
    if not query_text:
        raise ValueError("Rerank query cannot be blank")

    if not 1 <= limit <= 50:
        raise ValueError("Rerank limit must be between 1 and 50.")

    if not candidates:
        return []


    pairs = [(query_text, candidate.content) for candidate in candidates]

    scores = scorer.score_pairs(pairs)

    if len(scores) != len(candidates):
        raise ValueError("Reranker returned an unexpected score count.")


    if any(not isfinite(score) for score in scores):
        raise ValueError("Reranker returned a non-finite score.")

    scored_candidates = list(zip(candidates, scores, strict=True))

    scored_candidates.sort(
        key=lambda item: (
            -item[1],
            str(item[0].chunk_id),
        )
    )



    return [
        RerankedSearchResult(
            candidate=candidate,
            rerank_score=score,
            rerank_position=position,
        )
        for position, (candidate, score) in enumerate(
            scored_candidates[:limit],
            start=1,
        )
    ]
