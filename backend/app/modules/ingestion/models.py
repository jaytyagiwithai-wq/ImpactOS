from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.db.base import Base
from pgvector.sqlalchemy import VECTOR

from sqlalchemy import Computed, Index
from sqlalchemy.dialects.postgresql import TSVECTOR

'''
PostgreSQL can store it because pgvector adds a new data type to PostgreSQL called vector.

'''

class Chunk(Base):
    __tablename__="chunks"
    __table_args__=(
        Index(
            "ix_chunks_textsearch",
            "textsearch",
            postgresql_using="gin",
        ),
         UniqueConstraint(
            "version_id", "chunk_index",
            name="uq_chunks_version_index",
        ),
        CheckConstraint(
            "chunk_index >= 0",
            name="ck_chunks_index",
        ),
        CheckConstraint(
            "token_count > 0 AND token_count <= max_tokens",
            name="ck_chunks_token_count",
        ),
        CheckConstraint(
            "max_tokens > 0 AND overlap_tokens >= 0 "
            "AND overlap_tokens < max_tokens",
            name="ck_chunks_budget",
        ),
        CheckConstraint(
        "(embedding IS NULL AND embedding_model IS NULL) OR "
        "(embedding IS NOT NULL AND embedding_model IS NOT NULL)",
        name="ck_chunks_embedding_pair",
),
    
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="RESTRICT"),    )

    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)

    token_count: Mapped[int] = mapped_column(Integer)

    chunker_version: Mapped[str] = mapped_column(String(64))
    tokenizer: Mapped[str] = mapped_column(String(64))
    max_tokens: Mapped[int] = mapped_column(Integer)
    overlap_tokens: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(1536), nullable=True)
    textsearch: Mapped[str] = mapped_column(
        TSVECTOR, Computed(
            "to_tsvector('english',content)",
            persisted=True
        ),nullable=False
    )
    embedding_model: Mapped[str | None] = mapped_column(String(64),nullable=True,)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )



