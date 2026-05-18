from __future__ import annotations

from typing import Any

from backend.retrievers.base import RetrievalResult


class UnsupportedBackendError(NotImplementedError):
    pass


class UnsupportedRetriever:
    """Explicit stub for post-MVP backends such as Redis, Neo4j, and GraphRAG."""

    def __init__(self, name: str) -> None:
        self.name = name

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        del query, top_k, filters
        raise UnsupportedBackendError(
            f"{self.name} is a placeholder in the MVP and is not connected."
        )


RedisCacheBackend = UnsupportedRetriever
Neo4jGraphRetriever = UnsupportedRetriever
GraphRAGRetriever = UnsupportedRetriever
CommunitySearchRetriever = UnsupportedRetriever
KnowledgeGraphExplorer = UnsupportedRetriever

