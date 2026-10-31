from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints


class DocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
    ]
    source_type: Literal["text", "markdown", "pdf", "openapi", "code"]


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    title: str
    source_type: str
    status: str
    created_at: datetime


class DocumentVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    version_number: int
    original_filename: str
    media_type: str
    sha256: str
    byte_size: int
    status: str
    created_at: datetime
