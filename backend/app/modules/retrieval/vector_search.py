
from uuid import UUID
from dataclasses import dataclass
from sqlalchemy.orm import Session
from opentelemetry import trace
import logging
from time import perf_counter
from app.modules.documents.models import Document, DocumentVersion
from app.modules.ingestion.embeddings import embed_texts
from app.modules.ingestion.models import Chunk

from sqlalchemy import select

tracer = trace.get_tracer("impactos.retrieval")
logger = logging.getLogger("impactos.retrieval")

@dataclass
class VectorSearchResult:
    chunk_id: UUID
    document_id: UUID
    document_title: str
    version_id: UUID
    version_number: int
    chunk_index: int
    content: str
    distance: float


def search_active_chunks(
        session: Session,
        org_id: UUID,
        query_text: str,
        limit: int = 10
):
    query_text = query_text.strip()

    if not query_text:
        raise ValueError("Search query cannot blank")

    if not 1 <= limit <= 50:
        raise ValueError("Search limit must be between 1 and 50")


    started = perf_counter()

    attributes = {
        "app.operation":"retrieval.vectore_search",
        "app.tenant.id": str(org_id),
        "app.retrieval.limit":limit,
        "app.retrieval.query.length": len(query_text),       
        "app.retrieval.mode":"Vector",
        "app.outcome": "error"
    }

    with tracer.start_as_current_span("retrieval.vectore_search",attributes=attributes) as span:

        try:
            query_batch = embed_texts(texts=[query_text])
            query_vector = query_batch.vectors[0]

            distance = Chunk.embedding.cosine_distance(query_vector).label(
                "distance"
            )

            statement = (
                select(
                    Chunk.id.label("chunk_id"),
                    Document.id.label("document_id"),
                    Document.title.label("document_title"),
                    DocumentVersion.id.label("version_id"),
                    DocumentVersion.version_number.label("version_number"),
                    Chunk.chunk_index.label("chunk_index"),
                    Chunk.content.label("content"),
                    distance,

                ).join(
                    DocumentVersion, Chunk.version_id == DocumentVersion.id
                ).join(
                    Document,
                    DocumentVersion.document_id == Document.id)
                    .where(Document.org_id == org_id,
                    Document.active_version_id == DocumentVersion.id,
                    DocumentVersion.status == "ready",
                    Chunk.embedding.is_not(None)).order_by(distance, Chunk.id).limit(limit)
            )

            with session.begin():
                rows = session.execute(statement=statement).mappings().all() #mappings() because column names are safer than positions. By default sql alchemy returns in  tuple like format -> to change it to dictionary format we use mapping

            results = [
                VectorSearchResult
                (
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    document_title=row["document_title"],
                    version_id=row["version_id"],
                    version_number=row["version_number"],
                    chunk_index=row["chunk_index"],
                    content=row["content"],
                    distance=float(row["distance"]))    for row in rows        

        ]

            attributes.update(
                {
                    "app.outcome": "success",
                    "app.retrieval.result.count": len(results),
                }
            )
            return results

        except Exception as err:
            attributes["error.type"] = type(err).__name__
            span.record_exception(err)
            raise

        finally:
            attributes["app.duration_ms"] = (
                perf_counter() - started
            ) * 1000 
            span.set_attributes(attributes)


            logger.log(
                logging.INFO
                if attributes["app.outcome"] == "success"
                else logging.ERROR,
                "retrieval.vector_search.completed",
                extra=attributes,
            )
