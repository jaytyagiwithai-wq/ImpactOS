from uuid import UUID

import pytest

from app.modules.retrieval.fusion import FusedSearchResult
from app.modules.retrieval.reranking import rrf_fallback_results, rerank_candidates


class FakeScorer:
    def __init__(self, scores: list[float]):
        self.scores = scores
        self.calls: list[list[tuple[str, str]]] = []

    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        self.calls.append(pairs)
        return self.scores


def candidate(number: int, content: str) -> FusedSearchResult:
    return FusedSearchResult(
        chunk_id=UUID(int=number),
        document_id=UUID(int=100 + number),
        document_title=f"Document {number}",
        version_id=UUID(int=200 + number),
        version_number=1,
        chunk_index=number,
        content=content,
        rrf_score=0.01,
        vector_position=number,
        lexical_position=None,
        vector_distance=0.1,
        lexical_score=None,
    )


def test_rerank_candidates_batches_scores_and_preserves_provenance():
    first = candidate(1, "first chunk")
    second = candidate(2, "second chunk")
    third = candidate(3, "third chunk")
    scorer = FakeScorer([0.2, 0.9, 0.5])

    results = rerank_candidates(
        "Which evidence matters?",
        [first, second, third],
        scorer,
        limit=2,
    )

    assert scorer.calls == [[
        ("Which evidence matters?", "first chunk"),
        ("Which evidence matters?", "second chunk"),
        ("Which evidence matters?", "third chunk"),
    ]]
    assert [result.candidate.chunk_id for result in results] == [second.chunk_id, third.chunk_id]
    assert [result.rerank_score for result in results] == [0.9, 0.5]
    assert [result.rerank_position for result in results] == [1, 2]
    assert results[0].candidate.vector_position == second.vector_position
    assert results[0].candidate.rrf_score == second.rrf_score


def test_rerank_candidates_uses_chunk_id_to_break_equal_score_ties():
    lower_id = candidate(1, "lower id")
    higher_id = candidate(2, "higher id")
    scorer = FakeScorer([0.5, 0.5])

    results = rerank_candidates(
        "question",
        [higher_id, lower_id],
        scorer,
    )

    assert [result.candidate.chunk_id for result in results] == [lower_id.chunk_id, higher_id.chunk_id]


def test_rerank_candidates_rejects_unaligned_scores():
    with pytest.raises(ValueError, match="unexpected score count"):
        rerank_candidates(
            "question",
            [candidate(1, "one"), candidate(2, "two")],
            FakeScorer([0.5]),
        )


def test_rrf_fallback_preserves_rrf_order_without_inventing_scores():
    first = candidate(1, "first")
    second = candidate(2, "second")

    results = rrf_fallback_results([first, second], limit=1)

    assert [result.candidate.chunk_id for result in results] == [first.chunk_id]
    assert results[0].rerank_score is None
    assert results[0].rerank_position is None
