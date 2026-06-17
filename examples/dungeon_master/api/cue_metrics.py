"""Deterministic cue-uptake metrics for DM Final Cut prose (FR-505).

These helpers are intentionally pure and string-based. They provide a stable,
non-LLM witness for whether structured per-turn cues (dialogue/expression) are
surfaced in chapter prose.
"""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")
_WORD = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "onto",
    "over",
    "under",
    "then",
    "than",
    "when",
    "what",
    "where",
    "while",
    "your",
    "their",
    "there",
    "have",
    "has",
    "had",
    "were",
    "was",
    "are",
    "his",
    "her",
    "its",
    "our",
    "but",
    "not",
    "too",
}


def round_robin_paragraph_fraction(prose: str, cast_names: list[str]) -> float:
    """Fraction of cast-bearing paragraphs in fixed-order round-robin runs.

    Paragraphs are split on blank lines. The denominator is paragraphs that
    mention at least one cast name. Each paragraph's "leading cast" is the first
    cast name to appear by character offset. A paragraph contributes to the
    numerator when it belongs to a contiguous run (length >= 3) whose leading-cast
    indices advance by +1 modulo cast length.
    """
    cast = [normalize_text(n) for n in cast_names if normalize_text(n)]
    if not cast:
        return 0.0

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", prose or "") if p.strip()]
    leading: list[int] = []
    for p in paragraphs:
        p_norm = normalize_text(p)
        first_idx = -1
        first_pos = None
        for i, name in enumerate(cast):
            pos = p_norm.find(name)
            if pos >= 0 and (first_pos is None or pos < first_pos):
                first_pos = pos
                first_idx = i
        if first_idx >= 0:
            leading.append(first_idx)

    denom = len(leading)
    if denom < 3:
        return 0.0

    covered = 0
    i = 0
    n = len(cast)
    while i < denom:
        j = i
        while j + 1 < denom and leading[j + 1] == (leading[j] + 1) % n:
            j += 1
        run_len = j - i + 1
        if run_len >= 3:
            covered += run_len
        i = j + 1

    return covered / denom


def normalize_text(text: str) -> str:
    """Lowercase and collapse whitespace to a canonical comparison form."""
    return _WS.sub(" ", (text or "").strip().lower())


def _tokens(text: str) -> list[str]:
    return _WORD.findall(normalize_text(text))


def _expression_parts(expr: str) -> tuple[set[str], set[str]]:
    toks = [t for t in _tokens(expr) if len(t) >= 3 and t not in _STOPWORDS]
    unigrams = set(toks)
    bigrams = {f"{a} {b}" for a, b in zip(toks, toks[1:], strict=False)}
    return unigrams, bigrams


def cue_uptake(
    prose: str,
    dialogue_snippets: list[str],
    expression_cues: list[str],
) -> dict[str, float | int]:
    """Compute deterministic cue uptake rates and the combined score.

    Dialogue match: normalized exact substring.
    Expression match: any cue bigram present OR >=2 cue unigrams present.
    Combined score: arithmetic mean of dialogue and expression uptake.
    """
    prose_norm = normalize_text(prose)
    prose_uni = set(_tokens(prose_norm))
    prose_bi = {
        f"{a} {b}"
        for a, b in zip(
            list(_tokens(prose_norm)), list(_tokens(prose_norm))[1:], strict=False
        )
    }

    d_pool = [
        normalize_text(s) for s in dialogue_snippets if len(normalize_text(s)) >= 8
    ]
    d_total = len(d_pool)
    d_match = sum(1 for s in d_pool if s and s in prose_norm)
    d_rate = (d_match / d_total) if d_total else 0.0

    e_pool = [s for s in expression_cues if normalize_text(s)]
    e_total = len(e_pool)
    e_match = 0
    for cue in e_pool:
        cue_uni, cue_bi = _expression_parts(cue)
        has_bigram = any(bg in prose_bi for bg in cue_bi)
        uni_hits = len(cue_uni & prose_uni)
        if has_bigram or uni_hits >= 2:
            e_match += 1
    e_rate = (e_match / e_total) if e_total else 0.0

    return {
        "dialogue_total": d_total,
        "dialogue_matched": d_match,
        "dialogue_uptake": d_rate,
        "expression_total": e_total,
        "expression_matched": e_match,
        "expression_uptake": e_rate,
        "cue_uptake": 0.5 * d_rate + 0.5 * e_rate,
    }
