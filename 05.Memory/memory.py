import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Memory:
    id: int
    content: str
    category: str
    created_at: str


class MemoryStore:

    def __init__(
        self,
        db_path: str = "agent_memory.db",
    ):
        self.db_path = Path(db_path)

        self._initialize()

    def _connect(self):
        return sqlite3.connect(
            self.db_path
        )

    def _initialize(self):

        with self._connect() as conn:

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            conn.commit()

    def add(
        self,
        content: str,
        category: str = "general",
    ) -> int|None:

        created_at = datetime.now().isoformat()

        with self._connect() as conn:

            cursor = conn.execute(
                """
                INSERT INTO memories (
                    content,
                    category,
                    created_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    content,
                    category,
                    created_at,
                ),
            )

            conn.commit()

            return cursor.lastrowid

    def list_all(
        self,
        limit: int = 20,
    ) -> list[Memory]:

        with self._connect() as conn:

            rows = conn.execute(
                """
                SELECT
                    id,
                    content,
                    category,
                    created_at
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            Memory(
                id=row[0],
                content=row[1],
                category=row[2],
                created_at=row[3],
            )
            for row in rows
        ]

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Memory]:

        pattern = f"%{query}%"

        with self._connect() as conn:

            rows = conn.execute(
                """
                SELECT
                    id,
                    content,
                    category,
                    created_at
                FROM memories
                WHERE content LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    pattern,
                    limit,
                ),
            ).fetchall()

        return [
            Memory(
                id=row[0],
                content=row[1],
                category=row[2],
                created_at=row[3],
            )
            for row in rows
        ]