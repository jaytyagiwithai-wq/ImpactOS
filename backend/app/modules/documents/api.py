from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.documents import service
from app.modules.documents.errors import (
    DocumentNotFound,
    DocumentStorageUnavailable,
    InvalidUpload,
)
from app.modules.documents.schemas import (
    DocumentCreate,
    DocumentRead,
    DocumentSourceRead,
    DocumentVersionRead,
    SourceChunkRead,
)
from app.modules.documents.models import Document, DocumentVersion
from app.modules.ingestion.models import Chunk
from app.modules.ingestion.service import ingest_version
from app.core.config import get_settings
from app.modules.organizations.dependencies import get_local_org_id
from app.shared.db.session import get_session
from app.shared.storage.base import EmptyUpload, UploadStorage, UploadTooLarge
from app.shared.storage.dependencies import get_upload_storage

router = APIRouter(prefix="/v1/documents", tags=["documents"])


def _owned_version(
    session: Session, org_id: UUID, document_id: UUID, version_id: UUID
) -> DocumentVersion:
    version = session.scalar(
        select(DocumentVersion)
        .join(Document, DocumentVersion.document_id == Document.id)
        .where(
            DocumentVersion.id == version_id,
            DocumentVersion.document_id == document_id,
            Document.org_id == org_id,
        )
    )
    if version is None:
        raise HTTPException(404, "Document version not found")
    return version


@router.get("", response_model=list[DocumentSourceRead])
def list_documents(
    session: Annotated[Session, Depends(get_session)],
    org_id: Annotated[UUID, Depends(get_local_org_id)],
) -> list[DocumentSourceRead]:
    documents = session.scalars(
        select(Document)
        .where(Document.org_id == org_id)
        .order_by(Document.created_at.desc())
    ).all()

    result: list[DocumentSourceRead] = []
    for document in documents:
        latest_version = session.scalar(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document.id)
            .order_by(DocumentVersion.version_number.desc())
            .limit(1)
        )
        result.append(
            DocumentSourceRead(
                document=DocumentRead.model_validate(document),
                latest_version=(
                    DocumentVersionRead.model_validate(latest_version)
                    if latest_version is not None
                    else None
                ),
            )
        )
    return result


@router.post("", response_model=DocumentRead, status_code=201)
def create_document(
    payload: DocumentCreate,
    session: Annotated[Session, Depends(get_session)],
    org_id: Annotated[UUID, Depends(get_local_org_id)],
) -> DocumentRead:
    try:
        return service.create_document(session, org_id, payload)
    except DocumentStorageUnavailable:
        raise HTTPException(503, "Document storage unavailable") from None


@router.post(
    "/{document_id}/versions", response_model=DocumentVersionRead, status_code=201
)
def upload_document_version(
    document_id: UUID,
    file: Annotated[UploadFile, File()],
    org_id: Annotated[UUID, Depends(get_local_org_id)],
    session: Annotated[Session, Depends(get_session)],
    storage: Annotated[UploadStorage, Depends(get_upload_storage)],
) -> DocumentVersionRead:
    try:
        return service.upload_document_version(
            session=session,
            storage=storage,
            org_id=org_id,
            document_id=document_id,
            source=file.file,
            filename=file.filename,
            media_type=file.content_type,
        )
    except DocumentNotFound:
        raise HTTPException(404, "Document not found") from None
    except UploadTooLarge as error:
        raise HTTPException(413, str(error)) from None
    except (EmptyUpload, InvalidUpload) as error:
        raise HTTPException(400, str(error)) from None
    except DocumentStorageUnavailable:
        raise HTTPException(503, "Document storage unavailable") from None


@router.get(
    "/{document_id}/versions/{version_id}", response_model=DocumentVersionRead
)
def get_document_version(
    document_id: UUID,
    version_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    org_id: Annotated[UUID, Depends(get_local_org_id)],
) -> DocumentVersionRead:
    return DocumentVersionRead.model_validate(
        _owned_version(session, org_id, document_id, version_id)
    )


@router.post(
    "/{document_id}/versions/{version_id}/index", response_model=DocumentVersionRead
)
def index_document_version(
    document_id: UUID,
    version_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    org_id: Annotated[UUID, Depends(get_local_org_id)],
) -> DocumentVersionRead:
    """Synchronous local-development bridge; production workers consume queued jobs."""
    if get_settings().app_env not in {"local", "test"}:
        raise HTTPException(503, "Interactive indexing is disabled outside local development")

    _owned_version(session, org_id, document_id, version_id)
    try:
        ingest_version(session=session, org_id=org_id, version_id=version_id)
    except ValueError as error:
        raise HTTPException(400, str(error)) from None
    except Exception:
        raise HTTPException(500, "Indexing failed. Check the ingestion trace for details.") from None

    return DocumentVersionRead.model_validate(
        _owned_version(session, org_id, document_id, version_id)
    )


@router.get("/chunks/{chunk_id}", response_model=SourceChunkRead)
def get_active_source_chunk(
    chunk_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    org_id: Annotated[UUID, Depends(get_local_org_id)],
) -> SourceChunkRead:
    row = session.execute(
        select(
            Chunk.id.label("chunk_id"),
            Document.id.label("document_id"),
            Document.title.label("document_title"),
            Document.source_type.label("source_type"),
            DocumentVersion.id.label("version_id"),
            DocumentVersion.version_number.label("version_number"),
            DocumentVersion.original_filename.label("original_filename"),
            Chunk.chunk_index.label("chunk_index"),
            Chunk.content.label("content"),
        )
        .join(DocumentVersion, Chunk.version_id == DocumentVersion.id)
        .join(Document, DocumentVersion.document_id == Document.id)
        .where(
            Chunk.id == chunk_id,
            Document.org_id == org_id,
            Document.active_version_id == DocumentVersion.id,
            DocumentVersion.status == "ready",
        )
    ).mappings().one_or_none()
    if row is None:
        raise HTTPException(404, "Active source chunk not found")
    return SourceChunkRead.model_validate(row)
