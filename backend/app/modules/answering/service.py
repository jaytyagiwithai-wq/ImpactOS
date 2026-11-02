from app.modules.answering.context import EvidenceContext,render_evidence_context
from app.modules.answering.schemas import GroundedAnswer
from typing import Protocol


class CitationValidationError(ValueError):
    pass

class AnswerProvider(Protocol):
    def generate(
        self,
        *,
        question: str,
        evidence_text: str,
    ) -> GroundedAnswer:
        pass


def validate_citations(
        answer: GroundedAnswer,
        context: EvidenceContext
) -> GroundedAnswer:
    
    allowed_ids = {item.evidence_id for item in context.items}
    cited_ids = {citation.evidence_id for citation in answer.citations}

    invalid_ids = cited_ids - allowed_ids

    if invalid_ids:
        raise CitationValidationError(
            f"Answer cited evidence that was not supplied: {sorted(invalid_ids)}"
        )

    if answer.status == "answered" and not answer.citations:
        raise CitationValidationError(
            "An answered response must cite at least one evidence item."
        )

    return answer



def answer_question(
        question: str,
        context: EvidenceContext,
        provider: AnswerProvider
)-> GroundedAnswer:

    if not question:
        raise ValueError("Question cannot be blank.")

    if not context.items:
        return GroundedAnswer(
            status="insufficient_evidence",
            answer="No retrieval evidence is available for this question",
            citations=[],
            unknowns=["No evidence was retrieved."]
        )
    answer  = provider.generate(
        question=question,
        evidence_text=render_evidence_context(context=context)
    )

    return validate_citations(answer, context)


     