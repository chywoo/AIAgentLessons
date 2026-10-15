from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from rag.config import Settings
from rag.prompts import create_chains
from rag.schemas import RAGResult
from rag.workflow import RAGWorkflow


class AgenticRAGService:
    def __init__(self, graph):
        self.graph = graph

    def ask(self, question: str) -> RAGResult:
        question = question.strip()
        if not question:
            raise ValueError("Question must not be empty")

        state = self.graph.invoke({
            "question": question,
            "search_query": question,
            "documents": [],
            "search_attempts": 0,
            "evidence_sufficient": False,
        })

        return RAGResult(
            answer=state["answer"],
            sources=state["sources"],
            status=state["status"],
            search_attempts=state["search_attempts"],
        )


def build_service(settings: Settings, documents: list[Document]) -> AgenticRAGService:
    model = ChatOpenAI(
        model=settings.model_name,
        base_url=settings.base_url,
        api_key=settings.api_key,
        timeout=settings.llm_timeout,
        max_retries=2,
        temperature=1,
        reasoning_effort="none"
    )

    embeddings = HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )

    vector_store = InMemoryVectorStore.from_documents(documents, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": settings.retrieval_k})

    chains = create_chains(model)
    graph = RAGWorkflow(retriever, chains, settings.max_searches).build()

    return AgenticRAGService(graph)