import json
import logging

from langgraph.graph import StateGraph, START, END

from rag.documents import document_sources, format_documents, merge_documents
from rag.schemas import RAGState


logger = logging.getLogger(__name__)


class RAGWorkflow:
    def __init__(self, retriever, chains, max_searches: int = 2):
        if max_searches < 1:
            raise ValueError("max_searches must be >= 1")

        self.retriever = retriever
        self.chains = chains
        self.max_searches = max_searches

    def retrieve(self, state: RAGState) -> dict:
        query = state.get("search_query", state["question"])
        new_docs = self.retriever.invoke(query)
        documents = merge_documents(state.get("documents", []), new_docs)
        attempts = state.get("search_attempts", 0) + 1

        logger.info(json.dumps({
            "event": "retrieve",
            "attempt": attempts,
            "document_count": len(documents),
        }))

        return {
            "search_query": query,
            "documents": documents,
            "search_attempts": attempts,
        }

    def grade(self, state: RAGState) -> dict:
        if not state.get("documents"):
            return {"evidence_sufficient": False}

        result = self.chains.grade.invoke({
            "question": state["question"],
            "context": format_documents(state["documents"]),
        })

        return {"evidence_sufficient": result.sufficient}

    def rewrite(self, state: RAGState) -> dict:
        query = self.chains.rewrite.invoke({
            "question": state["question"],
            "search_query": state["search_query"],
            "context": format_documents(state.get("documents", [])),
        }).strip()

        return {"search_query": query or state["question"]}

    def answer(self, state: RAGState) -> dict:
        documents = state["documents"]
        answer = self.chains.answer.invoke({
            "question": state["question"],
            "context": format_documents(documents),
        })

        return {
            "answer": answer,
            "sources": document_sources(documents),
            "status": "answered",
        }

    def not_found(self, state: RAGState) -> dict:
        return {
            "answer": "Insufficient evidence in the available internal documents.",
            "sources": [],
            "status": "insufficient_evidence",
        }

    def route(self, state: RAGState) -> str:
        if state["evidence_sufficient"]:
            return "answer"

        return "rewrite" if state["search_attempts"] < self.max_searches else "not_found"

    def build(self):
        builder = StateGraph(RAGState)

        builder.add_node("retrieve", self.retrieve)
        builder.add_node("grade", self.grade)
        builder.add_node("rewrite", self.rewrite)
        builder.add_node("answer", self.answer)
        builder.add_node("not_found", self.not_found)

        builder.add_edge(START, "retrieve")
        builder.add_edge("retrieve", "grade")

        builder.add_conditional_edges("grade", self.route, {
            "answer": "answer",
            "rewrite": "rewrite",
            "not_found": "not_found",
        })

        builder.add_edge("rewrite", "retrieve")
        builder.add_edge("answer", END)
        builder.add_edge("not_found", END)

        return builder.compile()