from dataclasses import dataclass
from typing import BinaryIO, Protocol
from uuid import UUID


class UploadTooLarge(ValueError):
    pass


class EmptyUpload(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StoredUpload:
    storage_key: str
    sha256: str
    byte_size: int


class UploadStorage(Protocol):
    backend: str

    def save_upload(
        self,
        source: BinaryIO,
        org_id: UUID,
        document_id: UUID,
        version_id: UUID,
    ) -> StoredUpload: ...
