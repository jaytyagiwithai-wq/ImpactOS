from pydantic import BaseModel, ConfigDict, StringConstraints, Field
from typing import Annotated, Literal
from uuid import UUID
class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)]
    limit: int = Field(default=1,min=1, max=10)



class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_title: str
    version_number: int
    chunk_index: int
    content: str
    rrf_score: float
    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    vector_position: int | None
    lexical_position: int | None
    rerank_score: float | None
    rerank_position: int | None


class SearchResponse(BaseModel):
    ranking_mode: Literal["reranked", "rrf_fallback"]
    results: list[SearchResult]
