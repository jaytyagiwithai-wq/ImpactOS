from argparse import ArgumentParser

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.demo_corpus import DEMO_DOCUMENTS
from app.model_registry import load_metadata
from app.modules.documents.models import Document, DocumentVersion
from app.modules.ingestion.service import ingest_version
from app.modules.organizations.dependencies import get_local_org_id
from app.shared.db.session import engine


def main() -> None:
    parser = ArgumentParser(
        description="Ingest uploaded or failed versions of the local demo corpus."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List candidate versions without parsing or embedding them.",
    )
    args = parser.parse_args()

    load_metadata()
    org_id = get_local_org_id()
    titles = [title for title, _ in DEMO_DOCUMENTS]

    try:
        with Session(engine) as session:
            candidates = session.execute(
                select(DocumentVersion.id, Document.title)
                .join(Document, DocumentVersion.document_id == Document.id)
                .where(
                    Document.org_id == org_id,
                    Document.title.in_(titles),
                    DocumentVersion.status.in_(("uploaded", "failed")),
                )
                .order_by(Document.title, DocumentVersion.version_number)
            ).all()

        if not candidates:
            print("No demo versions need ingestion.")
            return

        for version_id, title in candidates:
            print(f"Candidate: {title} ({version_id})")

        if args.dry_run:
            print(f"Dry run complete: {len(candidates)} version(s) would be ingested.")
            return

        succeeded = 0
        failed = 0

        for version_id, title in candidates:
            try:
                # Each version gets its own session so a failure cannot poison
                # the next document's transaction state.
                with Session(engine, expire_on_commit=False) as session:
                    chunk_count = ingest_version(
                        session=session,
                        org_id=org_id,
                        version_id=version_id,
                    )
                print(f"Ready: {title} ({chunk_count} chunks)")
                succeeded += 1
            except Exception as error:
                print(f"Failed: {title} ({type(error).__name__})")
                failed += 1

        print(f"Demo ingestion complete: {succeeded} ready, {failed} failed.")
        if failed:
            raise SystemExit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
