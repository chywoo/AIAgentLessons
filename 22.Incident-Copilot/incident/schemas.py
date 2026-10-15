from typing import Literal, NotRequired, TypedDict

from pydantic import BaseModel, Field


class IncidentAnalysis(BaseModel):
    summary: str = Field(description="Incident summary")
    probable_cause: str = Field(description="Most likely cause based on evidence")
    evidence: list[str] = Field(description="Supporting metrics, logs, and runbooks")
    recommended_action: str = Field(description="Proposed remediation")
    confidence: Literal["low", "medium", "high"]


class IncidentState(TypedDict):
    incident_id: str
    service: str
    description: str
    analysis: NotRequired[dict]
    proposed_action: NotRequired[str]
    approved: NotRequired[bool]
    execution_result: NotRequired[str]
    final_report: NotRequired[str]