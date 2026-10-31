from hashlib import sha256
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR
from app.model_registry import load_metadata
from app.modules.documents.models import Document, DocumentVersion
from app.modules.documents.schemas import DocumentCreate
from app.modules.documents.service import create_document, upload_document_version
from app.modules.organizations.dependencies import get_local_org_id
from app.shared.db.session import engine
from app.shared.storage.local import LocalFileStorage


CORPUS_DIR = BACKEND_DIR / "evals" / "corpus"

DEMO_DOCUMENTS = (
    ("Payments Webhook Contract", "payments-webhook-contract.md"),
    ("Billing Adapter Consumer", "billing-adapter.md"),
    ("AcmePay Integration Guide", "acmepay-integration-guide.md"),
    ("Enterprise API Breaking-Change Policy", "api-breaking-change-policy.md"),
    ("Incident INC-184: Payment Reconciliation Mismatch", "incident-inc-184.md"),
    ("Analytics Consumer Inventory", "analytics-consumer.md"),
)


def main() -> None:
    load_metadata()
    org_id = get_local_org_id()
    storage = LocalFileStorage()

    created = 0
    skipped = 0

    try:
        with Session(engine, expire_on_commit=False) as session:
            for title, filename in DEMO_DOCUMENTS:
                path = CORPUS_DIR / filename
                digest = sha256(path.read_bytes()).hexdigest()

                document_id = session.scalar(
                    select(Document.id).where(
                        Document.org_id == org_id,
                        Document.title == title,
                    )
                )

                if document_id is None:
                    # The service owns its transaction, so end the read-only
                    # transaction created by the lookup before calling it.
                    session.rollback()
                    document = create_document(
                        session=session,
                        org_id=org_id,
                        payload=DocumentCreate(
                            title=title,
                            source_type="markdown",
                        ),
                    )
                    document_id = document.id

                existing_version = session.scalar(
                    select(DocumentVersion.id).where(
                        DocumentVersion.document_id == document_id,
                        DocumentVersion.sha256 == digest,
                    )
                )
                if existing_version is not None:
                    print(f"Skipped {title}: version already uploaded.")
                    skipped += 1
                    session.rollback()
                    continue

                # upload_document_version also owns its transaction.
                session.rollback()
                with path.open("rb") as source:
                    version = upload_document_version(
                        session=session,
                        storage=storage,
                        org_id=org_id,
                        document_id=document_id,
                        source=source,
                        filename=filename,
                        media_type="text/markdown",
                    )

                print(f"Uploaded {title}: {version.id}")
                created += 1
    finally:
        engine.dispose()

    print(f"Demo seed complete: {created} uploaded, {skipped} skipped.")


if __name__ == "__main__":
    main()
