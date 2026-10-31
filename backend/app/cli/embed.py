from argparse import ArgumentParser
from uuid import UUID

from sqlalchemy.orm import Session

from app.model_registry import load_metadata
from app.modules.ingestion.service import embed_version
from app.modules.organizations.dependencies import get_local_org_id
from app.shared.db.session import engine


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("version_id", type=UUID)
    args = parser.parse_args()

    load_metadata()
    org_id = get_local_org_id()

    try:
        with Session(engine, expire_on_commit=False) as session:
            count = embed_version(
                session=session,
                org_id=org_id,
                version_id=args.version_id,
            )

        print(f"Embedding completed: {count} chunks.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
