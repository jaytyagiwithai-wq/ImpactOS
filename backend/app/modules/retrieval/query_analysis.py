import re

TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9_]+(?:[.-][A-Za-z0-9_]+)*"

)

QUESTION_WORDS = {
    "what",
    "which",
    "who",
    "where",
    "when",
    "why",
    "how",
    "can",
    "could",
    "should",
    "would",
    "do",
    "does",
    "did",
    "is",
    "are",
    "was",
    "were",
    "a",
    "an",
    "the",
    "and",
    "or",
    "if",
    "find",
    "explain",
    "tell",
    "me",
}


def build_broad_lexical_query(query_text: str) -> str:
    """Create an OR-based fallback query from meaningful user terms."""
    tokens = TOKEN_PATTERN.findall(query_text)

    terms: list[str] = []
    seen: set[str] = set()

    for token in tokens:
        normalized = token.casefold()

        if normalized in QUESTION_WORDS:
            continue

        if normalized in seen:
            continue

        terms.append(token)
        seen.add(normalized)

    return " OR ".join(terms)