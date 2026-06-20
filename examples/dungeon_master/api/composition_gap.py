"""Outline-time chapter composition gate for DM v2 (FR-540).

The turn loop is a *local sampler*: it guarantees turn N follows turn N-1, nothing
more. Cross-chapter coherence rests on the inherited ``world_state`` ledger, which
the partitioner never sees and cannot author toward -- so two adjacent chapters can
each be locally coherent yet fail to COMPOSE (10029-BC Ch2->Ch3: isolated-grief
close into assembled-crowd open, no transition).

This module is the partitioner-facing seam check. It reads the authored
``entry_state``/``exit_state`` chapter contracts (1-2 sentence configurations) and
flags an adjacent pair whose configurations contradict by a FROZEN antonym set --
deterministic, no LLM, roster-bounded for the presence concept.

Scope carve (FR-540 J1 -- avoid ``false_duplicate``): this is the
SOCIAL/relational-configuration seam (who-is-together, present/absent). The
PHYSICAL lethal-seam (a carried-alive actor killed with no reposition beat) is the
distinct concern of :func:`gap_detectors.seam_precondition_gap`, which reads beats
and committed ``world_state`` -- different fields, different boundary. This module
NEVER inspects beats or the ledger, so a pure lethal-seam case is structurally
outside its reach.

Frozen antonym set (FR-540 J2): exactly two concepts --
``together <-> scattered`` (group configuration, scene-level) and
``present <-> absent`` (a roster actor's presence, subject-bound). A fourth
special-case branch is the ``regex_fourth_exclusion`` trap -> escalate to a
deferred LLM tier, never widen this set.
"""

from __future__ import annotations

import re

# Frozen antonym concepts (FR-540 J2). ``subject_bound`` togglees whether a shared
# roster name is required: the group configuration (together/scattered) is a
# scene-level fact; an actor's presence (present/absent) is bound to that actor, so
# "Arnulf gone" then "Hilde present" (different actors) must NOT cross-fire.
_COMPOSITION_ANTONYMS: tuple[dict, ...] = (
    {
        "concept": "together-scattered",
        "subject_bound": False,
        "a": frozenset({"together", "assembled", "gathered", "reunited"}),
        "b": frozenset({"scattered", "apart", "separated", "alone", "isolated"}),
    },
    {
        "concept": "present-absent",
        "subject_bound": True,
        "a": frozenset({"present", "arrived", "returned"}),
        "b": frozenset({"absent", "gone", "departed", "missing"}),
    },
)


def _has_any(text: str, tokens: frozenset[str]) -> bool:
    """Whether ``text`` contains any token as a whole word (case-insensitive)."""
    low = (text or "").lower()
    return any(re.search(rf"\b{re.escape(tok)}\b", low) for tok in tokens)


def _roster(chapters: list[dict]) -> set[str]:
    """The lowercased union of every chapter's authored ``cast`` (FR-540 roster bound)."""
    out: set[str] = set()
    for ch in chapters:
        for name in ch.get("cast") or []:
            token = str(name or "").strip().lower()
            if token:
                out.add(token)
    return out


def _shared_subject(exit_state: str, entry_state: str, roster: set[str]) -> bool:
    """Whether a roster name appears in BOTH states (the presence subject bound)."""
    el = (exit_state or "").lower()
    nl = (entry_state or "").lower()
    return any(name in el and name in nl for name in roster)


def composition_gap(chapters: list[dict]) -> dict:
    """Flag adjacent chapters whose entry/exit configurations contradict.

    For each adjacent pair ``(N, N+1)`` with BOTH an ``exit_state`` on N and an
    ``entry_state`` on N+1 (absent contracts degrade additively -- no gap), checks
    every frozen antonym concept: a contradiction is one state asserting one side
    and the other state asserting the opposite side of the SAME concept. The
    presence concept additionally requires a shared roster subject. Pure; never
    mutates ``chapters``; no LLM.

    Returns ``{gap_count, gaps:[{from_chapter, to_chapter, concept, exit_state,
    entry_state}]}`` (1-based chapter numbers).
    """
    roster = _roster(chapters)
    gaps: list[dict] = []
    for i in range(len(chapters) - 1):
        exit_state = str(chapters[i].get("exit_state") or "").strip()
        entry_state = str(chapters[i + 1].get("entry_state") or "").strip()
        if not exit_state or not entry_state:
            continue
        for concept in _COMPOSITION_ANTONYMS:
            exit_a = _has_any(exit_state, concept["a"])
            exit_b = _has_any(exit_state, concept["b"])
            entry_a = _has_any(entry_state, concept["a"])
            entry_b = _has_any(entry_state, concept["b"])
            contradiction = (exit_a and entry_b) or (exit_b and entry_a)
            if not contradiction:
                continue
            if concept["subject_bound"] and not _shared_subject(
                exit_state, entry_state, roster
            ):
                continue
            gaps.append(
                {
                    "from_chapter": i + 1,
                    "to_chapter": i + 2,
                    "concept": concept["concept"],
                    "exit_state": exit_state,
                    "entry_state": entry_state,
                }
            )
    return {"gap_count": len(gaps), "gaps": gaps}
