import logging
from time import perf_counter
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from langchain_core.documents import Document as LoadedDocument
from opentelemetry import trace
from app.modules.documents.models import Document, DocumentVersion
from app.modules.ingestion.models import Chunk

from app.core.config import get_settings
from app.modules.ingestion.embeddings import embed_texts
from app.modules.ingestion.chunking import chunk_docs
from app.modules.ingestion.loaders import load_doc
from app.shared.storage.local import UPLOAD_ROOT


from app.modules.documents.service import (
    begin_version_processing,
    mark_version_failed,
    mark_version_ready,
)

tracer = trace.get_tracer("impactos.ingestion")
logger = logging.getLogger("impactos.ingestion")
logger.setLevel(logging.INFO)

def chunk_values(chunk: Chunk) -> tuple:

    return(
        chunk.chunk_index,
        chunk.content,
        chunk.token_count,
        chunk.chunker_version,
        chunk.tokenizer,
        chunk.max_tokens,
        chunk.overlap_tokens
        
    )


def save_chunks(
        session: Session,
        org_id: UUID,
        version_id: UUID,
        chunks: list[LoadedDocument]
)-> int:

    started = perf_counter()

        
    attributes = {   
        "app.operation": "ingestion.persist",
        "app.tenant.id": str(org_id),
        "app.document.version.id": str(version_id),
        "app.chunk.count": len(chunks),
        "app.outcome": "error",
    }

    with tracer.start_as_current_span("ingestion.persist", attributes=attributes) as span:
        try:
            if not chunks:
                raise ValueError("Cannot save empty chunk set")
            rows=[]

            for i, chunk in enumerate(chunks):
                metadata = chunk.metadata
                rows.append(
                    Chunk(
                        version_id=version_id,
                        chunk_index = i,
                        content=chunk.page_content,
                        token_count=metadata["token_count"],
                        tokenizer=metadata["tokenizer"],
                        max_tokens=metadata["max_tokens"],
                        overlap_tokens=metadata["overlap_tokens"],
                        chunker_version=metadata["chunker_version"],
                    )
                )

            with session.begin():
                statement = select(DocumentVersion).join(Document, DocumentVersion.document_id == Document.id).where(DocumentVersion.id == version_id, Document.org_id ==org_id).with_for_update(of=DocumentVersion)
                version = session.scalar(statement=statement)

                if version is None:
                    raise LookupError("Document Version is not found")

                existing = session.scalars(
                    select(Chunk).where(Chunk.version_id == version_id)
                    .order_by(Chunk.chunk_index)
                ).all()

                if existing:
                    old_vals = [
                        chunk_values(row) for row in existing
                    ]
                    new_vals = [
                        chunk_values(row) for row in rows
                    ]

                    if old_vals != new_vals:
                        raise ValueError(
                            "Version already has a different chunk set"
                        )

                    result = "unchanged"
                else:
                    if version.status == "ready":
                        raise ValueError(
                            "Cannot add chunks to a ready version"
                        )

                    session.add_all(rows)
                    result = "created"

            attributes.update({
                "app.outcome": "success",
                "app.persist.result": result,
            })
            return len(rows)
        
        except Exception as err:
            attributes["error.type"] = type(err).__name__
            raise

        finally:
            attributes["app.duration_ms"] = (
            perf_counter() - started) * 1000

            span.set_attributes(attributes)

            level = (
                logging.INFO
                if attributes["app.outcome"] == "success"
                else logging.ERROR 
            )

            logger.log(
                level,
                "ingestion.persist.completed",
                extra=attributes
            )



