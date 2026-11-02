from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from app.shared.db.session import get_session
from app.modules.organizations.dependencies import get_local_org_id
from app.modules.retrieval.hybrid_search import search_active_chunks_hybrid
from app.modules.answering.context import select_evidence
from app.core.config import get_settings
from app.modules.answering.service import answer_question
from app.modules.answering.openai_provider import get_answer_provider


router = APIRouter(prefix="/v1/answers", tags=["answers"])

class AnswerRequest(BaseModel):
    model_config= ConfigDict(extra="forbid")

    query_text: str = Field(min_length=2, max_length=500)

class AnswerCitationResponse(BaseModel):
    evidence_id: int
    chunk_id: str
    document_title: str
    version_number: int
    chunk_index: int

class AnswerResponse(BaseModel):
    ranking_mode: str
    status: str
    answer: str
    citations: list[AnswerCitationResponse]
    unknowns: list[str]


@router.post("", response_model=AnswerResponse)
def answer(
    payload:AnswerRequest,
    session: Session = Depends(get_session),
    org_id = Depends(get_local_org_id)

) -> AnswerResponse:

    outcome = search_active_chunks_hybrid(
        session=session,
        org_id=org_id,
        query_text=payload.query_text,
        limit=5,
    )

    context = select_evidence(
        outcome.results,
        max_context_tokens=get_settings().answer_context_token_budget,
    )

    grounded_answer = answer_question(
        question=payload.query_text,
        context=context,
        provider=get_answer_provider(),
    )



    evidence_by_id = {
        item.evidence_id: item
        for item in context.items
    }

    citations = [
        AnswerCitationResponse(
            evidence_id=citation.evidence_id,
            chunk_id=evidence_by_id[citation.evidence_id].chunk_id,
            document_title=evidence_by_id[citation.evidence_id].document_title,
            version_number=evidence_by_id[citation.evidence_id].version_number,
            chunk_index=evidence_by_id[citation.evidence_id].chunk_index,
        )
        for citation in grounded_answer.citations
    ]


    return AnswerResponse(
        ranking_mode=outcome.ranking_mode,
        status=grounded_answer.status,
        answer=grounded_answer.answer,
        citations=citations,
        unknowns=grounded_answer.unknowns,
    )

