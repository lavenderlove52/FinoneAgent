"""QueryGenerator: sub-query decomposition and follow-up query generation."""

from __future__ import annotations

import ast
import json
import logging
import re

from backend.llm_client import LLMClient
from backend.agents.reasoning.prompts import (
    FOLLOWUP_QUERY_PROMPT,
    SUB_QUERY_PROMPT,
)

logger = logging.getLogger(__name__)

_MULTI_HYPOTHESIS_PROMPT = (
    '为以下问题生成2-3个可能的假设，这些假设应该代表不同角度或思路：\n\n'
    '问题: "{query}"\n\n'
    "每个假设应该:\n"
    "1. 不同于其他假设\n"
    "2. 提供一种可能的思考方向\n"
    "3. 有助于深入分析问题\n\n"
    "以列表形式返回假设，每个假设简短明了。"
)


def _safe_parse_list(text: str, fallback: list[str]) -> list[str]:
    """Try json.loads then ast.literal_eval on the first [...] block found."""
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if not match:
        return fallback
    raw = match.group(0)
    for parser in (json.loads, ast.literal_eval):
        try:
            result = parser(raw)
            if isinstance(result, list):
                return [str(item) for item in result if str(item).strip()]
        except Exception:
            continue
    return fallback


class QueryGenerator:
    """Generates sub-queries, follow-up queries, and multiple hypotheses."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_sub_queries(self, original_query: str) -> list[str]:
        """Decompose the original question into at most three sub-queries."""
        try:
            prompt = SUB_QUERY_PROMPT.format(original_query=original_query)
            response = self.llm_client.complete(
                [
                    {"role": "system", "content": "你是一个问题分解助手。"},
                    {"role": "user", "content": prompt},
                ]
            )
            return _safe_parse_list(response, [original_query])
        except Exception as exc:
            logger.warning("generate_sub_queries failed: %s", exc)
            return [original_query]

    def generate_followup_queries(
        self, original_query: str, retrieved_info: list[str]
    ) -> list[str]:
        """Return up to 2 follow-up queries, or [] when no further search is needed."""
        if not retrieved_info:
            return []
        try:
            info_text = "\n\n".join(retrieved_info[-3:])
            prompt = FOLLOWUP_QUERY_PROMPT.format(
                original_query=original_query,
                retrieved_info=info_text,
            )
            response = self.llm_client.complete(
                [
                    {"role": "system", "content": "你是一个搜索策略助手。"},
                    {"role": "user", "content": prompt},
                ]
            )
            return _safe_parse_list(response, [])
        except Exception as exc:
            logger.warning("generate_followup_queries failed: %s", exc)
            return []

    def generate_multiple_hypotheses(self, query: str) -> list[str]:
        """Generate 2-3 alternative hypotheses / angles for the query."""
        try:
            prompt = _MULTI_HYPOTHESIS_PROMPT.format(query=query)
            response = self.llm_client.complete(
                [
                    {"role": "system", "content": "你是一个假设生成助手。"},
                    {"role": "user", "content": prompt},
                ]
            )

            # Try list parsing first
            parsed = _safe_parse_list(response, [])
            if parsed:
                return parsed[:3]

            # Fall back to numbered / dash list extraction
            numbered = re.findall(r"\d+\.\s*(.*?)(?=\d+\.|$)", response, re.DOTALL)
            if numbered:
                return [s.strip() for s in numbered if s.strip()][:3]

            dash = re.findall(r"-\s*(.*?)(?=-|$)", response, re.DOTALL)
            if dash:
                return [s.strip() for s in dash if s.strip()][:3]

            lines = [
                ln.strip()
                for ln in response.split("\n")
                if ln.strip() and len(ln.strip()) > 10
            ]
            return lines[:3]
        except Exception as exc:
            logger.warning("generate_multiple_hypotheses failed: %s", exc)
            return []
