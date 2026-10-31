from uuid import UUID
from time import perf_counter
from sqlalchemy.orm import Session

from app.modules.retrieval.fusion import (
    FusedSearchResult,
    fuse_ranked_results,
)
from app.modules.retrieval.lexical_search import (
    search_active_chunks_lexically,
)
from app.modules.retrieval.vector_search import (
    search_active_chunks,
)
from opentelemetry import trace

tracer = trace.get_tracer("impactos.retrieval")




def search_active_chunks_hybrid(
        session:Session,
        org_id: UUID,
        query_text: str,
        limit: int = 10
) -> list[FusedSearchResult]:


    started = perf_counter()

    #ensures minimum candidate pool
    candidate_limit = max(30, limit) # we retrieve wider candidate set than final number of results because hybrid fusion needs enough overalp between retrieval method. A chunk that is rank 20 in both searhces can be a stronger rrd score 

    attributes = {
            "app.operation": "retrieval.hybrid_search",
            "app.tenant.id": str(org_id),
            "app.retrieval.mode" : "hybrid",
            "app.retrieval.query.length":len(query_text),
            "app.retrieval.candidate_limit":candidate_limit,
            "app.retrieval.vector.count":0,
            "app.retrieval.lexical.count":0,
            "app.retrieval.result.count":0,
            "app.outcome":"error"

        }

    with tracer.start_as_current_span("retrieval.hybrid_search", attributes=attributes) as span:
            try:
                vector_result = search_active_chunks(
                    session=session,
                    org_id=org_id,
                    query_text=query_text,
                    limit=candidate_limit
                )


                lexical_results = search_active_chunks_lexically(
                    session=session,
                    org_id=org_id,
                    query_text=query_text,
                    limit=candidate_limit

                )
                fused_results = fuse_ranked_results(
                    vector_results=vector_result,
                    lexical_results=lexical_results,
                    limit=limit,
                )

                attributes.update(
                    {
                        "app.retrieval.vector.count": len(vector_result),
                        "app.retrieval.lexical.count": len(lexical_results),
                        "app.retrieval.result.count": len(fused_results),
                        "app.outcome": "success",
                    }
                )

                return fused_results
            

            except Exception as er:
                attributes["error.type"] = type(er).__name__
                span.record_exception(exception=er)
                raise

            finally:
                 time = (perf_counter() - started) *1000 
                 attributes["app.duration_ms"] = time
                 span.set_attributes(attributes=attributes)