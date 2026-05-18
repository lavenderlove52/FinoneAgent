from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from backend.retrievers.base import RetrievalResult
from backend.retrievers.keyword import extract_terms, keyword_score


class SQLiteRetriever:
    name = "sqlite"

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        del filters
        if not self.db_path.exists():
            return []

        terms = extract_terms(query)
        if not terms:
            return []

        where = " OR ".join(["title LIKE ? OR content LIKE ?"] * len(terms))
        params: list[str | int] = []
        for term in terms:
            like = f"%{term}%"
            params.extend([like, like])

        sql = (
            "SELECT id, title, content, source FROM documents "
            f"WHERE {where} LIMIT ?"
        )
        params.append(max(top_k * 5, top_k))

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()

        results = [
            RetrievalResult(
                source_type="sqlite",
                source_id=str(row["id"]),
                title=row["title"],
                content=row["content"],
                score=keyword_score(query, row["title"], row["content"]),
                metadata={"source": row["source"], "db_path": str(self.db_path)},
            )
            for row in rows
        ]
        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]

