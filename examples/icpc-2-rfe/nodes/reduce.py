"""FR-722 deterministic reducer (REQ-YG-550) — no LLM call (Judgement F4).

Candidates from the map fan-out validate against a Pydantic model at
this boundary (Commandment 5); evidence spans must be substrings of the
raw transcript (F3 — a span the input never contained is a
plausible_wrong_answer). Ranking is a total order: verdict rank, then
confidence (within-rank tie-break only, F6), then code string.

NOTE: no ``from __future__ import annotations`` here — postponed
annotations break Pydantic model construction under file-path module
loading (spec_from_file_location cannot resolve the string ``Literal``).
"""

import difflib
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

CATALOG_VERSION = "ICPC-2e-v7.0"
COVERAGE_COMPONENTS = [1, 2, 3, 4, 5, 6, 7]

_VERDICT_RANK = {"match": 0, "partial_match": 1, "not_applicable": 2}


def _is_process(code: str) -> bool:
    return code.startswith("-")


class CandidateVerdict(BaseModel):
    """Per-code verdict returned by a map cluster item (judged contract)."""

    code: str
    title: str
    verdict: Literal["match", "partial_match", "not_applicable"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_short: str
    evidence_spans: list[str] = Field(default_factory=list)
    missing_signals: list[str] = Field(default_factory=list)


def _align_span(span: str, transcript: str, transcript_cf: str) -> str:
    """Align a claimed evidence span to the transcript (F3, field run 8).

    LLM token-fidelity is fragile — two prompt hardenings still produced
    one-character drift ("äitini" → "äitiini"). Copying is a mechanizable
    level, so it lives HERE: exact (case-folded) containment returns the
    true transcript text; a near-miss (similarity ≥ 0.85 against the
    best-anchored window) is REPAIRED to the actual substring; anything
    below the floor is a fabrication and raises. Output spans are
    therefore always verbatim transcript text, whatever the model typed.
    """
    # Models decorate quotes (field: '"a dry cough"' with literal quote
    # chars) — strip wrapping punctuation before aligning.
    span = span.strip().strip("\"'\u201c\u201d\u2018\u2019").strip()
    span_cf = span.casefold()
    idx = transcript_cf.find(span_cf)
    if idx >= 0:
        return transcript[idx : idx + len(span)]

    matcher = difflib.SequenceMatcher(None, transcript_cf, span_cf, autojunk=False)
    block = matcher.find_longest_match(0, len(transcript_cf), 0, len(span_cf))
    if block.size == 0:
        raise ValueError(f"evidence_span not in transcript: {span!r}")
    # Transcript window that should correspond to the whole claim.
    start = max(0, block.a - block.b)
    end = min(len(transcript), start + len(span) + 5)
    window = transcript[start:end]
    ratio = difflib.SequenceMatcher(
        None, window.casefold(), span_cf, autojunk=False
    ).ratio()
    if ratio < 0.85:
        raise ValueError(f"evidence_span not in transcript: {span!r}")
    return window.strip()


def _validate_candidates(state: dict) -> list[CandidateVerdict]:
    transcript = state["transcript"]
    transcript_cf = transcript.casefold()
    known_codes = {
        row["code"]
        for cluster in state.get("rfe_clusters") or []
        for row in cluster.get("codes") or []
    }
    validated: list[CandidateVerdict] = []
    for result in state.get("map_results") or []:
        for raw in (result or {}).get("candidates") or []:
            try:
                cand = CandidateVerdict.model_validate(raw)
            except ValidationError as exc:
                raise ValueError(f"Invalid candidate {raw!r}: {exc}") from exc
            if known_codes and cand.code not in known_codes:
                # FR-724 field finding: models drop the process-code
                # sigil ("48" for "-48") — repair mechanically when the
                # sigiled form IS in the catalog; anything else is an
                # invention (AC-02) and raises.
                if f"-{cand.code}" in known_codes:
                    cand.code = f"-{cand.code}"
                else:
                    raise ValueError(f"candidate code not in catalog: {cand.code!r}")
            try:
                cand.evidence_spans = [
                    _align_span(span, transcript, transcript_cf)
                    for span in cand.evidence_spans
                ]
            except ValueError as exc:
                raise ValueError(
                    f"evidence_span not in transcript for {cand.code}: {exc}"
                ) from exc
            validated.append(cand)
    return validated


def _sort_key(cand: CandidateVerdict) -> tuple:
    # FR-724 F4: within a verdict rank a process code outranks a chapter
    # code — the stated reason for a renewal/admin call IS the process
    # (ICPC RFE semantics). Deliberate rule, witnessed; "-" sorting
    # before letters must never be the reason this works.
    return (
        _VERDICT_RANK[cand.verdict],
        0 if _is_process(cand.code) else 1,
        -cand.confidence,
        cand.code,
    )


def _entry(cand: CandidateVerdict) -> dict:
    return {
        "code": cand.code,
        "title": cand.title,
        "verdict": cand.verdict,
        "confidence": cand.confidence,
        "reasoning_short": cand.reasoning_short,
        "evidence_spans": cand.evidence_spans,
    }


def reduce_best_rfe(state: dict) -> dict:
    """Deterministic selection; explanation composed mechanically."""
    ranked = sorted(_validate_candidates(state), key=_sort_key)
    # Per-code dedup, keep the best-ranked occurrence (raw-read finding,
    # field run 3: one cluster emitted L03 twice → duplicate secondary).
    seen: set[str] = set()
    deduped = [c for c in ranked if not (c.code in seen or seen.add(c.code))]
    matches = [c for c in deduped if c.verdict == "match"]
    partials = [c for c in deduped if c.verdict == "partial_match"]

    if matches:
        primary = _entry(matches[0])
        if _is_process(matches[0].code):
            # FR-724 F1: chapter_context is reducer-derived — the best-
            # ranked non-process candidate (match or partial), attached
            # mechanically. The LLM never judges chapter from a process
            # cluster.
            context = next((c for c in deduped if not _is_process(c.code)), None)
            if context is not None:
                primary["chapter_context"] = {
                    "code": context.code,
                    "title": context.title,
                }
        classification = {
            "primary": primary,
            "secondary": [_entry(c) for c in matches[1:]],
            "low_confidence": False,
            "best_partial": [_entry(c) for c in partials[:3]],
        }
    else:
        # AC-06: no forced match — explicit low-confidence result.
        classification = {
            "primary": None,
            "secondary": [],
            "low_confidence": True,
            "best_partial": [_entry(c) for c in partials[:3]],
        }

    return {
        "classification": classification,
        "meta": {
            "catalog_version": state.get("catalog_version") or CATALOG_VERSION,
            "catalog_coverage": {
                "components": COVERAGE_COMPONENTS,
                "clusters_evaluated": len(state.get("map_results") or []),
            },
            "candidates_total": len(deduped),
        },
    }
