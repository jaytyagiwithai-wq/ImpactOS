"""Integration coverage for the active-version retrieval boundary.

Run explicitly because this test requires the local PostgreSQL + pgvector stack:
    $env:IMPACTOS_RUN_INTEGRATION = "1"
    uv run pytest tests/test_active_version_filter.py -q
"""

import os
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.documents.models import Document, DocumentVersion
from app.modules.ingestion.models import Chunk
from app.modules.organizations.models import Organization
from app.modules.retrieval.lexical_search import search_active_chunks_lexically
from app.shared.db.session import engine


pytestmark = pytest.mark.skipif(
    os.getenv("IMPACTOS_RUN_INTEGRATION") != "1",
    reason="requires PostgreSQL; set IMPACTOS_RUN_INTEGRATION=1",
)


def test_lexical_search_excludes_ready_but_inactive_document_versions():
    """A ready old version must never leak through the active-version filter."""
    org_id = uuid4()
    document_id = uuid4()
    old_version_id = uuid4()
    active_version_id = uuid4()

    with Session(engine, expire_on_commit=False) as session:
        try:
            with session.begin():
                session.add(Organization(id=org_id, name="Active version test"))
                session.flush()  # No ORM relationship exists to order this FK insert.

                document = Document(
                    id=document_id,
                    org_id=org_id,
                    title="Versioned webhook contract",
                    source_type="markdown",
                    status="ready",
                )
                session.add(document)
                session.flush()  # Versions reference this document.

                session.add_all(
                    [
                        DocumentVersion(
                            id=old_version_id,
                            document_id=document_id,
                            version_number=1,
                            original_filename="contract-v1.md",
                            media_type="text/markdown",
                            storage_key=f"integration/{org_id}/v1",
                            sha256="1" * 64,
                            byte_size=1,
                            status="ready",
                        ),
                        DocumentVersion(
                            id=active_version_id,
                            document_id=document_id,
                            version_number=2,
                            original_filename="contract-v2.md",
                            media_type="text/markdown",
                            storage_key=f"integration/{org_id}/v2",
                            sha256="2" * 64,
                            byte_size=1,
                            status="ready",
                        ),
                    ]
                )
                session.flush()  # The document can now safely point to version two.

                session.add_all(
                    [
                        Chunk(
                            version_id=old_version_id,
                            chunk_index=0,
                            content="obsoletepolicytoken only exists in the old contract.",
                            token_count=8,
                            chunker_version="test",
                            tokenizer="test",
                            max_tokens=20,
                            overlap_tokens=0,
                        ),
                        Chunk(
                            version_id=active_version_id,
                            chunk_index=0,
                            content="activepolicytoken only exists in the current contract.",
                            token_count=8,
                            chunker_version="test",
                            tokenizer="test",
                            max_tokens=20,
                            overlap_tokens=0,
                        ),
                    ]
                )
                document.active_version_id = active_version_id

            old_results = search_active_chunks_lexically(
                session=session,
                org_id=org_id,
                query_text="obsoletepolicytoken",
            )
            active_results = search_active_chunks_lexically(
                session=session,
                org_id=org_id,
                query_text="activepolicytoken",
            )

            assert old_results == []
            assert [result.version_id for result in active_results] == [active_version_id]
            assert all(result.version_id != old_version_id for result in active_results)
        finally:
            with session.begin():
                session.execute(delete(Chunk).where(Chunk.version_id.in_([old_version_id, active_version_id])))
                session.execute(
                    Document.__table__.update()
                    .where(Document.id == document_id)
                    .values(active_version_id=None)
                )
                session.execute(
                    delete(DocumentVersion).where(
                        DocumentVersion.id.in_([old_version_id, active_version_id])
                    )
                )
                session.execute(delete(Document).where(Document.id == document_id))
                session.execute(delete(Organization).where(Organization.id == org_id))
