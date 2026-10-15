from langchain_core.documents import Document


def document_key(doc: Document) -> str:
    if doc.metadata.get("id"):
        return str(doc.metadata["id"])

    return f"{doc.metadata.get('source', 'unknown')}::{doc.page_content}"


def merge_documents(existing: list[Document], incoming: list[Document]) -> list[Document]:
    merged = {}
    for doc in [*existing, *incoming]:
        merged[document_key(doc)] = doc

    return list(merged.values())


def format_documents(documents: list[Document]) -> str:
    if not documents:
        return "NO DOCUMENTS FOUND"

    return "\n\n".join(
        f"[doc-{i}] Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
        for i, doc in enumerate(documents, start=1)
    )


def document_sources(documents: list[Document]) -> list[str]:
    return list(dict.fromkeys(
        str(doc.metadata.get("source", "unknown")) for doc in documents
    ))