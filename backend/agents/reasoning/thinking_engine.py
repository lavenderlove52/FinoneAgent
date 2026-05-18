"""ThinkingEngine: manages multi-round iterative reasoning state."""

from __future__ import annotations

import re
import traceback
import logging
from typing import Any

from backend.llm_client import LLMClient
from backend.agents.reasoning.prompts import (
    BEGIN_SEARCH_QUERY,
    END_SEARCH_QUERY,
    BEGIN_SEARCH_RESULT,
    END_SEARCH_RESULT,
    REASON_PROMPT,
)

logger = logging.getLogger(__name__)


class ThinkingEngine:
    """Manages multi-round reasoning state without LangChain dependencies."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self.all_reasoning_steps: list[str] = []
        self.msg_history: list[dict[str, str]] = []
        self.executed_search_queries: list[str] = []

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def initialize_with_query(self, query: str) -> None:
        """Reset state and seed message history with the user question."""
        self.all_reasoning_steps = []
        self.msg_history = [{"role": "user", "content": f'问题:"{query}"\n'}]
        self.executed_search_queries = []

    # ------------------------------------------------------------------
    # History management
    # ------------------------------------------------------------------

    def add_reasoning_step(self, content: str) -> None:
        self.all_reasoning_steps.append(content)

    def add_ai_message(self, content: str) -> None:
        self.msg_history.append({"role": "assistant", "content": content})

    def add_human_message(self, content: str) -> None:
        self.msg_history.append({"role": "user", "content": content})

    def update_continue_message(self) -> None:
        """Append or extend the last user message to request continued reasoning."""
        if not self.msg_history:
            return
        last = self.msg_history[-1]
        if last["role"] == "assistant":
            self.add_human_message("继续基于新信息进行推理分析。\n")
        else:
            last["content"] = last["content"] + "\n\n继续基于新信息进行推理分析。\n"

    # ------------------------------------------------------------------
    # Query generation via LLM
    # ------------------------------------------------------------------

    def generate_next_query(self) -> dict[str, Any]:
        """
        Call the LLM with current msg_history and extract search queries.

        Returns a dict with keys:
            status: "has_query" | "answer_ready" | "empty" | "error" | "no_query"
            content: str | None
            queries: list[str]
        """
        messages = [{"role": "system", "content": REASON_PROMPT}] + self.msg_history
        try:
            query_think = self.llm_client.complete(messages)

            # Strip internal <think>...</think> tags if present
            query_think = re.sub(r"<think>.*?</think>", "", query_think, flags=re.DOTALL)

            if not query_think.strip():
                return {"status": "empty", "content": None, "queries": []}

            self.add_reasoning_step(query_think)

            queries = self._extract_queries(query_think)

            if not queries:
                if "**回答**" in query_think or "足够的信息" in query_think:
                    return {"status": "answer_ready", "content": query_think, "queries": []}
                return {"status": "no_query", "content": query_think, "queries": []}

            return {"status": "has_query", "content": query_think, "queries": queries}

        except Exception as exc:
            error_msg = f"generate_next_query error: {exc}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return {"status": "error", "content": None, "queries": []}

    # ------------------------------------------------------------------
    # Query dedup
    # ------------------------------------------------------------------

    def has_executed_query(self, query: str) -> bool:
        return query in self.executed_search_queries

    def add_executed_query(self, query: str) -> None:
        self.executed_search_queries.append(query)

    # ------------------------------------------------------------------
    # Reasoning history utilities
    # ------------------------------------------------------------------

    def prepare_truncated_reasoning(self) -> str:
        """
        Return a token-efficient subset of reasoning steps:
        first step + last 4 steps + any step containing search tags.
        """
        steps = self.all_reasoning_steps
        if not steps:
            return ""
        if len(steps) <= 5:
            return "\n\n".join(f"Step {i + 1}: {s}" for i, s in enumerate(steps)).strip()

        # Collect (original_index, step) pairs
        important: list[tuple[int, str]] = [(0, steps[0])]

        tail_start = max(1, len(steps) - 4)
        for i in range(tail_start, len(steps)):
            important.append((i, steps[i]))

        for i in range(1, tail_start):
            if BEGIN_SEARCH_QUERY in steps[i] or BEGIN_SEARCH_RESULT in steps[i]:
                important.append((i, steps[i]))

        important.sort(key=lambda x: x[0])

        result = ""
        prev_idx = -1
        for idx, step in important:
            if idx > prev_idx + 1:
                result += "...\n\n"
            result += f"Step {idx + 1}: {step}\n\n"
            prev_idx = idx
        return result.strip()

    # ------------------------------------------------------------------
    # Tag removal
    # ------------------------------------------------------------------

    def remove_query_tags(self, text: str) -> str:
        pattern = re.escape(BEGIN_SEARCH_QUERY) + r".*?" + re.escape(END_SEARCH_QUERY)
        return re.sub(pattern, "", text, flags=re.DOTALL)

    def remove_result_tags(self, text: str) -> str:
        pattern = re.escape(BEGIN_SEARCH_RESULT) + r".*?" + re.escape(END_SEARCH_RESULT)
        return re.sub(pattern, "", text, flags=re.DOTALL)

    # ------------------------------------------------------------------
    # Full thinking output
    # ------------------------------------------------------------------

    def get_full_thinking(self) -> str:
        parts = []
        for step in self.all_reasoning_steps:
            clean = self.remove_query_tags(step)
            clean = self.remove_result_tags(clean)
            parts.append(clean)
        return "<think>\n" + "\n\n".join(parts) + "\n</think>"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_queries(self, text: str) -> list[str]:
        pattern = re.escape(BEGIN_SEARCH_QUERY) + r"(.*?)" + re.escape(END_SEARCH_QUERY)
        matches = re.findall(pattern, text, flags=re.DOTALL)
        return [m.strip() for m in matches if m.strip()]