def ingest_version(
        session: Session,
        org_id:UUID,
        version_id: UUID
) -> int:

    started = perf_counter()
    attributes = {
        "app.operation":"ingestion.run",
        "app.tenant.id":str(org_id),
        "app.document.version.id": str(version_id),
        "app.outcome":"error"

    }


    with tracer.start_as_current_span("ingestion.run", attributes=attributes) as span:
        try:
            
            should_process = begin_version_processing(
                session=session,
                org_id=org_id,
                version_id=version_id,
            )

            if not should_process:
                attributes.update(
                    {
                        "app.outcome": "success",
                        "app.ingestion.result": "already_ready",
                        "app.chunk.count": 0,
                    }
                )

                return 0

            
            with session.begin():
                source = session.execute(
                    select(
                        DocumentVersion.document_id,
                        DocumentVersion.storage_key,
                        Document.source_type
                    ).join(
                        Document,
                        DocumentVersion.document_id == Document.id,
                    )
                    .where(
                        DocumentVersion.id == version_id,
                        Document.org_id == org_id
                    )
                ).one_or_none()

                if source is None:
                    raise LookupError("Document version not found")

            root = UPLOAD_ROOT.resolve()
            path = (root / source.storage_key).resolve()

            if not path.is_relative_to(root):
                raise ValueError("Invalid storage key")

            with tracer.start_as_current_span("ingestion.load"):
                doc = load_doc(
                    path=path,
                    source_type=source.source_type,
                    org_id=org_id,
                    document_id=source.document_id,
                    version_id=version_id
                )

            with tracer.start_as_current_span("ingestion.chunk") as chunk_span:
                chunks = chunk_docs(documents=doc)

                chunk_span.set_attribute(
                    "app.chunk.count", len(chunks)
                )
            
            count = save_chunks(
                session=session,
                org_id=org_id,
                version_id=version_id,
                chunks=chunks
            )
            
            embedded_count = embed_version(
                session=session,
                org_id=org_id,
                version_id=version_id,
            )

            mark_version_ready(
                session=session,
                org_id=org_id,
                version_id=version_id,
            )

            attributes.update({
                "app.outcome":"success",
                "app.chunk.count": count,
                "app.embedding.chunks.written":embedded_count
            })

            return count
        
        except Exception as exc:
            attributes["error.type"] = type(exc).__name__
            
            try:
                mark_version_failed(
                    session=session,
                    org_id=org_id,
                    version_id=version_id,
                )
                
            except Exception:
                logger.exception(
                    "ingestion.mark_failed.failed",
                    extra={
                        "app.document.version.id": str(version_id),
                    },
                )
            raise

        finally:
            attributes["app.duration_ms"] = (perf_counter()-started)*1000
            span.set_attributes(attributes)

            logger.log(
                logging.INFO
                if attributes["app.outcome"] == "success"
                else logging.ERROR,
                "ingestion.run.completed",
                extra=attributes,
            )



def embed_version(
    session: Session,
    org_id: UUID,
    version_id: UUID
)-> int:

    started = perf_counter()

    setting = get_settings()

    attributes = {
        "app.operation":"embedding.persist",
        "app.tenant.id":str(org_id),
        "app.document.version.id": str(version_id),
        "app.embedding.outcome": "error",
        "app.embedding.chunks.found":0,
        "app.embedding.chunks.written": 0,
        "app.embedding.prompt_tokens": 0,
   }

    with tracer.start_as_current_span("embedding.persist", attributes=attributes) as span:
        try:
            with session.begin():
                statement = select(DocumentVersion.id).join(Document, DocumentVersion.document_id == Document.id).where(DocumentVersion.id == version_id, Document.org_id == org_id)
                version = session.scalar(statement=statement)

                if version is None:
                    raise ValueError("No document version found")
            written = 0

            while True:
                with session.begin():
                    rows = session.execute(
                        select(Chunk.id, Chunk.content)
                        .join(
                            DocumentVersion,
                            Chunk.version_id == DocumentVersion.id,
                        )
                        .join(
                            Document,
                            DocumentVersion.document_id == Document.id
                        )
                        .where(
                            Chunk.version_id == version_id,
                            DocumentVersion.id == version_id,
                            Document.org_id == org_id,
                            Chunk.embedding.is_(None),
                        )
                        .order_by(Chunk.chunk_index)
                        .limit(setting.embedding_batch_size)
                    ).all()

                if not rows:
                    break

                attributes["app.embedding.chunks.found"] += len(rows)

                result = embed_texts([content for _, content in rows])

                attributes["app.embedding.prompt_tokens"] += result.prompt_tokens

                with session.begin():
                    for (chunk_id, _), vector in zip(
                        rows,
                        result.vectors,
                        strict=True, #raise error if both list have diff lengths
                    ):
                        update_result = session.execute(
                            update(Chunk)
                            .where(
                                Chunk.id == chunk_id,
                                Chunk.embedding.is_(None),
                            )
                            .values(
                                embedding=vector,
                                embedding_model=result.model,
                            )
                        )
                        written += update_result.rowcount or 0

            attributes.update(
                {
                    "app.embedding.chunks.written": written,
                    "app.embedding.outcome": "success",
                }
            )
            return written

        except Exception as exc:
            attributes["error.type"] = type(exc).__name__
            span.record_exception(exc)
            raise

        finally:
            attributes["app.duration_ms"] = (
                perf_counter() - started
            ) * 1000

            span.set_attributes(attributes)

            logger.log(
                logging.INFO
                if attributes["app.embedding.outcome"] == "success"
                else logging.ERROR,
                "embedding.persist.completed",
                extra=attributes,
            )


