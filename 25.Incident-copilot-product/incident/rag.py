import json
import os

from langchain.tools import tool
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

COLLECTION = "incident_runbooks"


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
        model_kwargs={
            "device": os.getenv("EMBEDDING_DEVICE", "cpu")
        },
    )


def seed_runbooks() -> None:
    documents = [
        Document(
            page_content=(
                "Database connection pool exhaustion: "
                "Inspect active connections, slow queries, "
                "connection leaks, and recent deployments. "
                "Require approval before changing pool settings."
            ),
            metadata={"source_id": "RB-DB-001", "version": "1.0"},
        ),
        Document(
            page_content=(
                "High API latency: Compare p95 latency to baseline. "
                "Inspect error rates, application logs, "
                "and downstream dependencies."
            ),
            metadata={"source_id": "RB-API-001", "version": "1.0"},
        ),
        Document(
            page_content=(
                "Deployment rollback: Verify correlation between "
                "deployment and incident. Obtain approval before "
                "rollback. Monitor error rate after the change."
            ),
            metadata={"source_id": "RB-DEPLOY-001", "version": "1.0"},
        ),
    ]

    QdrantVectorStore.from_documents(
        documents=documents,
        embedding=get_embeddings(),
        url=os.environ["QDRANT_URL"],
        collection_name=COLLECTION,
        force_recreate=True,
    )


def build_runbook_tool():
    store = QdrantVectorStore.from_existing_collection(
        embedding=get_embeddings(),
        url=os.environ["QDRANT_URL"],
        collection_name=COLLECTION,
    )

    @tool
    def search_runbooks(query: str) -> str:
        """Search incident runbooks and return cited procedures."""
        docs = store.similarity_search(query, k=3)

        return json.dumps({
            "items": [
                {
                    "source_id": doc.metadata["source_id"],
                    "version": doc.metadata.get("version"),
                    "content": doc.page_content,
                }
                for doc in docs
            ]
        })

    return search_runbooks

if __name__ == "__main__":
    # Ingesting runbooks
    from dotenv import load_dotenv;

    load_dotenv()
    seed_runbooks()