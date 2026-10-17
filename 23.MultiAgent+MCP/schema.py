from pydantic import BaseModel, Field


class InvestigationResult(BaseModel):
    agent_name: str
    summary: str
    evidence: list[str] = Field(default_factory=list)
    probable_causes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
