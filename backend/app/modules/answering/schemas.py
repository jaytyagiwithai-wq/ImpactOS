from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: int


#forces every future LLM response into one of two honest outcomes:


class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status : Literal["answered","insufficient_evidence"]
    answer: str
    citations: list[Citation]
    unknowns: list[str]
