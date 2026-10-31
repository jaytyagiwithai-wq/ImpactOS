from argparse import ArgumentParser

from sqlalchemy.orm import Session

from app.model_registry import load_metadata
from app.modules.organizations.dependencies import get_local_org_id
from app.modules.retrieval.vector_search import search_active_chunks
from app.shared.db.session import engine


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    load_metadata()
    org_id = get_local_org_id()

    try:
        with Session(engine, expire_on_commit=False) as session:
            results = search_active_chunks(
                session=session,
                org_id=org_id,
                query_text=args.query,
                limit=args.limit,
            )

        for rank, result in enumerate(results, start=1):
            print(
                f"\n[{rank}] {result.document_title} "
                f"v{result.version_number} "
                f"chunk={result.chunk_index} "
                f"distance={result.distance:.4f}"
            )
            print(result.content)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()