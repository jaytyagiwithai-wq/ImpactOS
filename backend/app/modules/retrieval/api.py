from fastapi import APIRouter, Depends
from app.shared.db.session import get_session
from app.modules.organizations.dependencies import get_local_org_id
from app.modules.retrieval.schema import SearchRequest, SearchResult,SearchResponse
from app.modules.retrieval.hybrid_search import search_active_chunks_hybrid

router = APIRouter(prefix="/v1/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    session = Depends(get_session),
    org_id = Depends(get_local_org_id)) -> SearchResponse:

    outcome = search_active_chunks_hybrid(
        session=session,
        org_id=org_id,
        query_text=payload.query_text,
        limit=payload.limit
    )

   
    return SearchResponse(
        ranking_mode=outcome.ranking_mode,
        results=[
            SearchResult(
                document_title=result.candidate.document_title,
                version_number=result.candidate.version_number,
                chunk_index=result.candidate.chunk_index,
                content=result.candidate.content,
                chunk_id=result.candidate.chunk_id,
                document_id=result.candidate.document_id,
                version_id=result.candidate.version_id,
                vector_position=result.candidate.vector_position,
                lexical_position=result.candidate.lexical_position,
                rrf_score=float(result.candidate.rrf_score),
                rerank_score=result.rerank_score,
                rerank_position=result.rerank_position,
            )
            for result in outcome.results
        ]
    )
