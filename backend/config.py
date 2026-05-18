from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parent
KNOWLEDGE_BASE_ROOT = BACKEND_ROOT / "knowledge_base"


@dataclass(frozen=True)
class LLMSettings:
    """Runtime settings for the OpenAI-compatible AIGW endpoint."""

    api_key: str | None
    base_url: str = "https://aigw.fosunwealth.com/v1"
    model: str = "claude-opus-4.6"

    @classmethod
    def from_env(cls) -> "LLMSettings":
        return cls(
            api_key=os.getenv("AIGW_API_KEY") or os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("AIGW_BASE_URL", cls.base_url),
            model=os.getenv("AIGW_MODEL", cls.model),
        )


@dataclass(frozen=True)
class KnowledgeBaseSettings:
    md_path: Path = KNOWLEDGE_BASE_ROOT / "md"
    sqlite_path: Path = KNOWLEDGE_BASE_ROOT / "sqlite" / "knowledge.db"

