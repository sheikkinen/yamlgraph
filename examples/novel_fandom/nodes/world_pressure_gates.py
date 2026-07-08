"""FR-692: World-pressure admission + kinship reciprocity gates (REQ-YG-531/532).

The world-pressure pass grows canon *additively* under two mechanical rules:

  * **Admission** — a newly created entity is admitted only if it cites the plot
    thread(s) it pressurizes and every cited id resolves to a live thread. No
    thread citation, no admission (`check_pressure_admission`).
  * **Reciprocity** — a kinship edge `A --kind--> B` (for a bounded set of
    reciprocal kinds) must be acknowledged by some reverse edge `B --*--> A`
    (`check_reciprocity`).

One implementation, two callers (tests + the `world_pressure.yaml` graph nodes).

RED contract: this module ships as always-valid stubs; every invalid-fixture
test fails until the real logic lands (GREEN).
"""

from __future__ import annotations

from typing import Any

# Kinship kinds that must be mutually acknowledged. Bounded for FR-692 to the
# kinds present in the three known non-reciprocal edges; broader coverage is
# deferred (see FR-692 Judgement).
RECIPROCAL_KINDS: frozenset[str] = frozenset({"mother", "father", "clanmate"})


def check_pressure_admission(
    entities: list[dict[str, Any]],
    thread_ids: set[str],
) -> dict[str, Any]:
    """Admit a candidate entity only if it cites the thread(s) it pressurizes.

    Each entity must carry a non-empty ``pressurizes`` list and every cited id
    must resolve to a live thread in ``thread_ids``. Runs over the pass's
    candidate entities only — pre-existing canon is exempt.

    Args:
        entities: candidate entity page dicts (each must carry ``id``).
        thread_ids: the set of live plot thread ids.

    Returns:
        {"valid": bool, "violations": list[str]}
    """
    violations: list[str] = []
    for ent in entities:
        eid = ent.get("id", "<no-id>")
        cited = ent.get("pressurizes") or []
        if not cited:
            violations.append(
                f"entity '{eid}': cites no thread (empty pressurizes) — no admission"
            )
            continue
        for tid in cited:
            if tid not in thread_ids:
                violations.append(
                    f"entity '{eid}': pressurizes '{tid}' which is not a live thread"
                )
    return {"valid": not violations, "violations": violations}


def check_reciprocity(
    characters: list[dict[str, Any]],
    reciprocal_kinds: set[str],
) -> dict[str, Any]:
    """Every kinship edge of a reciprocal kind must be acknowledged in reverse.

    For each ``A --kind--> B`` whose ``kind`` is in ``reciprocal_kinds``, some
    reverse edge ``B --*--> A`` (of any kind) must exist. Reciprocity is mutual
    acknowledgment, not identical reverse kind.

    Args:
        characters: character page dicts carrying ``id`` and ``relationships``
            (each relationship a dict with ``to`` and ``kind``).
        reciprocal_kinds: kinds that must be reciprocated.

    Returns:
        {"valid": bool, "violations": list[str]}
    """
    # index of who acknowledges whom: source -> set(targets)
    acknowledges: dict[str, set[str]] = {}
    for ch in characters:
        cid = ch.get("id", "")
        targets = {r.get("to", "") for r in ch.get("relationships") or []}
        acknowledges[cid] = targets

    violations: list[str] = []
    for ch in characters:
        src = ch.get("id", "<no-id>")
        for rel in ch.get("relationships") or []:
            kind = rel.get("kind", "")
            if kind not in reciprocal_kinds:
                continue
            tgt = rel.get("to", "")
            if src not in acknowledges.get(tgt, set()):
                violations.append(
                    f"'{src}' --{kind}--> '{tgt}' is not reciprocated: "
                    f"'{tgt}' has no reverse edge to '{src}'"
                )
    return {"valid": not violations, "violations": violations}


# ------------------------------------------------------------------
# Graph adapters — one implementation, two callers (tests + graph nodes)
# ------------------------------------------------------------------


def gate_reciprocity(state: dict[str, Any]) -> dict[str, Any]:
    """Graph node: run the kinship reciprocity gate over loaded canon.

    Reads ``state["canon_pages"]`` (id -> page dict), keeps characters, and
    checks reciprocity for ``RECIPROCAL_KINDS``. Returns the aggregated verdict
    under ``gate_result``.
    """
    canon = state.get("canon_pages", {}) or {}
    characters = [p for p in canon.values() if p.get("type") == "character"]
    return {"gate_result": check_reciprocity(characters, set(RECIPROCAL_KINDS))}


def gate_admission(state: dict[str, Any]) -> dict[str, Any]:
    """Graph node: run the pressure-admission gate over pass candidates.

    Reads ``state["candidates"]`` (the entities the pass created) and derives
    the live thread id set from ``state["thread_ids"]`` (explicit) or from
    ``state["canon_pages"]`` entries of type ``thread``. Returns the verdict
    under ``gate_result``.
    """
    candidates = state.get("candidates", []) or []
    thread_ids = set(state.get("thread_ids", []) or [])
    if not thread_ids:
        canon = state.get("canon_pages", {}) or {}
        thread_ids = {
            pid for pid, page in canon.items() if page.get("type") == "thread"
        }
    return {"gate_result": check_pressure_admission(candidates, thread_ids)}
