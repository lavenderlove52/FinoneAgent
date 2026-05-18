from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class RetrievalResult:
    source_type: str
    source_id: str
    title: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class Retriever(Protocol):
    name: str

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Return ranked retrieval results for a user query."""

