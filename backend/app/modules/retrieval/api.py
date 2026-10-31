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

    results = search_active_chunks_hybrid(
        session=session,
        org_id=org_id,
        query_text=payload.query_text,
        limit=payload.limit
    )

   
    return SearchResponse(results=[SearchResult(
        document_title=result.document_title, 
        version_number=result.version_number, 
        chunk_index=result.chunk_index, 
        content=result.content,
        chunk_id=result.chunk_id,
        document_id=result.document_id,
        version_id=result.version_id,
        vector_position=result.vector_position,
        lexical_position=result.lexical_position,
        rrf_score=float(result.rrf_score)) for result in results]
    )
