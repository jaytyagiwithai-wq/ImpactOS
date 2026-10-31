from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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
    DocumentVersionRead,
)
from app.modules.organizations.dependencies import get_local_org_id
from app.shared.db.session import get_session
from app.shared.storage.base import EmptyUpload, UploadStorage, UploadTooLarge
from app.shared.storage.dependencies import get_upload_storage

router = APIRouter(prefix="/v1/documents", tags=["documents"])


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
