from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.retrievers.base import RetrievalResult
from backend.retrievers.keyword import keyword_score


@dataclass(frozen=True)
class MarkdownChunk:
    source_id: str
    title: str
    content: str
    path: Path
    heading: str
    chunk_index: int


class MarkdownRetriever:
    name = "markdown"

    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        del filters
        ranked: list[RetrievalResult] = []
        for chunk in self._iter_chunks():
            score = keyword_score(query, chunk.title, chunk.heading, chunk.content)
            if score <= 0:
                continue
            ranked.append(
                RetrievalResult(
                    source_type="markdown",
                    source_id=chunk.source_id,
                    title=chunk.title,
                    content=chunk.content,
                    score=score,
                    metadata={
                        "path": str(chunk.path),
                        "heading": chunk.heading,
                        "chunk_index": chunk.chunk_index,
                    },
                )
            )
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]

    def _iter_chunks(self) -> list[MarkdownChunk]:
        if not self.root_path.exists():
            return []

        chunks: list[MarkdownChunk] = []
        for path in sorted(self.root_path.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            chunks.extend(self._split_file(path, text))
        return chunks

    def _split_file(self, path: Path, text: str) -> list[MarkdownChunk]:
        chunks: list[MarkdownChunk] = []
        title = path.stem
        heading = title
        paragraph_lines: list[str] = []
        chunk_index = 0

        def flush() -> None:
            nonlocal chunk_index
            content = "\n".join(paragraph_lines).strip()
            paragraph_lines.clear()
            if not content:
                return
            chunks.append(
                MarkdownChunk(
                    source_id=f"{path.name}:{chunk_index}",
                    title=title,
                    content=content,
                    path=path,
                    heading=heading,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1

        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if line.startswith("#"):
                flush()
                heading = line.lstrip("#").strip() or title
                if heading and title == path.stem:
                    title = heading
                continue
            if not line.strip():
                flush()
                continue
            paragraph_lines.append(line)
        flush()
        return chunks

