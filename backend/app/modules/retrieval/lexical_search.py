from opentelemetry import trace
import logging
from dataclasses import dataclass
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import cast, literal, select, func, or_
from sqlalchemy.dialects.postgresql import REGCONFIG
from app.modules.documents.models import Document, DocumentVersion
from app.modules.ingestion.models import Chunk
from time import perf_counter


from app.modules.retrieval.query_analysis import (
    build_broad_lexical_query,
)


tracer = trace.get_tracer("impactos.retrieval")
logger = logging.getLogger("impactos.retrieval")

@dataclass
class LexicalSearchResult:
    chunk_id: UUID
    document_id: UUID
    document_title: str
    version_id: UUID
    version_number: int
    chunk_index: int
    content: str
    rank: float



def search_active_chunks_lexically(
        session:Session,
        org_id:UUID,
        query_text: str,
        limit: int = 10
        ) -> list[LexicalSearchResult]:

    query_text = query_text.strip()

    if not query_text:
        raise ValueError("Search query cannot be blank")

    if not 1 <= limit <= 50:
        raise ValueError("Search limit should be between 1 and 50")


    started = perf_counter()

    attributes = {
        "app.operation": "retrieval.lexical_search",
        "app.tenant.id": str(org_id),
        "app.retrieval.limit": limit,
        "app.retrieval.query.length": len(query_text),
        "app.retrieval.mode": "lexical",
        "app.outcome": "error",

    }
    with tracer.start_as_current_span("retrieval.lexical_search" , attributes=attributes) as span:
        try:

            text_config = cast(literal("english"), REGCONFIG)

            strict_tsquery = func.websearch_to_tsquery(
                text_config,
                query_text,
            )

            broad_query_text = build_broad_lexical_query(query_text)

            broad_tsquery = func.websearch_to_tsquery(
                text_config,
                broad_query_text,
            )
            strict_rank = func.ts_rank_cd(
                Chunk.textsearch,
                strict_tsquery,
            )

            broad_rank = func.ts_rank_cd(
                Chunk.textsearch,
                broad_tsquery,
            )

            rank = func.greatest(
                strict_rank,
                broad_rank,
            ).label("rank")

            strict_match = Chunk.textsearch.op("@@")(strict_tsquery)
            broad_match = Chunk.textsearch.op("@@")(broad_tsquery)


            statement = (
                select(
                    Chunk.id.label("chunk_id"),
                    Document.id.label("document_id"),
                    Document.title.label("document_title"),
                    DocumentVersion.id.label("version_id"),
                    DocumentVersion.version_number.label("version_number"),
                    Chunk.chunk_index.label("chunk_index"),
                    Chunk.content.label("content"),
                    rank,
                )
                .join(
                    DocumentVersion,
                    Chunk.version_id == DocumentVersion.id,
                )
                .join(
                    Document,
                    DocumentVersion.document_id == Document.id,
                )
                .where(
                    Document.org_id == org_id,
                    Document.active_version_id == DocumentVersion.id,
                    DocumentVersion.status == "ready",
                    or_(strict_match, broad_match),
                )
                .order_by(rank.desc(), Chunk.id)
                .limit(limit)
            )

            with session.begin():
                rows = session.execute(statement).mappings().all()

            results = [
                LexicalSearchResult(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    document_title=row["document_title"],
                    version_id=row["version_id"],
                    version_number=row["version_number"],
                    chunk_index=row["chunk_index"],
                    content=row["content"],
                    rank=float(row["rank"]),
                )
                for row in rows
            ]

            attributes.update(
                {
                    "app.outcome": "success",
                    "app.retrieval.result.count": len(results),
                }
            )
            return results

        except Exception as error:
            attributes["error.type"] = type(error).__name__
            span.record_exception(error)
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
                "retrieval.lexical_search.completed",
                extra=attributes,
            )
