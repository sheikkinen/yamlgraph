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

    A thread opens on its first raise. Once open it may receive several
    releases — de-escalation resolves a tension in steps, not one release per
    raise. A release fired before any raise (by sequence) is unbalanced. A
    thread declared ``released`` must cite at least one release event.
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

        raises_seen = 0
        for seq, op, eid in events:
            if op == "raise":
                raises_seen += 1
            elif raises_seen == 0:
                violations.append(
                    f"thread '{tid}': release '{eid}' (seq {seq}) has no prior raise"
                )
    return {"valid": not violations, "violations": violations}


def check_cap_and_distinctness(threads: list[dict[str, Any]]) -> dict[str, Any]:
    """At most MAX_THREADS threads; distinct threads; non-empty opposition.

    Distinctness keys on ``(kind, carriers)``: a feud and a survival crisis
    between the same two people are different threads. Only a same-kind,
    same-carrier pair is a true duplicate.
    """
    violations: list[str] = []
    if len(threads) > MAX_THREADS:
        violations.append(f"thread count {len(threads)} exceeds cap of {MAX_THREADS}")

    seen: dict[tuple[str, frozenset[str]], str] = {}
    for t in threads:
        tid = t.get("id", "<no-id>")
        if not (t.get("opposition") or "").strip():
            violations.append(f"thread '{tid}': opposition is empty")
        key = (t.get("kind", ""), frozenset(t.get("carriers", [])))
        if key in seen:
            violations.append(
                f"thread '{tid}': duplicates thread '{seen[key]}' "
                "(same kind and carriers)"
            )
        else:
            seen[key] = tid
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


# --- Graph-node adapters (second caller: story_extract.yaml) ---
#
# These read graph state, derive the canon facts the pure gates need, and
# aggregate their verdicts into the {"gate_result": ...} shape the graph edges
# route on. The pure functions above stay the single source of gate logic.

_MAJOR_ROLES = frozenset({"protagonist", "antagonist", "supporting"})


def _derive_canon(
    canon_pages: dict[str, dict[str, Any]],
) -> tuple[set[str], dict[str, int], set[str]]:
    """Extract (all ids, event sequences, major character ids) from canon.

    "Major" is any named character with an arc — every role except ``minor``.
    """
    canon_ids = set(canon_pages.keys())
    sequences: dict[str, int] = {}
    major_ids: set[str] = set()
    for pid, page in canon_pages.items():
        if page.get("type") == "event" and page.get("sequence") is not None:
            sequences[pid] = page["sequence"]
        if page.get("type") == "character" and page.get("role") in _MAJOR_ROLES:
            major_ids.add(pid)
    return canon_ids, sequences, major_ids


def _as_dicts(items: Any) -> list[dict[str, Any]]:
    """Normalize a list of Pydantic models or dicts to plain dicts."""
    out: list[dict[str, Any]] = []
    for item in items or []:
        out.append(item.model_dump() if hasattr(item, "model_dump") else dict(item))
    return out


def gate_threads(state: dict[str, Any]) -> dict[str, Any]:
    """Run all four thread gates over the final union in graph state.

    Reads state["threads"] (final union), state["canon_pages"],
    state["prior_thread_ids"] (set, empty on first run), and
    state["dropped_threads"] (list of {id, reason}). Returns the aggregated
    {"gate_result": {"valid", "violations"}}.
    """
    threads = _as_dicts(state.get("threads"))
    canon_ids, sequences, _ = _derive_canon(state.get("canon_pages", {}))
    prior_ids = set(state.get("prior_thread_ids", []) or [])
    dropped = _as_dicts(state.get("dropped_threads"))

    violations: list[str] = []
    for result in (
        check_citation_integrity(threads, canon_ids),
        check_ledger_walk(threads, sequences),
        check_cap_and_distinctness(threads),
        check_id_stability(threads, prior_ids, dropped),
    ):
        violations.extend(result["violations"])
    return {"gate_result": {"valid": not violations, "violations": violations}}


def gate_throughlines(state: dict[str, Any]) -> dict[str, Any]:
    """Run the throughline gate over graph state.

    Reads state["throughlines"] and state["canon_pages"]. Returns
    {"gate_result": {"valid", "violations"}}.
    """
    throughlines = _as_dicts(state.get("throughlines"))
    canon_ids, sequences, major_ids = _derive_canon(state.get("canon_pages", {}))
    result = check_throughlines(throughlines, canon_ids, sequences, major_ids)
    return {"gate_result": result}
