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

from typing import Literal

from pydantic import BaseModel, Field, ValidationError

CATALOG_VERSION = "ICPC-2e-v7.0"
COVERAGE_COMPONENTS = [1, 7]

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


def _validate_candidates(state: dict) -> list[CandidateVerdict]:
    transcript_cf = state["transcript"].casefold()
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
                # AC-02: verdicts are drawn only from the catalog list.
                raise ValueError(f"candidate code not in catalog: {cand.code!r}")
            for span in cand.evidence_spans:
                # Case-insensitive containment: field runs showed the
                # model case-folds span first-letters ("He" -> "he");
                # still catches invented spans (F3, raw-read finding).
                if span.casefold() not in transcript_cf:
                    raise ValueError(
                        f"evidence_span not in transcript for {cand.code}: " f"{span!r}"
                    )
            validated.append(cand)
    return validated


def _sort_key(cand: CandidateVerdict) -> tuple:
    return (_VERDICT_RANK[cand.verdict], -cand.confidence, cand.code)


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
        classification = {
            "primary": _entry(matches[0]),
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
