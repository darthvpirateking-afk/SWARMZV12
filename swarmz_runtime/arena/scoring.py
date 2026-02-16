"""
arena/scoring.py – Deterministic scoring strategies for arena candidates.

All scoring is pure-function, deterministic: same inputs → same outputs.
"""

from __future__ import annotations

from typing import Any, Dict


def score_candidate(response: str, prompt: str,
                    strategy: str = "length_quality") -> float:
    """Score a candidate response deterministically.

    Strategies:
      - length_quality: weighted combination of response length and structure
      - length_only: purely based on response length (normalized)
    """
    if strategy == "length_only":
        return _score_length(response)
    return _score_length_quality(response, prompt)


def _score_length(response: str) -> float:
    """Normalize response length to 0..1 (caps at 2000 chars)."""
    length = len(response.strip())
    return min(length / 2000.0, 1.0)


def _score_length_quality(response: str, prompt: str) -> float:
    """Combined scoring: length (40%), structure (30%), relevance (30%)."""
    text = response.strip()
    if not text:
        return 0.0

    # Length component (0..1, caps at 2000)
    length_score = min(len(text) / 2000.0, 1.0)

    # Structure component: reward paragraphs, lists, variety
    lines = text.split("\n")
    non_empty = [l for l in lines if l.strip()]
    structure_score = min(len(non_empty) / 10.0, 1.0)

    # Relevance component: how many prompt words appear in response
    prompt_words = set(prompt.lower().split())
    response_words = set(text.lower().split())
    if prompt_words:
        overlap = len(prompt_words & response_words) / len(prompt_words)
    else:
        overlap = 0.5
    relevance_score = min(overlap, 1.0)

    score = 0.4 * length_score + 0.3 * structure_score + 0.3 * relevance_score
    return round(score, 6)


def rank_candidates(candidates: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Sort candidates by score descending, assign deterministic ranks.

    Tie-breaking: higher score first, then lower worker_index, then lexical id.
    """
    sorted_cands = sorted(
        candidates,
        key=lambda c: (-c.get("score", 0.0),
                       c.get("worker_index", 0),
                       c.get("id", "")),
    )
    for i, c in enumerate(sorted_cands, start=1):
        c["rank"] = i
    return sorted_cands
