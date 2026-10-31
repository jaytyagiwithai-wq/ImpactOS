from functools import lru_cache

from app.shared.storage.base import UploadStorage
from app.shared.storage.local import LocalFileStorage


@lru_cache
def get_upload_storage() -> UploadStorage:
    """Select the storage implementation at the application boundary."""
    return LocalFileStorage()
