from hashlib import sha256
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from app.core.config import BACKEND_DIR
from app.shared.storage.base import EmptyUpload, StoredUpload, UploadTooLarge

UPLOAD_ROOT = BACKEND_DIR / ".data" / "uploads"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class LocalFileStorage:
    backend = "local"

    def __init__(
        self,
        root: Path = UPLOAD_ROOT,
        max_upload_bytes: int = MAX_UPLOAD_BYTES,
    ) -> None:
        if max_upload_bytes <= 0:
            raise ValueError("max_upload_bytes must be positive")
        self.root = root
        self.max_upload_bytes = max_upload_bytes

    def save_upload(
        self,
        source: BinaryIO,
        org_id: UUID,
        document_id: UUID,
        version_id: UUID,
    ) -> StoredUpload:
        storage_key = f"{org_id}/{document_id}/{version_id}/source"
        target = self.root / storage_key
        target.parent.mkdir(parents=True, exist_ok=False)
        partial = target.with_name("source.part")
        digest = sha256()
        byte_size = 0

        try:
            with partial.open("xb") as destination:
                while chunk := source.read(1024 * 1024):
                    byte_size += len(chunk)
                    if byte_size > self.max_upload_bytes:
                        raise UploadTooLarge("File exceeds the upload size limit")
                    digest.update(chunk)
                    destination.write(chunk)

            if byte_size == 0:
                raise EmptyUpload("File is empty")

            partial.rename(target)
        except Exception:
            partial.unlink(missing_ok=True)
            target.parent.rmdir()
            raise

        return StoredUpload(storage_key, digest.hexdigest(), byte_size)
