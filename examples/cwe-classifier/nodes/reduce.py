"""FR-733 deterministic reducer (REQ-YG-559) — no LLM call.

Copy-adapted from examples/icpc-2-rfe/nodes/reduce.py (judged: no
shared-library extraction in this FR; what a library WOULD need is
recorded in the FR). Candidates from the map fan-out validate against a
Pydantic model at this boundary; evidence spans must align to the raw
description (the icpc _align_span discipline, same 0.85 floor).

CWE-specific rules (all catalog-derived, F3/F2):
- Prohibited codes are absent from every cluster → not-in-catalog raise.
- Discouraged match claims demote to partial (capped, evidence kept).
- Allowed-with-Review matches stay primary-capable, flagged review:true.
- Lowest-abstraction guard: a match whose ChildOf descendant (transitive)
  is also matched demotes to partial; lone Class matches survive.

NOTE: no ``from __future__ import annotations`` here — postponed
annotations break Pydantic model construction under file-path module
loading (spec_from_file_location cannot resolve the string ``Literal``).
"""

import difflib
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

CATALOG_VERSION = "cwec_v4.20"

_VERDICT_RANK = {"match": 0, "partial_match": 1, "not_applicable": 2}


class CandidateVerdict(BaseModel):
    """Per-code verdict returned by a map cluster item (judged contract)."""

    code: str
    title: str
    verdict: Literal["match", "partial_match", "not_applicable"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_short: str
    evidence_spans: list[str] = Field(default_factory=list)
    missing_signals: list[str] = Field(default_factory=list)
    capped: bool = False  # Discouraged demotion or shadowed Class ancestor
    review: bool = False  # Allowed-with-Review flag (F3: outcome, not demotion)


def _align_span(span: str, description: str, description_cf: str) -> str:
    """Align a claimed evidence span to the description (icpc F3 boundary).

    Exact (case-folded) containment returns the true source text; a
    near-miss (similarity ≥ 0.85 against the best-anchored window) is
    REPAIRED to the actual substring; below the floor is a fabrication
    and raises. Output spans are always verbatim description text.
    """
    span = span.strip().strip("\"'\u201c\u201d\u2018\u2019").strip()
    span_cf = span.casefold()
    idx = description_cf.find(span_cf)
    if idx >= 0:
        return description[idx : idx + len(span)]

    matcher = difflib.SequenceMatcher(None, description_cf, span_cf, autojunk=False)
    block = matcher.find_longest_match(0, len(description_cf), 0, len(span_cf))
    if block.size == 0:
        raise ValueError(f"evidence_span not in description: {span!r}")
    start = max(0, block.a - block.b)
    end = min(len(description), start + len(span) + 5)
    window = description[start:end]
    ratio = difflib.SequenceMatcher(
        None, window.casefold(), span_cf, autojunk=False
    ).ratio()
    if ratio < 0.85:
        raise ValueError(f"evidence_span not in description: {span!r}")
    return window.strip()


def _catalog_rows(state: dict) -> dict[str, dict]:
    return {
        row["code"]: row
        for cluster in state.get("cwe_clusters") or []
        for row in cluster.get("codes") or []
    }


def _validate_candidates(state: dict, rows: dict[str, dict]) -> list[CandidateVerdict]:
    description = state["description"]
    description_cf = description.casefold()
    validated: list[CandidateVerdict] = []
    for result in state.get("map_results") or []:
        for raw in (result or {}).get("candidates") or []:
            try:
                cand = CandidateVerdict.model_validate(raw)
            except ValidationError as exc:
                raise ValueError(f"Invalid candidate {raw!r}: {exc}") from exc
            if rows and cand.code not in rows:
                # Sigil analog (icpc FR-724 field finding): models emit
                # the bare number ("79" for "CWE-79") — repair when the
                # prefixed form IS in the catalog; anything else —
                # including Prohibited codes, absent from all clusters —
                # is an invention and raises.
                if f"CWE-{cand.code}" in rows:
                    cand.code = f"CWE-{cand.code}"
                else:
                    raise ValueError(f"candidate code not in catalog: {cand.code!r}")
            try:
                cand.evidence_spans = [
                    _align_span(span, description, description_cf)
                    for span in cand.evidence_spans
                ]
            except ValueError as exc:
                raise ValueError(
                    f"evidence_span not in description for {cand.code}: {exc}"
                ) from exc
            usage = (rows.get(cand.code) or {}).get("mapping_usage", "Allowed")
            if usage == "Discouraged" and cand.verdict == "match":
                # F3 / icpc FR-727 mechanism: demote, never drop —
                # evidence stays visible in best_partial.
                cand.verdict = "partial_match"
                cand.capped = True
            if usage == "Allowed-with-Review" and cand.verdict == "match":
                cand.review = True
            validated.append(cand)
    return validated


def _ancestors(code: str, rows: dict[str, dict]) -> set[str]:
    """Transitive ChildOf ancestors, catalog-derived."""
    out: set[str] = set()
    stack = list((rows.get(code) or {}).get("parents") or [])
    while stack:
        parent = stack.pop()
        if parent in out:
            continue
        out.add(parent)
        stack.extend((rows.get(parent) or {}).get("parents") or [])
    return out


def _demote_matched_ancestors(candidates: list, rows: dict[str, dict]) -> None:
    """F2 lowest-abstraction guard: a match whose ChildOf descendant is
    also matched demotes to partial (CWE-79 Base beats its matched
    CWE-707 Class ancestor). Lone Class matches survive — the rule
    never fires without a competing descendant."""
    matched = [c for c in candidates if c.verdict == "match"]
    shadowed: set[str] = set()
    for cand in matched:
        shadowed |= _ancestors(cand.code, rows) & {c.code for c in matched}
    for cand in candidates:
        if cand.verdict == "match" and cand.code in shadowed:
            cand.verdict = "partial_match"
            cand.capped = True


def _sort_key(cand: CandidateVerdict) -> tuple:
    # icpc FR-727 refinement: a DEMOTED claim must not outcompete
    # genuine partials for the 3-slot best_partial window.
    return (
        _VERDICT_RANK[cand.verdict],
        1 if cand.capped else 0,
        -cand.confidence,
        cand.code,
    )


def _entry(cand: CandidateVerdict) -> dict:
    entry = {
        "code": cand.code,
        "title": cand.title,
        "verdict": cand.verdict,
        "confidence": cand.confidence,
        "reasoning_short": cand.reasoning_short,
        "evidence_spans": cand.evidence_spans,
    }
    if cand.review:
        entry["review"] = True
    return entry


def reduce_best_cwe(state: dict) -> dict:
    """Deterministic selection; explanation composed mechanically."""
    rows = _catalog_rows(state)
    validated = _validate_candidates(state, rows)
    _demote_matched_ancestors(validated, rows)
    ranked = sorted(validated, key=_sort_key)
    seen: set[str] = set()
    deduped = [c for c in ranked if not (c.code in seen or seen.add(c.code))]
    matches = [c for c in deduped if c.verdict == "match"]
    partials = [c for c in deduped if c.verdict == "partial_match"]

    if matches:
        classification = {
            "primary": _entry(matches[0]),
            "secondary": [_entry(c) for c in matches[1:]],
            "low_confidence": False,
            "best_partial": [_entry(c) for c in partials[:3]],
        }
    else:
        classification = {
            "primary": None,
            "secondary": [],
            "low_confidence": True,
            "best_partial": [_entry(c) for c in partials[:3]],
        }

    clusters = state.get("cwe_clusters") or []
    coverage = dict(clusters[0]["coverage"]) if clusters else {}
    coverage["clusters_evaluated"] = len(state.get("map_results") or [])
    return {
        "classification": classification,
        "meta": {
            "catalog_version": (
                clusters[0]["catalog_version"] if clusters else CATALOG_VERSION
            ),
            "catalog_coverage": coverage,
            "candidates_total": len(deduped),
        },
    }
