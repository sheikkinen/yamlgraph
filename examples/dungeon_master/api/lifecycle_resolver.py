"""Deterministic lifecycle precedence resolver (FR-534).

The single source of truth for "what is a character's authoritative state, and is
the plan sworn to keep them alive?" Both the chapter-open precedence gate
(``turn_ops._enforce_memory_precedence_gate``) and prose generation (the turn
director + final cut) consult this module, so plan-over-prose precedence reaches
the boundary where the prose is *born*, not only the boundary where it is *read*.

Precedence (highest first): ``chapter_memory > live_synopsis > seam_packet``.

The FR-533 spike found DM v2 already enforced this precedence for *bookkeeping*
but never fed it to *generation*, so the turn engine could narrate the death of a
plan-protected character the ledger then refused to record (the ch7 Witta
resurrection). ``protected_characters`` closes that gap.

This module is a *low-level* dependency: it imports ``seam_packet`` and
``chapter_nav`` at module load — both leaves — so it never reaches into
``turn_ops``. FR-536 dissolved the former lazy ``turn_ops`` doc-walk import: the
nav primitives now live in ``chapter_nav``, which this module imports directly
(J4), leaving ``turn_ops`` free to import the extractors here at load with no
cycle.
"""

from __future__ import annotations

from examples.dungeon_master.api import chapter_nav
from examples.dungeon_master.api.seam_packet import parse_seam_packet

# State precedence order: highest authority first.
PRECEDENCE: tuple[str, str, str] = ("chapter_memory", "live_synopsis", "seam_packet")

# Lowercased states treated as "alive/active" for protection membership.
_LIVE_STATES: frozenset[str] = frozenset({"alive", "active"})


def _norm_name(name: object) -> str:
    return " ".join(str(name or "").lower().split())


def _state_map_from_memory(memory: dict) -> dict[str, str]:
    states: dict[str, str] = {}
    for item in list(memory.get("character_state_deltas") or []):
        if not isinstance(item, dict):
            continue
        key = _norm_name(item.get("name"))
        state = str(item.get("to_state") or "").strip()
        if key and state:
            states[key] = state
    return states


def _state_map_from_synopsis(doc: dict) -> dict[str, str]:
    states = dict(doc.get("live_synopsis", {}).get("character_states") or {})
    out: dict[str, str] = {}
    for name, state in states.items():
        key = _norm_name(name)
        val = str(state or "").strip()
        if key and val:
            out[key] = val
    return out


