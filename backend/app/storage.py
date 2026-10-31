from hashlib import sha256
from typing import BinaryIO
from uuid import UUID

from app.core.config import BACKEND_DIR


UPLOAD_ROOT = BACKEND_DIR / ".data" / "uploads"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class UploadTooLarge(ValueError):
    pass


class EmptyUpload(ValueError):
    pass


def save_upload(
    source: BinaryIO,
    org_id: UUID,
    document_id: UUID,
    version_id: UUID,

) -> tuple[str, str, int]:
    
    storage_key = f"{org_id}/{document_id}/{version_id}/source"
    target = UPLOAD_ROOT / storage_key
    target.parent.mkdir(parents=True, exist_ok=False)

    partial = target.with_name("source.part")
    digest = sha256()
    byte_size = 0

    try:
        with partial.open("xb") as destination:
            while chunk := source.read(1024 * 1024):
                byte_size += len(chunk)

                if byte_size > MAX_UPLOAD_BYTES:
                    raise UploadTooLarge("File exceeds 10 MiB")

                digest.update(chunk)
                destination.write(chunk)

        if byte_size == 0:
            raise EmptyUpload("File is empty")

        partial.rename(target)

    except Exception:
        partial.unlink(missing_ok=True)
        target.parent.rmdir()
        raise

    return storage_key, digest.hexdigest(), byte_size