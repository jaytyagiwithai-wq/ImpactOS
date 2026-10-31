from dataclasses import dataclass
from uuid import UUID

from app.modules.retrieval.lexical_search import LexicalSearchResult
from app.modules.retrieval.vector_search import VectorSearchResult


@dataclass
class FusedSearchResult:
    chunk_id: UUID
    document_id: UUID
    document_title: str
    version_id: UUID
    version_number: int
    chunk_index: int
    content: str

    rrf_score: float
    vector_position: int | None
    lexical_position: int | None

    vector_distance: float | None
    lexical_score: float | None


def fuse_ranked_results(
    vector_results: list[VectorSearchResult],
    lexical_results: list[LexicalSearchResult],
    *,
    limit: int = 10,
    rrf_k: int = 60,
    vector_weight: float = 1.0,
    lexical_weight: float = 1.0,
) -> list[FusedSearchResult]:
    if not 1 <= limit <= 50:
        raise ValueError("Fusion limit must be between 1 and 50.")

    if rrf_k < 1:
        raise ValueError("RRF constant must be positive.")

    if vector_weight < 0 or lexical_weight < 0:
        raise ValueError("Retriever weights cannot be negative.")

    if vector_weight == 0 and lexical_weight == 0:
        raise ValueError("At least one retriever weight must be positive.")

    scores: dict[UUID, float] = {}
    vector_by_id: dict[UUID, VectorSearchResult] = {}
    lexical_by_id: dict[UUID, LexicalSearchResult] = {}
    vector_positions: dict[UUID, int] = {}
    lexical_positions: dict[UUID, int] = {}

    for position, result in enumerate(vector_results, start=1):
        if result.chunk_id in vector_by_id:
            continue

        vector_by_id[result.chunk_id] = result
        vector_positions[result.chunk_id] = position
        scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + (
            vector_weight / (rrf_k + position)
        )

    for position, result in enumerate(lexical_results, start=1):
        if result.chunk_id in lexical_by_id:
            continue

        lexical_by_id[result.chunk_id] = result
        lexical_positions[result.chunk_id] = position
        scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + (
            lexical_weight / (rrf_k + position)
        )

    fused_results = []

    for chunk_id, rrf_score in scores.items():
        vector_result = vector_by_id.get(chunk_id)
        lexical_result = lexical_by_id.get(chunk_id)

        # Both retrieval paths point to the same underlying chunk.
        evidence = vector_result or lexical_result
        assert evidence is not None

        fused_results.append(
            FusedSearchResult(
                chunk_id=chunk_id,
                document_id=evidence.document_id,
                document_title=evidence.document_title,
                version_id=evidence.version_id,
                version_number=evidence.version_number,
                chunk_index=evidence.chunk_index,
                content=evidence.content,
                rrf_score=rrf_score,
                vector_position=vector_positions.get(chunk_id),
                lexical_position=lexical_positions.get(chunk_id),
                vector_distance=(
                    vector_result.distance
                    if vector_result is not None
                    else None
                ),
                lexical_score=(
                    lexical_result.rank
                    if lexical_result is not None
                    else None
                ),
            )
        )

    return sorted(
        fused_results,
        key=lambda result: (
            -result.rrf_score,
            min(
                result.vector_position or 10_000,
                result.lexical_position or 10_000,
            ),
            str(result.chunk_id),
        ),
    )[:limit]