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
    """Every carrier/source/raise/release id must resolve to a canon id."""
    violations: list[str] = []
    for t in threads:
        tid = t.get("id", "<no-id>")
        for field in ("carriers", "sources", "raises", "releases"):
            for ref in t.get(field, []):
                if ref not in canon_ids:
                    violations.append(
                        f"thread '{tid}': {field} cites unknown canon id '{ref}'"
                    )
    return {"valid": not violations, "violations": violations}


def check_ledger_walk(
    threads: list[dict[str, Any]], sequences: dict[str, int]
) -> dict[str, Any]:
    """Walk each thread's raise/release events in sequence order.

    A release fires only against an open raise; a release seen while nothing is
    open is unbalanced. A thread declared ``released`` must cite at least one
    release event.
    """
    violations: list[str] = []
    for t in threads:
        tid = t.get("id", "<no-id>")
        releases = t.get("releases", [])
        if t.get("status") == "released" and not releases:
            violations.append(
                f"thread '{tid}': status=released but no release event cited"
            )

        events: list[tuple[int, str, str]] = []
        for eid in t.get("raises", []):
            seq = sequences.get(eid)
            if seq is not None:
                events.append((seq, "raise", eid))
        for eid in releases:
            seq = sequences.get(eid)
            if seq is not None:
                events.append((seq, "release", eid))
        events.sort(key=lambda x: x[0])

        opened = 0
        for seq, op, eid in events:
            if op == "raise":
                opened += 1
            elif opened == 0:
                violations.append(
                    f"thread '{tid}': release '{eid}' (seq {seq}) has no prior raise"
                )
            else:
                opened -= 1
    return {"valid": not violations, "violations": violations}


def check_cap_and_distinctness(threads: list[dict[str, Any]]) -> dict[str, Any]:
    """At most MAX_THREADS threads; distinct carrier sets; non-empty opposition."""
    violations: list[str] = []
    if len(threads) > MAX_THREADS:
        violations.append(f"thread count {len(threads)} exceeds cap of {MAX_THREADS}")

    seen: dict[frozenset[str], str] = {}
    for t in threads:
        tid = t.get("id", "<no-id>")
        if not (t.get("opposition") or "").strip():
            violations.append(f"thread '{tid}': opposition is empty")
        carrier_set = frozenset(t.get("carriers", []))
        if carrier_set in seen:
            violations.append(
                f"thread '{tid}': carrier set duplicates thread '{seen[carrier_set]}'"
            )
        else:
            seen[carrier_set] = tid
    return {"valid": not violations, "violations": violations}


def check_id_stability(
    threads: list[dict[str, Any]],
    prior_ids: set[str],
    dropped: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Regeneration must preserve ids or account for every dropped prior id.

    No-op on the first run (empty ``prior_ids``). Any prior id absent from the
    current set must appear in ``dropped``.
    """
    if not prior_ids:
        return {"valid": True, "violations": []}

    violations: list[str] = []
    current_ids = {t.get("id") for t in threads}
    dropped_ids = {d.get("id") for d in (dropped or [])}
    for pid in prior_ids:
        if pid not in current_ids and pid not in dropped_ids:
            violations.append(
                f"prior thread '{pid}' dropped without a reason in `dropped`"
            )
    return {"valid": not violations, "violations": violations}


def check_throughlines(
    throughlines: list[dict[str, Any]],
    canon_ids: set[str],
    sequences: dict[str, int],
    major_ids: set[str],
) -> dict[str, Any]:
    """Each throughline walks cited, sequenced events in non-decreasing order.

    A throughline needs at least one slack point or an explicit ``arc_taut``
    claim; a major character's arc may not be zero-delta (every entry ``none``).
    """
    violations: list[str] = []
    for tl in throughlines:
        char = tl.get("character", "<no-char>")
        entries = tl.get("entries", [])

        prev_seq: int | None = None
        for entry in entries:
            eid = entry.get("event")
            if eid not in canon_ids:
                violations.append(
                    f"throughline '{char}': entry cites unknown event '{eid}'"
                )
                continue
            seq = sequences.get(eid)
            if seq is None:
                violations.append(
                    f"throughline '{char}': event '{eid}' has no sequence"
                )
                continue
            if prev_seq is not None and seq < prev_seq:
                violations.append(
                    f"throughline '{char}': event '{eid}' (seq {seq}) out of order"
                )
            prev_seq = seq

        has_slack = any(e.get("slack") for e in entries)
        if not has_slack and not tl.get("arc_taut"):
            violations.append(
                f"throughline '{char}': no slack point and no arc_taut claim"
            )

        if char in major_ids:
            has_delta = any(e.get("delta") in ("gain", "loss") for e in entries)
            if not has_delta:
                violations.append(
                    f"throughline '{char}': zero-delta arc for major character"
                )
    return {"valid": not violations, "violations": violations}
