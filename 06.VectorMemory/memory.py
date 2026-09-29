import sqlite3
import math
from datetime import datetime
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import AgentConfig
from vector_memory import VectorMemory


@dataclass
class Memory:
    id: int
    memory_key: str | None
    content: str
    category: str

    importance: float

    status: str

    created_at: str
    updated_at: str

    expires_at: str | None

    access_count: int


class MemoryStore:

    def __init__(
        self,
        db_path: str = "agent_memory.db",
    ):
        config = AgentConfig()

        self.db_path = Path(db_path)
        self.vector_memory = VectorMemory(config.vector_db)

        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):

        with self._connect() as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    memory_key TEXT,

                    content TEXT NOT NULL,
                    category TEXT NOT NULL,

                    importance REAL NOT NULL DEFAULT 0.5,

                    status TEXT NOT NULL DEFAULT 'active',

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    expires_at TEXT,

                    access_count INTEGER NOT NULL DEFAULT 0
                )
                """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_memories_key
                ON memories(memory_key)
                """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_memories_status
                ON memories(status)
                """)

            conn.commit()

    def add(
        self,
        content: str,
        category: str = "general",
        memory_key: str | None = None,
        importance: float = 0.5,
        expires_at: str | None = None,
    ) -> int | None:

        now = datetime.now().isoformat()

        importance = max(0.0, min(1.0, importance))

        existing = None

        if memory_key:
            existing = self.find_active_by_key(memory_key)

        # Same key + same content
        if existing and existing.content.strip() == content.strip():
            return existing.id

        #
        # Same key but changed value:
        # old memory becomes superseded.
        #
        if existing:
            with self._connect() as conn:

                conn.execute(
                    """
                    UPDATE memories
                    SET
                        status = 'superseded',
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (now, existing.id),
                )

                conn.commit()

            self.vector_memory.set_status(
                existing.id,
                "superseded",
            )

        #
        # Insert new canonical memory
        #
        with self._connect() as conn:

            cursor = conn.execute(
                """
                INSERT INTO memories (
                    memory_key,
                    content,
                    category,
                    importance,
                    status,
                    created_at,
                    updated_at,
                    expires_at,
                    access_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_key,
                    content,
                    category,
                    importance,
                    "active",
                    now,
                    now,
                    expires_at,
                    0,
                ),
            )

            memory_id = cursor.lastrowid

            conn.commit()

            self.vector_memory.add(
                memory_id=memory_id,
                content=content,
                category=category,
                memory_key=memory_key,
                importance=importance,
                status="active",
                updated_at=now,
            )

            return memory_id

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        candidates = self.vector_memory.search(
            query=query,
            limit=20,
        )

        results = []

        for candidate in candidates:

            memory = self.find_active_by_key(candidate["id"])

            if memory is None:
                continue

            if memory.status != "active":
                continue

            if self.is_expired(memory):
                continue

            recency = calculate_recency_score(memory.updated_at)

            final_score = calculate_final_score(
                semantic_score=candidate["score"],
                importance=memory.importance,
                recency_score=recency,
            )

            results.append(
                {
                    "id": memory.id,
                    "content": memory.content,
                    "semantic_score": candidate["score"],
                    "importance": memory.importance,
                    "recency": recency,
                    "score": final_score,
                }
            )

        results.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return results[:limit]

    def find_active_by_key(self, memory_key: str) -> Memory | None:

        with self._connect() as conn:

            row = conn.execute(
                """
                SELECT
                    id,
                    memory_key,
                    content,
                    category,
                    importance,
                    status,
                    created_at,
                    updated_at,
                    expires_at,
                    access_count
                FROM memories

                WHERE memory_key = ?
                AND status = 'active'

                ORDER BY updated_at DESC

                LIMIT 1
                """,
                (memory_key,),
            ).fetchone()

        if row is None:
            return None

        return Memory(*row)

    def is_expired(self, memory: Memory) -> bool:
        if memory.expires_at is None:
            return False

        expires = datetime.fromisoformat(memory.expires_at)

        return datetime.now() >= expires


def calculate_recency_score(
    updated_at: str,
    half_life_days: float = 30,
) -> float:

    updated = datetime.fromisoformat(updated_at)

    age = datetime.now() - updated

    age_days = max(
        age.total_seconds() / 86400,
        0.0,
    )

    return math.exp(-math.log(2) * age_days / half_life_days)
