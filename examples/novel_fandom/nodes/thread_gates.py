"""Mechanical gates for story threads and throughlines (FR-691).

Pure functions — no I/O, no LLM. Each returns
``{"valid": bool, "violations": list[str]}`` following the novel_fandom gate
convention (ref_integrity, validate_pages). One implementation, two callers:
invoked as Python nodes inside `story_extract.yaml` (fail the run) and imported
directly by tests (prove the invariant).

Gates:
  1. citation_integrity — every carrier/source/raise/release id resolves to canon
  2. ledger_walk        — a release without a prior raise (by sequence) fails
  3. cap_and_distinctness — union <= 8; distinct carrier-sets; opposition non-empty
  4. id_stability       — regeneration preserves ids; drops listed with reasons
  5. throughlines       — sequence-ordered, cited, non-zero-delta for majors

Id resolution against a YAML set is arithmetic, not an LLM task (FR-690/691
Judgement): the ref_check LLM graph-tool is the wrong tool here.
"""

from __future__ import annotations

from typing import Any

MAX_THREADS = 8


def check_citation_integrity(
    threads: list[dict[str, Any]], canon_ids: set[str]
) -> dict[str, Any]:
    """STUB (FR-691 RED): real logic lands in GREEN."""
    return {"valid": True, "violations": []}


def check_ledger_walk(
    threads: list[dict[str, Any]], sequences: dict[str, int]
) -> dict[str, Any]:
    """STUB (FR-691 RED): real logic lands in GREEN."""
    return {"valid": True, "violations": []}


def check_cap_and_distinctness(threads: list[dict[str, Any]]) -> dict[str, Any]:
    """STUB (FR-691 RED): real logic lands in GREEN."""
    return {"valid": True, "violations": []}


def check_id_stability(
    threads: list[dict[str, Any]],
    prior_ids: set[str],
    dropped: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """STUB (FR-691 RED): real logic lands in GREEN."""
    return {"valid": True, "violations": []}


def check_throughlines(
    throughlines: list[dict[str, Any]],
    canon_ids: set[str],
    sequences: dict[str, int],
    major_ids: set[str],
) -> dict[str, Any]:
    """STUB (FR-691 RED): real logic lands in GREEN."""
    return {"valid": True, "violations": []}
