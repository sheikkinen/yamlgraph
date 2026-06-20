"""Deterministic resolved-fact reversal detector for DM v2 (FR-542 B).

The state-blind successor witness: a fact a chapter RESOLVES (its committed
``chapter_memory.resolved_events``) must not be silently un-resolved by the next
chapter, and a ``forbidden_regression`` it asserts must not be contradicted. The
seam ledger already records these lines, but they are only rendered into prose
context where a 0.7-temperature sampler can ignore them (the 10029-BC food-bundle
reversal: secured in Ch3, "unclaimed" in Ch4).

This is the *fact-persistence* seam, distinct from the lifecycle/resurrection
family (``gap_detectors.seam_precondition_gap``, FR-507/509/510/526) and from the
entrance seam (``seam_entrance``, FR-538/539). It runs over committed ledger lines
only -- a closed antonym set about a SHARED subject -- so it is deterministic,
roster/closed-set bounded, and never reaches an LLM or ``turn_ops``.

Split into its own leaf (FR-536 size doctrine): ``gap_detectors`` sits at the
450-line ceiling, so the new detector lives here rather than crammed over the gate.
"""

from __future__ import annotations

import re

# The closed antonym set (FR-542 B, FROZEN). Exactly three pairs: a fourth case is
# the ``regex_fourth_exclusion`` trap -> escalate to the Phase-2 LLM tier, never
# widen this tuple. Each side carries only minimal morphological variants of the
# one canonical token, matched case-folded as whole words.
_FACT_ANTONYMS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    # secured <-> unclaimed
    (
        ("secured", "claimed", "stowed"),
        ("unclaimed", "unsecured", "abandoned"),
    ),
    # present <-> absent
    (
        ("present", "arrived"),
        ("absent", "gone", "departed", "missing"),
    ),
    # closed <-> reopened
    (
        ("closed", "sealed"),
        ("reopened", "unsealed"),
    ),
)

_ANTONYM_TOKENS: frozenset[str] = frozenset(
    token for pair in _FACT_ANTONYMS for side in pair for token in side
)

# Function words and generic predicates that never identify a fact's subject.
_SUBJECT_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "into",
        "onto",
        "from",
        "with",
        "this",
        "that",
        "than",
        "they",
        "them",
        "their",
        "there",
        "then",
        "were",
        "have",
        "been",
        "back",
        "again",
        "after",
        "before",
        "fully",
        "kept",
        "stays",
        "still",
        "over",
        "down",
        "drifted",
        "sat",
        "against",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _subject_tokens(line: str) -> set[str]:
    """Significant subject words of a ledger line (>=4 chars, not antonym/stopword)."""
    return {
        token
        for token in _TOKEN_RE.findall(str(line or "").lower())
        if len(token) >= 4
        and token not in _SUBJECT_STOPWORDS
        and token not in _ANTONYM_TOKENS
    }


def _asserted_side(line: str) -> tuple[int, int] | None:
    """``(pair_index, side)`` of the first antonym token in ``line``; ``None`` if none."""
    tokens = set(_TOKEN_RE.findall(str(line or "").lower()))
    for pair_index, (side_a, side_b) in enumerate(_FACT_ANTONYMS):
        if tokens & set(side_a):
            return (pair_index, 0)
        if tokens & set(side_b):
            return (pair_index, 1)
    return None


def _antonym_reversals(
    prior_lines: list[str], later_lines: list[str], reason: str
) -> list[dict]:
    """Lines where ``later`` asserts the opposite antonym side of ``prior``, same subject.

    A reversal requires (a) the prior line asserts one side of a frozen antonym
    pair, (b) a later line asserts the *opposite* side of the *same* pair, and
    (c) the two lines share at least one subject token -- so opposite sides about
    different subjects (a secured gate vs an unclaimed boat) never compose a false
    reversal.
    """
    gaps: list[dict] = []
    for prior in prior_lines:
        prior_side = _asserted_side(prior)
        if prior_side is None:
            continue
        prior_subjects = _subject_tokens(prior)
        if not prior_subjects:
            continue
        for later in later_lines:
            later_side = _asserted_side(later)
            if later_side is None:
                continue
            if later_side[0] != prior_side[0] or later_side[1] == prior_side[1]:
                continue
            shared = prior_subjects & _subject_tokens(later)
            if not shared:
                continue
            gaps.append(
                {
                    "subject": sorted(shared)[0],
                    "prior_fact": str(prior).strip(),
                    "reversed_fact": str(later).strip(),
                    "antonym_pair": prior_side[0],
                    "reason": reason,
                }
            )
    return gaps


def _lines(raw: object) -> list[str]:
    """Non-empty string lines of a committed ledger field."""
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item or "").strip()]


def _delta_texts(raw: object) -> list[str]:
    """Render character_state_deltas to 'name to_state' lines for subject matching."""
    out: list[str] = []
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, dict):
            text = f"{item.get('name', '')} {item.get('to_state', '')}".strip()
            if text:
                out.append(text)
    return out


def fact_reversal_gap(prev_card: dict, card: dict) -> dict:
    """Flag a resolved-fact reversal / forbidden-regression violation across a pair.

    Diffs the committed ``chapter_memory`` of two consecutive chapters: a
    ``resolved_event`` from ``prev_card`` the successor's committed ledger
    (resolved events or open threads) contradicts by the frozen antonym set, and a
    ``forbidden_regression`` from ``prev_card`` the successor's ledger or character
    deltas contradicts. Pure, deterministic, closed-set; returns
    ``{gap_count, gaps:[{subject, prior_fact, reversed_fact, antonym_pair, reason}]}``.
    """
    prev_mem = (prev_card or {}).get("chapter_memory") or {}
    mem = (card or {}).get("chapter_memory") or {}

    later_facts = _lines(mem.get("resolved_events")) + _lines(mem.get("open_threads"))
    gaps = _antonym_reversals(
        _lines(prev_mem.get("resolved_events")),
        later_facts,
        "resolved_event_reversal",
    )
    gaps += _antonym_reversals(
        _lines(prev_mem.get("forbidden_regressions")),
        later_facts + _delta_texts(mem.get("character_state_deltas")),
        "forbidden_regression_violation",
    )
    return {"gap_count": len(gaps), "gaps": gaps}
