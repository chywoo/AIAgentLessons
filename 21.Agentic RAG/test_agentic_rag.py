from langchain_core.documents import Document
from agentic_rag import AgenticRAGService, EvidenceGrade


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
    service = AgenticRAGService.__new__(AgenticRAGService)
    service.retriever = FakeRetriever(results)
    service.max_searches = max_searches

    service.grade_chain = FakeChain(
        lambda data: EvidenceGrade(sufficient=grade_fn(data))
    )
    service.rewrite_chain = FakeChain(
        lambda data: "database failover runbook"
    )
    service.answer_chain = FakeChain(
        lambda data: "Production uses PostgreSQL 16. [doc-1]"
    )

    service.graph = service._build_graph()
    return service


def test_answer_without_retry():
    docs = [
        Document(
            page_content="Production uses PostgreSQL 16.",
            metadata={"id": "db", "source": "db.md"},
        )
    ]

    service = make_service(
        {"What DB does production use?": docs},
        grade_fn=lambda data: "PostgreSQL 16" in data["context"],
    )

    result = service.ask("What DB does production use?")

    assert result.status == "answered"
    assert result.search_attempts == 1
    assert result.sources == ["db.md"]


def test_rewrite_and_retry():
    docs = [
        Document(
            page_content="Promote standby after approval.",
            metadata={"id": "failover", "source": "runbook.md"},
        )
    ]

    service = make_service(
        {"database failover runbook": docs},
        grade_fn=lambda data: "Promote standby" in data["context"],
    )

    result = service.ask("How do we recover the DB?")

    assert result.status == "answered"
    assert result.search_attempts == 2
    assert service.retriever.queries == [
        "How do we recover the DB?",
        "database failover runbook",
    ]


def test_stop_when_evidence_missing():
    service = make_service(
        {},
        grade_fn=lambda data: False,
        max_searches=2,
    )

    result = service.ask("What is the database password?")

    assert result.status == "insufficient_evidence"
    assert result.search_attempts == 2
    assert result.sources == []
