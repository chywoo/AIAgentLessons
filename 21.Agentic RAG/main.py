import logging

from dotenv import load_dotenv
from langchain_core.documents import Document

from rag.config import Settings
from rag.service import build_service


def main():
    load_dotenv()
    logging.basicConfig(level=logging.CRITICAL)

    documents = [
        Document(
            page_content="Production uses PostgreSQL 16. The primary cluster is prod-pg.",
            metadata={"id": "db-1", "source": "database-architecture.md"},
        ),
        Document(
            page_content=(
                "If the database primary fails, verify standby health and replication lag. "
                "Obtain on-call approval before promoting a standby."
            ),
            metadata={"id": "runbook-1", "source": "db-failover-runbook.md"},
        ),
        Document(
            page_content=(
                "After failover, update the database connection endpoint "
                "and monitor service errors."
            ),
            metadata={"id": "runbook-2", "source": "post-failover-runbook.md"},
        ),
    ]

    service = build_service(Settings(), documents)

    questions = [
        "What DB does production use?",
        "What should we do when the primary database fails?",
        "What is the production database password?",
    ]

    for question in questions:
        result = service.ask(question)
        print(f"\nQuestion: {question}")
        print(f"Status: {result.status}")
        print(f"Answer: {result.answer}")
        print(f"Sources: {result.sources}")
        print(f"Search attempts: {result.search_attempts}")


if __name__ == "__main__":
    main()