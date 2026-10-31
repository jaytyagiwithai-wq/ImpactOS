import logging
from time import perf_counter
from typing import BinaryIO
from uuid import UUID, uuid4

from opentelemetry import trace
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.documents.errors import (
    DocumentNotFound,
    DocumentStorageUnavailable,
    InvalidUpload,
)
from app.modules.documents.models import Document, DocumentVersion
from app.modules.documents.schemas import (
    DocumentCreate,
    DocumentRead,
    DocumentVersionRead,
)
from app.shared.storage.base import EmptyUpload, UploadStorage, UploadTooLarge

tracer = trace.get_tracer("impactos.documents")
logger = logging.getLogger("impactos.documents")
logger.setLevel(logging.INFO)


def create_document(
    session: Session,
    org_id: UUID,
    payload: DocumentCreate,
) -> DocumentRead:
    started = perf_counter()
    attributes = {
        "app.operation": "document.create",
        "app.tenant.id": str(org_id),
        "app.document.source_type": payload.source_type,
        "app.outcome": "unexpected_error",
    }
    log_level = logging.ERROR

    with tracer.start_as_current_span("document.create", attributes=attributes) as span:
        try:
            with session.begin():
                document = Document(
                    org_id=org_id,
                    title=payload.title,
                    source_type=payload.source_type,
                    status="registered",
                )
                session.add(document)
                session.flush()
                session.refresh(document)
                response = DocumentRead.model_validate(document)

            # Exiting session.begin() must succeed before reporting success.
            attributes.update({
                "app.outcome": "success",
                "app.document.id": str(response.id),
            })
            log_level = logging.INFO
            return response
        except SQLAlchemyError as error:
            attributes.update({
                "app.outcome": "database_error",
                "error.type": type(error).__name__,
            })
            raise DocumentStorageUnavailable("Document storage unavailable") from None
        finally:
            attributes["app.duration_ms"] = (perf_counter() - started) * 1000
            span.set_attributes(attributes)
            logger.log(log_level, "documents.create.completed", extra=attributes)


def upload_document_version(
    session: Session,
    storage: UploadStorage,
    org_id: UUID,
    document_id: UUID,
    source: BinaryIO,
    filename: str | None,
    media_type: str | None,
) -> DocumentVersionRead:
    version_id = uuid4()
    started = perf_counter()
    file_saved = False
    log_level = logging.ERROR
    attributes = {
        "app.operation": "document_versions.upload",
        "app.tenant.id": str(org_id),
        "app.document.id": str(document_id),
        "app.document.version.id": str(version_id),
        "app.outcome": "unexpected_error",
        "storage.backend": storage.backend,
    }

    with tracer.start_as_current_span(
        "document_version.upload", attributes=attributes
    ) as span:
        try:
            filename = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
            media_type = media_type or "application/octet-stream"
            if not filename or len(filename) > 255 or "\x00" in filename:
                raise InvalidUpload("Invalid filename")
            if len(media_type) > 255:
                raise InvalidUpload("Invalid media type")

            with session.begin():
                owned_id = session.scalar(
                    select(Document.id).where(
                        Document.id == document_id,
                        Document.org_id == org_id,
                    )
                )
                if owned_id is None:
                    raise DocumentNotFound("Document not found")

            # File I/O is outside the database transaction.
            source.seek(0)
            with tracer.start_as_current_span("storage.write"):
                stored = storage.save_upload(source, org_id, document_id, version_id)
                file_saved = True

            with session.begin():
                locked_id = session.scalar(
                    select(Document.id)
                    .where(Document.id == document_id, Document.org_id == org_id)
                    .with_for_update()
                )
                if locked_id is None:
                    raise DocumentNotFound("Document not found")

                latest_number = session.scalar(
                    select(func.max(DocumentVersion.version_number)).where(
                        DocumentVersion.document_id == document_id
                    )
                )
                version = DocumentVersion(
                    id=version_id,
                    document_id=document_id,
                    version_number=(latest_number or 0) + 1,
                    original_filename=filename,
                    media_type=media_type,
                    storage_key=stored.storage_key,
                    sha256=stored.sha256,
                    byte_size=stored.byte_size,
                    status="uploaded",
                )
                session.add(version)
                session.flush()
                session.refresh(version)
                response = DocumentVersionRead.model_validate(version)

            attributes.update({
                "app.outcome": "success",
                "app.document.version.number": response.version_number,
                "app.document.byte_size": stored.byte_size,
            })
            log_level = logging.INFO
            return response
        except (DocumentNotFound, InvalidUpload, EmptyUpload, UploadTooLarge):
            attributes["app.outcome"] = "rejected"
            log_level = logging.INFO
            raise
        except (SQLAlchemyError, OSError) as error:
            attributes.update({
                "app.outcome": (
                    "database_error"
                    if isinstance(error, SQLAlchemyError)
                    else "storage_error"
                ),
                "error.type": type(error).__name__,
            })
            raise DocumentStorageUnavailable("Document storage unavailable") from None
        finally:
            attributes["app.duration_ms"] = (perf_counter() - started) * 1000
            # A commit error can have an uncertain outcome. Keep the file.
            if file_saved and attributes["app.outcome"] != "success":
                attributes["app.storage.reconciliation_required"] = True
            span.set_attributes(attributes)
            logger.log(
                log_level, "document_versions.upload.completed", extra=attributes
            )


def _get_owned_version_for_update(
    session: Session,
    org_id: UUID,
    version_id: UUID,
) -> DocumentVersion:
    version = session.scalar(
        select(DocumentVersion)
        .join(
            Document,
            DocumentVersion.document_id == Document.id,
        )
        .where(
            DocumentVersion.id == version_id,
            Document.org_id == org_id,
        )
        .with_for_update(of=DocumentVersion)
    )

    if version is None:
        raise DocumentNotFound("Document version not found.")

    return version


def begin_version_processing(
    session: Session,
    org_id: UUID,
    version_id: UUID,
) -> bool:
    with session.begin():
        version = _get_owned_version_for_update(
            session,
            org_id,
            version_id,
        )

        if version.status == "ready":
            return False

        if version.status not in {"uploaded", "failed", "processing"}:
            raise ValueError(
                f"Cannot process a version with status: {version.status}"
            )

        version.status = "processing"
        return True


def mark_version_ready(
    session: Session,
    org_id: UUID,
    version_id: UUID,
) -> None:
    with session.begin():
        version = _get_owned_version_for_update(
            session,
            org_id,
            version_id,
        )

        if version.status != "processing":
            raise ValueError(
                f"Cannot mark version ready from status: {version.status}"
            )

        document = session.scalar(
            select(Document).where(Document.id == version.document_id,
                                   Document.org_id == org_id).with_for_update()
        ) 
        if document is None:
            raise DocumentNotFound("Document not found.")

        version.status = "ready"
        document.active_version_id = version.id


def mark_version_failed(
    session: Session,
    org_id: UUID,
    version_id: UUID,
) -> None:
    with session.begin():
        version = _get_owned_version_for_update(
            session,
            org_id,
            version_id,
        )

        # Never downgrade a completed version because of a later duplicate job.
        if version.status != "ready":
            version.status = "failed"