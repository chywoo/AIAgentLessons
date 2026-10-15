from types import SimpleNamespace

from langchain_core.documents import Document

from rag.schemas import EvidenceGrade
from rag.service import AgenticRAGService
from rag.workflow import RAGWorkflow


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.queries = []

    def invoke(self, query):
        self.queries.append(query)
        return self.results.get(query, [])


class FakeChain:
    def __init__(self, fn):
        self.fn = fn

    def invoke(self, data):
        return self.fn(data)


def make_service(results, grade_fn, max_searches=2):
    retriever = FakeRetriever(results)

    chains = SimpleNamespace(
        grade=FakeChain(
            lambda data: EvidenceGrade(sufficient=grade_fn(data))
        ),
        rewrite=FakeChain(
            lambda data: "database failover runbook"
        ),
        answer=FakeChain(
            lambda data: "Production uses PostgreSQL 16. [doc-1]"
        ),
    )

    graph = RAGWorkflow(retriever, chains, max_searches).build()
    return AgenticRAGService(graph), retriever


def test_answer_without_retry():
    docs = [
        Document(
            page_content="Production uses PostgreSQL 16.",
            metadata={"id": "db", "source": "db.md"},
        )
    ]

    service, retriever = make_service(
        {"What DB does production use?": docs},
        grade_fn=lambda data: "PostgreSQL 16" in data["context"],
    )

    result = service.ask("What DB does production use?")

    assert result.status == "answered"
    assert result.search_attempts == 1
    assert result.sources == ["db.md"]
    assert len(retriever.queries) == 1


def test_rewrite_and_retry():
    docs = [
        Document(
            page_content="Promote standby after approval.",
            metadata={"id": "failover", "source": "runbook.md"},
        )
    ]

    service, retriever = make_service(
        {"database failover runbook": docs},
        grade_fn=lambda data: "Promote standby" in data["context"],
    )

    result = service.ask("How do we recover the DB?")

    assert result.status == "answered"
    assert result.search_attempts == 2
    assert retriever.queries == [
        "How do we recover the DB?",
        "database failover runbook",
    ]


def test_stop_when_evidence_missing():
    service, _ = make_service({}, lambda data: False)

    result = service.ask("What is the production database password?")

    assert result.status == "insufficient_evidence"
    assert result.search_attempts == 2
    assert result.sources == []


def test_each_invocation_starts_fresh():
    docs = [
        Document(
            page_content="Production uses PostgreSQL 16.",
            metadata={"id": "db", "source": "db.md"},
        )
    ]

    service, _ = make_service(
        {"What DB does production use?": docs},
        grade_fn=lambda data: True,
    )

    first = service.ask("What DB does production use?")
    second = service.ask("What DB does production use?")

    assert first.search_attempts == 1
    assert second.search_attempts == 1
