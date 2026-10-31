"""The composition root for ORM discovery, shared by startup and Alembic."""

from sqlalchemy import MetaData

from app.shared.db.base import Base


def load_metadata() -> MetaData:
    # Explicit imports register each module's tables with the one shared Base.
    from app.modules.documents import models as documents_models  # noqa: F401
    from app.modules.organizations import models as organization_models  # noqa: F401
    from app.modules.ingestion import models as ingestion_models  # noqa: F401

    return Base.metadata
