from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('registered','queued','processing','ready','failed')",
            name="status",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(32))
    '''
    If retrieval filters only DocumentVersion.status == "ready", it could search both old and new policy content. That is bad

    '''
    active_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("document_versions.id", ondelete="RESTRICT"),nullable=True,index=True)
    status: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "version_number", name="uq_document_versions_number"
        ),
        UniqueConstraint("storage_key", name="uq_document_versions_storage_key"),
        CheckConstraint("version_number > 0", name="ck_document_versions_number"),
        CheckConstraint("byte_size > 0", name="ck_document_versions_size"),
        CheckConstraint(
            "status IN ('uploaded', 'processing', 'ready', 'failed')",
            name="ck_document_versions_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="RESTRICT"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    original_filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))
    sha256: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(24), server_default="uploaded")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
