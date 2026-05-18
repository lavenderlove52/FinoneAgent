from __future__ import annotations

import re


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]")


def extract_terms(text: str) -> list[str]:
    terms = {token.lower() for token in _TOKEN_RE.findall(text)}
    normalized = text.strip().lower()
    if normalized:
        terms.add(normalized)
    return sorted(terms, key=len, reverse=True)


def keyword_score(query: str, *parts: str) -> float:
    haystack = "\n".join(parts).lower()
    if not haystack:
        return 0.0
    score = 0.0
    for term in extract_terms(query):
        count = haystack.count(term)
        if count:
            score += count * max(1.0, len(term) / 4)
    return score

