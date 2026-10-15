from dataclasses import dataclass
from typing import NotRequired, TypedDict

from langchain_core.documents import Document
from pydantic import BaseModel, Field


class RAGState(TypedDict):
    question: str
    search_query: NotRequired[str]
    documents: NotRequired[list[Document]]
    search_attempts: NotRequired[int]
    evidence_sufficient: NotRequired[bool]
    answer: NotRequired[str]
    sources: NotRequired[list[str]]
    status: NotRequired[str]


class EvidenceGrade(BaseModel):
    sufficient: bool = Field(
        description="Whether the evidence fully supports answering the question."
    )


@dataclass
class RAGResult:
    answer: str
    sources: list[str]
    status: str
    search_attempts: int
