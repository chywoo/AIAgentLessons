from typing import Literal

from pydantic import BaseModel, Field


class IncidentInput(BaseModel):
    incident_id: str = Field(min_length=1)
    service: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,62}$")
    description: str = Field(min_length=10, max_length=4000)


class MetricsFinding(BaseModel):
    summary: str
    probable_cause: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]


class RunbookFinding(BaseModel):
    summary: str
    runbook_ids: list[str] = Field(default_factory=list)
    recommended_action: Literal[
        "inspect_database_connections",
        "review_deployment",
        "no_action",
    ]
    rationale: str


class ActionPlan(BaseModel):
    action: Literal[
        "inspect_database_connections",
        "review_deployment",
        "no_action",
    ]
    target_service: str
    rationale: str