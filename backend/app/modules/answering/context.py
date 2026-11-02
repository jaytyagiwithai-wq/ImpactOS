from app.modules.retrieval.reranking import RankedSearchResult
from dataclasses import dataclass
import tiktoken

TOKENIZER = tiktoken.get_encoding("cl100k_base")

@dataclass
class EvidenceItem:
    evidence_id: int
    document_title:str
    version_number: int
    chunk_id: str
    chunk_index: int
    content: str
    token_count: int
    rerank_score: float | None



@dataclass
class EvidenceContext:
    items: list[EvidenceItem]
    total_tokens: int
    token_budget: int


def select_evidence(
        results: list[RankedSearchResult],
        max_context_tokens: int = 4_000,

)-> EvidenceContext:

    if max_context_tokens < 1:
        raise ValueError("Context token budget must be positive")

    items: list[EvidenceItem] = []
    total_tokens = 0

    for result in results:
        candidate = result.candidate
        token_count = len(TOKENIZER.encode(candidate.content))

        if total_tokens + token_count > max_context_tokens:
            continue

        items.append(
            EvidenceItem(
                evidence_id=len(items)+1,
                document_title=candidate.document_title,
                version_number=candidate.version_number,
                chunk_id=str(candidate.chunk_id),
                chunk_index=candidate.chunk_index,
                content=candidate.content,
                token_count=token_count,
                rerank_score=result.rerank_score
            )
        )

        total_tokens += token_count
    
    return EvidenceContext(
        items=items,
        total_tokens=total_tokens,
        token_budget=max_context_tokens
    )


def render_evidence_context(context: EvidenceContext) -> str:
    if not context.items:
        return  "No retrieved evidence is available"

    blocks = []


    for item in context.items:
        blocks.append(
           f"[E{item.evidence_id}]\n"
            f"Source: {item.document_title}\n"
            f"Version: {item.version_number}\n"
            f"Chunk: {item.chunk_index}\n\n"
            f"{item.content.strip()}"
        )


    return "\n\n---\n\n".join(blocks)