def _state_map_from_seam(packet: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in list(packet.get("character_lifecycle") or []):
        if not isinstance(item, dict):
            continue
        key = _norm_name(item.get("name"))
        state = str(item.get("existence_state") or "").strip()
        if key and state:
            out[key] = state
    return out


def _resolve_inputs(doc: dict, cid: str) -> tuple[dict, dict, dict, dict]:
    """``(chapter_memory, mem_states, syn_states, seam_states)`` for chapter ``cid``."""
    prev_cid = chapter_nav.previous_chapter_id(doc, cid) or ""
    prev_card = chapter_nav.chapter_card(doc, prev_cid) if prev_cid else {}
    chapter_memory = dict(prev_card.get("chapter_memory") or {})
    seam = parse_seam_packet(chapter_nav.inherited_seam_packet(doc, cid))
    return (
        chapter_memory,
        _state_map_from_memory(chapter_memory),
        _state_map_from_synopsis(doc),
        _state_map_from_seam(seam),
    )


def state_conflict_violations(doc: dict, cid: str) -> list[dict[str, str]]:
    """Deterministic precedence conflicts among the three memory sources.

    Higher-precedence source wins; a lower source disagreeing is a violation. This
    is the precedence logic the chapter-open gate raises on — extracted here so the
    gate and ``protected_characters`` share one ordering.
    """
    _, mem_states, syn_states, seam_states = _resolve_inputs(doc, cid)
    violations: list[dict[str, str]] = []

    for name, mem_state in mem_states.items():
        syn_state = syn_states.get(name)
        if syn_state and syn_state != mem_state:
            violations.append(
                {
                    "type": "state_conflict",
                    "name": name,
                    "higher_source": "chapter_memory",
                    "lower_source": "live_synopsis",
                    "detail": f"{mem_state} conflicts with {syn_state}",
                }
            )
        seam_state = seam_states.get(name)
        if seam_state and seam_state != mem_state:
            violations.append(
                {
                    "type": "state_conflict",
                    "name": name,
                    "higher_source": "chapter_memory",
                    "lower_source": "seam_packet",
                    "detail": f"{mem_state} conflicts with {seam_state}",
                }
            )

    for name, syn_state in syn_states.items():
        if name in mem_states:
            continue
        seam_state = seam_states.get(name)
        if seam_state and seam_state != syn_state:
            violations.append(
                {
                    "type": "state_conflict",
                    "name": name,
                    "higher_source": "live_synopsis",
                    "lower_source": "seam_packet",
                    "detail": f"{syn_state} conflicts with {seam_state}",
                }
            )

    return violations


def _display_names(chapter_memory: dict, doc: dict, seam: dict) -> dict[str, str]:
    """``{norm_name: display_name}`` across all three sources (first-seen wins)."""
    out: dict[str, str] = {}

    def _add(name: object) -> None:
        disp = str(name or "").strip()
        if disp:
            out.setdefault(_norm_name(disp), disp)

    for item in chapter_memory.get("character_state_deltas") or []:
        if isinstance(item, dict):
            _add(item.get("name"))
    for name in doc.get("live_synopsis", {}).get("character_states") or {}:
        _add(name)
    for item in seam.get("character_lifecycle") or []:
        if isinstance(item, dict):
            _add(item.get("name"))
    return out


def _floor_map(seam: dict) -> dict[str, int]:
    """``{norm_name: allowed_reappearance_from_chapter}`` from the inherited seam."""
    out: dict[str, int] = {}
    for item in seam.get("character_lifecycle") or []:
        if not isinstance(item, dict):
            continue
        key = _norm_name(item.get("name"))
        floor = item.get("allowed_reappearance_from_chapter")
        if key and isinstance(floor, int):
            out[key] = floor
    return out


def _guard_reason(
    key: str, display: str, chapter_memory: dict, syn_states: dict
) -> str | None:
    """Which plan guard names this character, if any (J4 conjunction, second clause).

    A plan guard is an ``irreversible_facts`` "X is alive" assertion, a
    ``forbidden_regressions`` "X is dead" entry, or a ``live_synopsis`` presence.
    Returns the guard kind, or ``None`` when the character is unguarded (a
    transient walk-on the plan does not protect).
    """
    needle = display.lower()
    for fact in chapter_memory.get("irreversible_facts") or []:
        text = str(fact).lower()
        if needle in text and "alive" in text:
            return "irreversible_facts"
    for reg in chapter_memory.get("forbidden_regressions") or []:
        text = str(reg).lower()
        if needle in text and "dead" in text:
            return "forbidden_regressions"
    if key in syn_states:
        return "live_synopsis"
    return None


def _highest_precedence_state(
    key: str, mem: dict, syn: dict, seam: dict
) -> tuple[str, str]:
    """``(state, source)`` for ``key`` by precedence; ``("", "")`` when unknown."""
    if key in mem:
        return mem[key], "chapter_memory"
    if key in syn:
        return syn[key], "live_synopsis"
    if key in seam:
        return seam[key], "seam_packet"
    return "", ""


def protected_characters(doc: dict, cid: str) -> dict[str, dict]:
    """Characters the plan requires alive in chapter ``cid`` (J4 conjunction).

    ``protected = (highest-precedence state is alive/active) AND (a plan guard
    names the character)``. Returns ``{norm_name: {name, reason, floor, state,
    source}}`` — ``name`` the display name for prose constraints, ``floor`` the
    authored ``allowed_reappearance_from_chapter`` (wired for a follow-up; not
    bound to behaviour here), ``reason`` the guard kind, ``state``/``source`` the
    authoritative precedence result.

    A transient walk-on that is merely alive in one source but named by no plan
    guard is NOT protected, so legitimate deaths remain possible.
    """
    chapter_memory, mem, syn, seam_states = _resolve_inputs(doc, cid)
    seam = parse_seam_packet(chapter_nav.inherited_seam_packet(doc, cid))
    display = _display_names(chapter_memory, doc, seam)
    floors = _floor_map(seam)

    out: dict[str, dict] = {}
    for key in set(mem) | set(syn) | set(seam_states):
        state, source = _highest_precedence_state(key, mem, syn, seam_states)
        if state.lower() not in _LIVE_STATES:
            continue
        reason = _guard_reason(key, display.get(key, key), chapter_memory, syn)
        if reason is None:
            continue
        out[key] = {
            "name": display.get(key, key),
            "reason": reason,
            "floor": floors.get(key),
            "state": state,
            "source": source,
        }
    return out


def protected_cast_names(doc: dict, cid: str) -> list[str]:
    """Display names of protected characters for chapter ``cid``, stable order."""
    return [entry["name"] for entry in protected_characters(doc, cid).values()]
