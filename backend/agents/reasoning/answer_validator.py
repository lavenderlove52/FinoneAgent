"""AnswerValidator: lightweight heuristic validation for generated answers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_ERROR_PATTERNS = [
    "抱歉，处理您的问题时遇到了错误",
    "无法获取",
    "无法回答这个问题",
    "没有找到相关信息",
]

_MIN_LENGTH = 50


class AnswerValidator:
    """Validate an answer with simple length and pattern checks."""

    def __init__(
        self,
        keyword_extractor: Callable[[str], list[str]] | None = None,
    ) -> None:
        self._keyword_extractor = keyword_extractor

    def validate(self, query: str, answer: str) -> dict[str, Any]:  # noqa: ARG002
        """
        Returns a dict:
            length: bool           – answer is long enough
            no_error_patterns: bool – answer contains no known error strings
            passed: bool           – all checks pass
        """
        length_ok = len(answer) >= _MIN_LENGTH
        no_error = not any(pat in answer for pat in _ERROR_PATTERNS)
        return {
            "length": length_ok,
            "no_error_patterns": no_error,
            "passed": length_ok and no_error,
        }
