from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

from openai import OpenAI

from backend.config import LLMSettings


Message = dict[str, str]


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM client cannot be configured from the environment."""


class LLMClient:
    """Single entry point for all FinoneAgent model calls."""

    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings.from_env()
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if not self.settings.api_key:
            raise LLMConfigurationError(
                "请先设置环境变量 AIGW_API_KEY 或 OPENAI_API_KEY"
            )
        if self._client is None:
            self._client = OpenAI(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
            )
        return self._client

    def complete(
        self,
        messages: Iterable[Message],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        response = self.client.chat.completions.create(
            model=model or self.settings.model,
            messages=list(messages),
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def stream_chat(
        self,
        messages: Iterable[Message],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> Iterator[str]:
        stream = self.client.chat.completions.create(
            model=model or self.settings.model,
            messages=list(messages),
            temperature=temperature,
            stream=True,
            **kwargs,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content

