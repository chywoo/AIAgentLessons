from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct, Distance


class VectorMemory:
    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "agent_memories",
    ):
        print(
            f"[VectorMemory] Connecting to Qdrant at {url} and using collection '{collection_name}'"
        )
        self.client = QdrantClient(url=url, trust_env=False)
        self.collection_name = collection_name
        self.model = SentenceTransformer("BAAI/bge-m3")

        test_vector = self.embed("dimension test")
        self.vector_size = len(test_vector)
        self._create_collection_if_not_exists()

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def _create_collection_if_not_exists(self):
        print(self.client.http)
        collections = self.client.get_collections().collections

        names = {collection.name for collection in collections}

        if self.collection_name in names:
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size, distance=Distance.COSINE
            ),
        )

    def add(
        self,
        memory_id: int,
        content: str,
        category: str,
        memory_key: str | None,
        importance: float,
        status: str,
        updated_at: str,
    ):

        vector = self.embed(content)

        point = PointStruct(
            id=memory_id,
            vector=vector,
            payload={
                "memory_id": memory_id,
                "memory_key": memory_key,
                "content": content,
                "category": category,
                "importance": importance,
                "status": status,
                "updated_at": updated_at,
            },
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    # -------------------------------------------------
    # Semantic search
    # -------------------------------------------------
    def search(
        self, query: str, limit: int = 5, score_threshold: float = 0.55
    ) -> list[dict]:
        query_vector = self.embed(query)

        result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )

        memories = []

        for point in result.points:
            memories.append(
                {
                    "id": point.id,
                    "score": point.score,
                    "content": point.payload.get("content"),
                    "category": point.payload.get("category"),
                }
            )

        return memories

    def set_status(self, memory_id: int, status: str):

        self.client.set_payload(
            collection_name=self.collection_name,
            payload={"status": status},
            points=[memory_id],
        )
