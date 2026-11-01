"""Offline retrieval benchmark for the fixed ImpactOS demo corpus."""

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR
from app.modules.organizations.dependencies import get_local_org_id
from app.modules.retrieval.hybrid_search import search_active_chunks_hybrid
from app.modules.retrieval.lexical_search import search_active_chunks_lexically
from app.modules.retrieval.vector_search import search_active_chunks
from app.shared.db.session import engine


CASES_PATH = BACKEND_DIR / "evals" / "retrieval_cases.json"
SearchFunction = Callable[..., list[Any]]
METHODS: dict[str, SearchFunction] = {
    "vector": search_active_chunks,
    "lexical": search_active_chunks_lexically,
    "hybrid": search_active_chunks_hybrid,
}


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    """Load the version-controlled benchmark labels, not database identifiers."""
    return json.loads(path.read_text(encoding="utf-8"))


def matches_evidence(result: Any, evidence: dict[str, Any]) -> bool:
    """A result is relevant only when this *chunk* contains every gold anchor."""
    result = getattr(result, "candidate", result)
    if result.document_title != evidence["document_title"]:
        return False

    # Loaders may preserve Markdown line wrapping. It must not turn an otherwise
    # valid phrase such as "invoice reconciliation" into a false negative.
    content = " ".join(result.content.casefold().split())
    return all(
        " ".join(term.casefold().split()) in content
        for term in evidence["required_terms"]
    )


def evaluate_method(
    session: Session,
    org_id: UUID,
    method_name: str,
    search_fn: SearchFunction,
    cases: list[dict[str, Any]],
    *,
    limit: int,
) -> None:
    document_recalls: list[float] = []
    evidence_recalls: list[float] = []
    evidence_reciprocal_ranks: list[float] = []
    evidence_precisions: list[float] = []
    latencies_ms: list[float] = []

    print(f"\n=== {method_name.upper()} @ {limit} ===")

    for case in cases:
        started = perf_counter()
        search_output = search_fn(
            session=session,
            org_id=org_id,
            query_text=case["query"],
            limit=limit,
        )
        results = getattr(search_output, "results", search_output)
        latency_ms = (perf_counter() - started) * 1_000
        latencies_ms.append(latency_ms)

        expected_documents = set(case["expected_documents"])
        returned_documents = {
            getattr(result, "candidate", result).document_title for result in results
        }
        document_recall = len(expected_documents & returned_documents) / len(
            expected_documents
        )
        document_recalls.append(document_recall)

        expected_evidence = case["expected_evidence"]
        evidence_matches = [
            any(matches_evidence(result, evidence) for result in results)
            for evidence in expected_evidence
        ]
        evidence_recall = sum(evidence_matches) / len(expected_evidence)
        evidence_recalls.append(evidence_recall)

        result_is_evidence = [
            any(matches_evidence(result, evidence) for evidence in expected_evidence)
            for result in results
        ]
        first_evidence_rank = next(
            (
                position
                for position, is_evidence in enumerate(result_is_evidence, start=1)
                if is_evidence
            ),
            None,
        )
        evidence_reciprocal_ranks.append(
            1 / first_evidence_rank if first_evidence_rank is not None else 0.0
        )
        evidence_precisions.append(
            sum(result_is_evidence) / len(results) if results else 0.0
        )

        returned = [
            f"{getattr(result, 'candidate', result).document_title}"
            f"#{getattr(result, 'candidate', result).chunk_index}"
            for result in results
        ]
        print(
            f"{case['id']}: doc_recall={document_recall:.2f} "
            f"evidence_recall={evidence_recall:.2f} "
            f"evidence_mrr={evidence_reciprocal_ranks[-1]:.2f} "
            f"latency_ms={latency_ms:.1f} {returned}"
        )

    print(
        "Summary: "
        f"mean_document_recall@{limit}={mean(document_recalls):.3f} "
        f"mean_evidence_recall@{limit}={mean(evidence_recalls):.3f} "
        f"mean_evidence_mrr={mean(evidence_reciprocal_ranks):.3f} "
        f"mean_evidence_precision@{limit}={mean(evidence_precisions):.3f} "
        f"mean_latency_ms={mean(latencies_ms):.1f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--method",
        choices=[*METHODS, "all"],
        default="all",
        help="Retriever to benchmark.",
    )
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    if not 1 <= args.limit <= 50:
        parser.error("--limit must be between 1 and 50")

    cases = load_cases()
    selected_methods = METHODS if args.method == "all" else {args.method: METHODS[args.method]}

    try:
        with Session(engine, expire_on_commit=False) as session:
            org_id = get_local_org_id()
            for method_name, search_fn in selected_methods.items():
                evaluate_method(
                    session,
                    org_id,
                    method_name,
                    search_fn,
                    cases,
                    limit=args.limit,
                )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
