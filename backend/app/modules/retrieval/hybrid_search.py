from time import perf_counter
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from opentelemetry import trace
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.retrieval.fusion import fuse_ranked_results
from app.modules.retrieval.lexical_search import search_active_chunks_lexically
from app.modules.retrieval.reranking import (
    PairScorer,
    RankedSearchResult,
    get_reranker,
    rerank_candidates,
    rrf_fallback_results,
)
from app.modules.retrieval.vector_search import search_active_chunks


tracer = trace.get_tracer("impactos.retrieval")


@dataclass(frozen=True)
class HybridSearchOutcome:
    results: list[RankedSearchResult]
    ranking_mode: Literal["reranked", "rrf_fallback"]


def search_active_chunks_hybrid(
    session: Session,
    org_id: UUID,
    query_text: str,
    limit: int = 10,
    *,
    reranker: PairScorer | None = None,
) -> HybridSearchOutcome:
    """Retrieve broadly with RRF, then precisely rerank safe candidates."""
    query_text = query_text.strip()
    if not query_text:
        raise ValueError("Search query cannot be blank.")
    if not 1 <= limit <= 50:
        raise ValueError("Search limit must be between 1 and 50.")

    settings = get_settings()
    candidate_limit = max(settings.retrieval_candidate_limit, limit)
    rerank_candidate_limit = max(settings.reranker_candidate_limit, limit)
    if candidate_limit > 50 or rerank_candidate_limit > 50:
        raise ValueError("Retrieval and rerank candidate limits must be at most 50.")

    started = perf_counter()
    attributes = {
        "app.operation": "retrieval.hybrid_search",
        "app.tenant.id": str(org_id),
        "app.retrieval.mode": "hybrid_reranked",
        "app.retrieval.query.length": len(query_text),
        "app.retrieval.candidate_limit": candidate_limit,
        "app.reranker.candidate_limit": rerank_candidate_limit,
        "app.retrieval.vector.count": 0,
        "app.retrieval.lexical.count": 0,
        "app.reranker.input_count": 0,
        "app.reranker.outcome": "not_attempted",
        "app.retrieval.degraded": False,
        "app.retrieval.result.count": 0,
        "app.outcome": "error",
    }

    with tracer.start_as_current_span(
        "retrieval.hybrid_search", attributes=attributes
    ) as span:
        try:
            vector_results = search_active_chunks(
                session=session,
                org_id=org_id,
                query_text=query_text,
                limit=candidate_limit,
            )
            lexical_results = search_active_chunks_lexically(
                session=session,
                org_id=org_id,
                query_text=query_text,
                limit=candidate_limit,
            )
            fused_candidates = fuse_ranked_results(
                vector_results=vector_results,
                lexical_results=lexical_results,
                limit=rerank_candidate_limit,
            )

            try:
                scorer = reranker or get_reranker()
                results = rerank_candidates(
                    query_text=query_text,
                    candidates=fused_candidates,
                    scorer=scorer,
                    limit=limit,
                )
                ranking_mode = "reranked"
                attributes["app.reranker.model"] = getattr(
                    scorer, "model_name", "custom"
                )
                attributes["app.reranker.outcome"] = "success"
            except Exception as error:
                # Retrieval succeeded and candidates have already passed tenant,
                # active-version, and ready-version filtering. Degrade only this
                # optional ranking stage; never hide the condition from telemetry.
                results = rrf_fallback_results(fused_candidates, limit=limit)
                ranking_mode = "rrf_fallback"
                attributes["app.reranker.outcome"] = "error"
                attributes["app.reranker.error.type"] = type(error).__name__
                attributes["app.retrieval.degraded"] = True
                span.record_exception(error)

            attributes.update(
                {
                    "app.retrieval.vector.count": len(vector_results),
                    "app.retrieval.lexical.count": len(lexical_results),
                    "app.reranker.input_count": len(fused_candidates),
                    "app.retrieval.result.count": len(results),
                    "app.outcome": "success",
                }
            )
            return HybridSearchOutcome(
                results=results,
                ranking_mode=ranking_mode,
            )
        except Exception as error:
            attributes["error.type"] = type(error).__name__
            span.record_exception(error)
            raise
        finally:
            attributes["app.duration_ms"] = (perf_counter() - started) * 1_000
            span.set_attributes(attributes)
