"""Event sequence ordering check for novel_fandom canon (FR-690).

Pure function + fixtures for the story pipeline's total-order invariant.
`sequence` is optional at the Pydantic layer (genesis/create_event do not emit
it) but MANDATORY for the Floodmark canon — this check is where that mandate
lives. Arithmetic, not an LLM task (ref_check is the wrong tool): uniqueness
and year/sequence consistency are pure computation.

Loaded directly by tests; can be wrapped as a Python node by the story
pipeline. One implementation, two callers.
"""

from __future__ import annotations

from typing import Any


def check_event_sequence(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate the total-order invariant over canon events.

    Three invariants:
      (a) completeness — every event has a non-null integer ``sequence``
      (b) uniqueness   — no two events share a ``sequence`` value
      (c) consistency  — for any two events with differing ``year``, the
                         ``sequence`` order agrees with the ``year`` order
                         (a later year never gets an earlier sequence)

    Args:
        events: list of event page dicts (must carry ``id``; ``sequence`` and
            ``year`` optional per-dict but (a) flags missing ``sequence``).

    Returns:
        {"valid": bool, "violations": list[str]}
    """
    violations: list[str] = []

    # (a) completeness
    sequenced: list[dict[str, Any]] = []
    for ev in events:
        seq = ev.get("sequence")
        if seq is None or not isinstance(seq, int) or isinstance(seq, bool):
            violations.append(
                f"event '{ev.get('id', '?')}' has missing or non-integer sequence"
            )
        else:
            sequenced.append(ev)

    # (b) uniqueness
    seen: dict[int, str] = {}
    for ev in sequenced:
        seq = ev["sequence"]
        if seq in seen:
            violations.append(
                f"duplicate sequence {seq}: '{seen[seq]}' and '{ev['id']}'"
            )
        else:
            seen[seq] = ev["id"]

    # (c) year/sequence consistency — only events carrying an integer year
    dated = [
        ev
        for ev in sequenced
        if isinstance(ev.get("year"), int) and not isinstance(ev.get("year"), bool)
    ]
    for i, a in enumerate(dated):
        for b in dated[i + 1 :]:
            if a["year"] == b["year"]:
                continue
            year_order = a["year"] < b["year"]
            seq_order = a["sequence"] < b["sequence"]
            if year_order != seq_order:
                earlier_year, later_year = (a, b) if a["year"] < b["year"] else (b, a)
                violations.append(
                    f"year/sequence contradiction: '{earlier_year['id']}' "
                    f"(year={earlier_year['year']}, seq={earlier_year['sequence']}) "
                    f"vs '{later_year['id']}' "
                    f"(year={later_year['year']}, seq={later_year['sequence']})"
                )

    return {"valid": len(violations) == 0, "violations": violations}
