from uuid import UUID

from app.modules.retrieval.fusion import FusedSearchResult
from app.modules.retrieval.hybrid_search import search_active_chunks_hybrid
from app.modules.retrieval.lexical_search import LexicalSearchResult
from app.modules.retrieval.vector_search import VectorSearchResult


class FailingScorer:
    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        raise RuntimeError("simulated reranker outage")


def test_hybrid_search_falls_back_to_rrf_when_reranker_fails(monkeypatch):
    vector = VectorSearchResult(
        chunk_id=UUID(int=1), document_id=UUID(int=11), document_title="Vector",
        version_id=UUID(int=21), version_number=1, chunk_index=0,
        content="vector evidence", distance=0.1,
    )
    lexical = LexicalSearchResult(
        chunk_id=UUID(int=2), document_id=UUID(int=12), document_title="Lexical",
        version_id=UUID(int=22), version_number=1, chunk_index=0,
        content="lexical evidence", rank=0.9,
    )

    monkeypatch.setattr(
        "app.modules.retrieval.hybrid_search.search_active_chunks",
        lambda **_: [vector],
    )
    monkeypatch.setattr(
        "app.modules.retrieval.hybrid_search.search_active_chunks_lexically",
        lambda **_: [lexical],
    )

    outcome = search_active_chunks_hybrid(
        session=object(),
        org_id=UUID(int=100),
        query_text="question",
        limit=2,
        reranker=FailingScorer(),
    )

    assert outcome.ranking_mode == "rrf_fallback"
    assert [item.candidate.chunk_id for item in outcome.results] == [
        vector.chunk_id,
        lexical.chunk_id,
    ]
    assert all(item.rerank_score is None for item in outcome.results)
