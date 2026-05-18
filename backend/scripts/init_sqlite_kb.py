from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.config import KnowledgeBaseSettings


SAMPLE_ROWS = [
    (
        1,
        "FinoneAgent MVP SQLite 知识",
        "SQLite 知识库在第一阶段使用 documents(id, title, content, source) 表，"
        "通过参数化 LIKE 查询完成轻量检索。",
        "sample_sqlite",
    ),
    (
        2,
        "DeepResearch 本地检索范围",
        "第一阶段 DeepResearchAgent 只检索 Markdown 与 SQLite，Redis、Neo4j、"
        "GraphRAG、社区搜索和知识图谱探索仅保留接口占位。",
        "sample_sqlite",
    ),
]


def init_db(db_path: Path | None = None) -> Path:
    target = db_path or KnowledgeBaseSettings().sqlite_path
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT OR REPLACE INTO documents (id, title, content, source)
            VALUES (?, ?, ?, ?)
            """,
            SAMPLE_ROWS,
        )
        conn.commit()
    return target


if __name__ == "__main__":
    print(init_db())

