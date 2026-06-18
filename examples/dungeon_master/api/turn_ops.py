"""Play-loop operations for DM v2 turns (FR-477).

Pure operations on the story ``doc`` plus the single turn-graph invocation, kept
apart from the stage adapter so the structured turn side-channel (per-character
``intents``) lives in one place and ``session`` stays under the size gate.

A turn's ``recap`` is a plain ``{text, reviewed}`` entry — the same shape every
stage uses — which is what lets the generic weave/edit/accept act on a turn (J3).
``intents`` is the structured side-channel, never a stage entry.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime

from examples.dungeon_master.api.graph_app import clean_text, field, get_app
from examples.dungeon_master.api.seam_packet import (
    format_seam_packet,
    parse_seam_packet,
    validate_character_lifecycle,
)
from examples.dungeon_master.api.tree import (
    FINAL_CUT_GRAPH,
    TURN_GRAPH,
)
from examples.dungeon_master.api.world_state import (
    RETRIEVAL_TOPK,
    format_world_state,
    parse_world_state,
    rank_relationships,
)

_MAX_CUE_FIELD_CHARS = 240
_LOG = logging.getLogger(__name__)


class LifecycleGateError(RuntimeError):
    """Deterministic chapter-open lifecycle violation gate failure."""

    def __init__(self, payload: dict):
        self.payload = payload
        super().__init__(f"LIFECYCLE_GATE_VIOLATION: {payload}")


class ContinuityMemoryConflictError(LifecycleGateError):
    """Deterministic chapter-open memory-precedence conflict gate failure."""

    def __init__(self, payload: dict):
        self.payload = payload
        super(LifecycleGateError, self).__init__()
        RuntimeError.__init__(self, f"CONTINUITY_MEMORY_CONFLICT: {payload}")


def _trim_value(value: object, *, max_chars: int = _MAX_CUE_FIELD_CHARS) -> str:
    """Stringify and bound payload fields without dropping schema keys."""
    text = str(value or "")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _chapter_card(doc: dict, cid: str) -> dict:
    """Read-only view of chapter ``cid``'s card (empty if absent)."""
    return doc.get("chapters", {}).get("cards", {}).get(cid, {})


def chapter_turns(doc: dict, cid: str) -> list[dict]:
    """Read-only view of chapter ``cid``'s played turns (FR-491 C; empty if none)."""
    return _chapter_card(doc, cid).get("turns") or []


def chapter_beat_list(doc: dict, cid: str) -> list[str]:
    """Chapter ``cid``'s enumerated key-event beats (FR-503; empty if none).

    The finite contract the director selects from and the play loop drives toward.
    Non-empty by the FR-504 boundary contract (``chapter_ops._require_beats``); a
    chapter persisted before that contract — or one with no card — yields ``[]``.
    """
    return list(_chapter_card(doc, cid).get("beats") or [])


def reset_chapter_for_replay(doc: dict, cid: str) -> None:
    """Wipe chapter ``cid``'s played state so it can be re-played from its inherited start.

    Single named site for the doc-shape surgery a chapter replay requires (FR-522
    J1): drop this chapter's played ``turns``, clear its ``reviewed`` flag, and pop
    its own committed ``world_state``/``seam_packet`` (the close-graph emissions),
    so the next play derives them afresh. It touches ONLY ``cid``'s card — the
    inherited start (every prior chapter's committed state) is never read here and
    never mutated, which is what makes a replay a controlled experiment.
    """
    card = doc.get("chapters", {}).get("cards", {}).get(cid)
    if not isinstance(card, dict):
        return
    card["turns"] = []
    card["reviewed"] = False
    card.pop("world_state", None)
    card.pop("seam_packet", None)


def turn_record(doc: dict, cid: str, n: int) -> dict:
    """Chapter ``cid``'s ``turns[n-1]`` record ``{n, intents, recap}`` (created if absent).

    Turns are stored per chapter under ``chapters.cards[<cid>]["turns"]`` (FR-491
    Amendment C), never the flat ``doc["turns"]``: each chapter plays its own loop.
    """
    cards = doc.setdefault("chapters", {}).setdefault("cards", {})
    card = cards.setdefault(cid, {})
    turns = card.setdefault("turns", [])
    while len(turns) < n:
        m = len(turns) + 1
        turns.append({"n": m, "intents": {}, "recap": {"text": "", "reviewed": False}})
    rec = turns[n - 1]
    rec.setdefault("intents", {})
    rec.setdefault("recap", {"text": "", "reviewed": False})
    return rec


def turn_direction(doc: dict, cid: str, n: int) -> dict:
    """The director's ``direction`` side-channel for chapter ``cid``'s turn ``n``.

    A structured ``{phase, establishing, beats_satisfied, scene_complete, steer,
    continuity}`` judgement produced alongside the turn's intents (FR-479 J4);
    the recap entry shape stays ``{text, reviewed}`` (FR-477 J3). Empty if absent.
    """
    turns = chapter_turns(doc, cid)
    if n < 1 or len(turns) < n:
        return {}
    return turns[n - 1].get("direction") or {}


def turn_intents(doc: dict, chars: dict, cid: str, n: int) -> list[dict]:
    """Chapter ``cid``'s turn ``n`` intents as ordered performance cards (cast order).

    Each card is ``{name, thinking, intent, dialogue, expression}`` (FR-486): the
    private ``thinking`` and the decisive ``intent`` the arc reads, plus the
    outward performance layer — the spoken ``dialogue`` and the visible
    ``expression`` that projects the thinking. A turn played before FR-486 carries
    only the first two keys; the new keys default to ``""`` (a silent character is
    legitimate, not a defect — an additive side-channel, never a raise).
    """
    turns = chapter_turns(doc, cid)
    if n < 1 or len(turns) < n:
        return []
    intents = turns[n - 1].get("intents", {})
    out: list[dict] = []
    for char_id in chars["roster"]:
        if char_id in intents:
            perf = intents[char_id]
            out.append(
                {
                    "name": chars["cards"].get(char_id, {}).get("name") or char_id,
                    "thinking": perf.get("thinking", ""),
                    "intent": perf.get("intent", ""),
                    "dialogue": perf.get("dialogue", ""),
                    "expression": perf.get("expression", ""),
                }
            )
    return out


def prior_intents(doc: dict, cid: str, n: int) -> dict:
    """Each character's intent from chapter ``cid``'s turn ``n-1`` (empty before turn 2)."""
    turns = chapter_turns(doc, cid)
    if n < 2 or len(turns) < n - 1:
        return {}
    prev = turns[n - 2].get("intents", {})
    return {char_id: v.get("intent", "") for char_id, v in prev.items()}


def inherited_world_state(doc: dict, cid: str) -> dict:
    """The structured world_state chapter ``cid`` inherits — the PREVIOUS ledger.

    The load-bearing forward-carry (FR-488 J7, preserved through play): each
    chapter is played from where the last one left off. The carried value is the
    typed ledger (FR-499A) the previous chapter closed with. Empty (``{}``) for the
    first chapter, or when the chapter id is not in the derived order.
    """
    chapters = doc.get("chapters", {})
    order = chapters.get("order", [])
    cards = chapters.get("cards", {})
    if cid not in order:
        return {}
    i = order.index(cid)
    if i == 0:
        return {}
    return cards.get(order[i - 1], {}).get("world_state", {}) or {}


def inherited_seam_packet(doc: dict, cid: str) -> dict:
    """The seam packet chapter ``cid`` inherits from the previous chapter (FR-506)."""
    chapters = doc.get("chapters", {})
    order = chapters.get("order", [])
    cards = chapters.get("cards", {})
    if cid not in order:
        return {}
    i = order.index(cid)
    if i == 0:
        return {}
    return cards.get(order[i - 1], {}).get("seam_packet", {}) or {}


def _previous_chapter_id(doc: dict, cid: str) -> str:
    """Resolve the previous chapter id for chapter ``cid``; ``""`` when none."""
    order = doc.get("chapters", {}).get("order", [])
    if cid not in order:
        return ""
    i = order.index(cid)
    if i == 0:
        return ""
    return str(order[i - 1])


def _opening_source_pointer(doc: dict, cid: str) -> dict:
    """Deterministic source pointer for chapter-open seam memory resolution."""
    prev_cid = _previous_chapter_id(doc, cid)
    seam = parse_seam_packet(inherited_seam_packet(doc, cid))
    digest = hashlib.sha256(
        json.dumps(seam, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "chapter_id": prev_cid,
        "seam_hash": digest,
        "resolved_at": datetime.now(UTC).isoformat(),
    }


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


def _enforce_memory_precedence_gate(doc: dict, cid: str, n: int) -> None:
    """Block chapter turn-1 execution on deterministic memory source conflicts."""
    if n != 1:
        return
    prev_cid = _previous_chapter_id(doc, cid)
    if not prev_cid:
        return

    prev_card = _chapter_card(doc, prev_cid)
    chapter_memory = dict(prev_card.get("chapter_memory") or {})
    seam = parse_seam_packet(inherited_seam_packet(doc, cid))
    mem_states = _state_map_from_memory(chapter_memory)
    syn_states = _state_map_from_synopsis(doc)
    seam_states = _state_map_from_seam(seam)

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

    if not violations:
        return
    payload = {
        "code": "CONTINUITY_MEMORY_CONFLICT",
        "chapter_id": str(cid),
        "turn_n": n,
        "violations": violations,
        "source_pointer": _opening_source_pointer(doc, cid),
    }
    _LOG.warning("Continuity memory conflict: %s", payload)
    raise ContinuityMemoryConflictError(payload)


def _compile_opening_onepager(doc: dict, cid: str) -> dict:
    """Compile deterministic chapter-open onepager from structured memory layers."""
    prev_cid = _previous_chapter_id(doc, cid)
    prev_card = _chapter_card(doc, prev_cid) if prev_cid else {}
    chapter_memory = dict(prev_card.get("chapter_memory") or {})
    seam = parse_seam_packet(inherited_seam_packet(doc, cid))

    must_include = list(seam.get("must_carry_facts") or [])
    for fact in list(chapter_memory.get("irreversible_facts") or []):
        if fact not in must_include:
            must_include.append(fact)

    must_exclude = list(seam.get("opening_constraints") or [])
    for item in list(chapter_memory.get("forbidden_regressions") or []):
        if item not in must_exclude:
            must_exclude.append(item)

    active_cast_constraints: list[str] = []
    for item in list(seam.get("character_lifecycle") or []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        state = str(item.get("existence_state") or "").strip()
        visibility = str(item.get("visibility_mode") or "").strip()
        allowed = item.get("allowed_reappearance_from_chapter")
        if not name:
            continue
        extra = (
            f", allowed_reappearance_from_chapter={allowed}"
            if isinstance(allowed, int)
            else ""
        )
        active_cast_constraints.append(
            f"{name}: existence_state={state}, visibility_mode={visibility}{extra}"
        )

    checks = [
        f"source_pointer.chapter_id={_opening_source_pointer(doc, cid).get('chapter_id')}",
        "respect must_exclude constraints",
    ]
    return {
        "opening_truths": must_include[:12],
        "must_include": must_include[:12],
        "must_exclude": must_exclude[:12],
        "active_cast_constraints": active_cast_constraints[:12],
        "continuity_checks": checks,
    }


def _format_opening_onepager(onepager: dict) -> str:
    """Render opening onepager to deterministic prompt text."""
    lines: list[str] = ["OPENING ONEPAGER CONTRACT:"]
    labels = (
        ("opening_truths", "Opening Truths"),
        ("must_include", "Must Include"),
        ("must_exclude", "Must Exclude"),
        ("active_cast_constraints", "Active Cast Constraints"),
        ("continuity_checks", "Continuity Checks"),
    )
    wrote = False
    for key, label in labels:
        values = list(onepager.get(key) or [])
        if not values:
            continue
        wrote = True
        lines.append(f"{label}:")
        lines.extend(f"- {v}" for v in values)
    return "\n".join(lines) if wrote else ""


def _chapter_index(doc: dict, cid: str) -> int:
    """Resolve chapter id to 1-based chapter index for lifecycle gates."""
    order = doc.get("chapters", {}).get("order", [])
    if cid in order:
        return order.index(cid) + 1
    if str(cid).isdigit():
        n = int(cid)
        return n if n >= 1 else 1
    return 1


def _enforce_lifecycle_gate(doc: dict, cid: str, n: int, cast: list[dict]) -> None:
    """Block chapter turn-1 execution when lifecycle seam constraints are violated."""
    if n != 1:
        return
    packet = inherited_seam_packet(doc, cid)
    active_cast_names = [str(c.get("name") or "").strip() for c in cast]
    violations = validate_character_lifecycle(
        packet,
        chapter_id=_chapter_index(doc, cid),
        active_cast_names=active_cast_names,
    )
    if not violations:
        return

    payload = {
        "code": "LIFECYCLE_GATE_VIOLATION",
        "chapter_id": str(cid),
        "turn_n": n,
        "violations": violations,
    }
    _LOG.warning("Lifecycle gate violation: %s", payload)
    raise LifecycleGateError(payload)


def _chapter_cast_exits(doc: dict, cid: str, n: int) -> list[str]:
    """Names the director benched in chapter ``cid``'s turns *before* ``n`` (FR-521 S2).

    The director's structured ``cast_exits`` field names roster members who have
    left the scene this chapter — died, been swept away — and must not act again.
    Accumulated (union) across every prior turn so a single later clean turn cannot
    resurrect a benched actor, and chapter-scoped (read only from this chapter's
    own turns) so a legitimate cross-chapter return is never barred here. De-duped,
    first-seen order.
    """
    exits: list[str] = []
    for k in range(1, n):
        d = turn_direction(doc, cid, k)
        exits.extend(str(x) for x in (d.get("cast_exits") or []) if str(x).strip())
    return list(dict.fromkeys(exits))


def _filter_roster_for_lifecycle(
    doc: dict, chars: dict, cid: str, n: int, roster: list[str]
) -> list[str]:
    """Apply deterministic chapter-open lifecycle filtering to reviewed roster ids.

    Two layers, both source-side leak reductions (the hard lifecycle gate remains):

    - **Within-chapter exits (FR-521 S2):** drop any roster member the director has
      benched on an earlier turn of *this* chapter (its structured ``cast_exits``).
      The witnessed fix — a swept-away actor kept full agency because an advisory
      in the scene was ignored; only removing it from the cast stops the break.
      Never empties the cast (a chapter with everyone gone closes on its turn cap).
    - **Chapter-open seam gate:** at turn 1, admission uses the previous chapter's
      committed seam packet as lifecycle authority.
    """
    roster = _drop_within_chapter_exits(doc, chars, cid, n, roster)
    if n != 1:
        return roster

    packet = inherited_seam_packet(doc, cid)
    chapter_idx = _chapter_index(doc, cid)
    names_by_id = {
        char_id: str(chars["cards"].get(char_id, {}).get("name") or char_id).strip()
        for char_id in roster
    }
    candidate_names = [name for name in names_by_id.values() if name]
    violations = validate_character_lifecycle(
        packet,
        chapter_id=chapter_idx,
        active_cast_names=candidate_names,
    )
    if not violations:
        return roster

    blocked = {_norm_name(v.get("name")) for v in violations}
    filtered = [
        char_id
        for char_id in roster
        if _norm_name(names_by_id.get(char_id)) not in blocked
    ]
    if filtered:
        return filtered

    payload = {
        "code": "LIFECYCLE_GATE_VIOLATION",
        "chapter_id": str(cid),
        "turn_n": n,
        "violations": violations,
    }
    _LOG.warning("Lifecycle gate violation: %s", payload)
    raise LifecycleGateError(payload)


def _drop_within_chapter_exits(
    doc: dict, chars: dict, cid: str, n: int, roster: list[str]
) -> list[str]:
    """Drop roster ids the director benched earlier this chapter (FR-521 S2).

    Reads the accumulated ``cast_exits`` for chapter ``cid`` before turn ``n`` and
    removes any roster id whose display name matches (case-insensitive). Guards
    against handing the turn an empty cast: if every member has exited, the
    unfiltered roster is kept (the chapter's turn cap closes it instead).
    """
    exits = {_norm_name(name) for name in _chapter_cast_exits(doc, cid, n)}
    if not exits:
        return roster
    filtered = [
        char_id
        for char_id in roster
        if _norm_name(str(chars["cards"].get(char_id, {}).get("name") or char_id))
        not in exits
    ]
    return filtered or roster


def build_allowed_scene_cast(doc: dict, cid: str) -> list[str]:
    """Build deterministic allowed cast names for chapter-close prose control.

    Source-of-truth contract:
    1) iterate ``characters.roster`` in roster order,
    2) keep reviewed cards only,
    3) apply lifecycle exclusions against inherited seam packet for chapter-open,
    4) normalize names by lowercased/whitespace-collapsed matching keys.

    Returned values are display names in stable roster order.
    """
    chars = dict(doc.get("characters") or {})
    cards = dict(chars.get("cards") or {})
    roster = list(chars.get("roster") or [])

    reviewed_ids = [
        char_id
        for char_id in roster
        if bool(dict(cards.get(char_id) or {}).get("reviewed"))
    ]
    if not reviewed_ids:
        return []

    name_by_id = {
        char_id: str(dict(cards.get(char_id) or {}).get("name") or char_id).strip()
        for char_id in reviewed_ids
    }
    candidate_names = [name for name in name_by_id.values() if name]
    if not candidate_names:
        return []

    violations = validate_character_lifecycle(
        inherited_seam_packet(doc, cid),
        chapter_id=_chapter_index(doc, cid),
        active_cast_names=candidate_names,
    )
    blocked = {_norm_name(v.get("name")) for v in violations}
    out: list[str] = []
    seen: set[str] = set()
    for char_id in reviewed_ids:
        name = name_by_id.get(char_id, "")
        if not name:
            continue
        key = _norm_name(name)
        if key in blocked or key in seen:
            continue
        seen.add(key)
        out.append(name)
    return out


def chapter_recaps_text(doc: dict, cid: str) -> str:
    """Chapter ``cid``'s played recaps, in order, as one labelled block (FR-491 B)."""
    lines = []
    for t in chapter_turns(doc, cid):
        txt = (t.get("recap") or {}).get("text", "")
        if txt.strip():
            lines.append(f"Turn {t.get('n')}: {txt}")
    return "\n\n".join(lines)


def chapter_scene_complete(doc: dict, cid: str) -> bool:
    """Whether any of chapter ``cid``'s played turns reported the scene complete."""
    return any(
        (t.get("direction") or {}).get("scene_complete")
        for t in chapter_turns(doc, cid)
    )


# A chapter's only natural exit is its director emitting ``scene_complete``. A
# director that never resolves (observed live: a diffusion provider stuck in the
# "rising" phase for 91 turns) would consume the entire book turn_cap on a single
# chapter. This per-chapter turn budget is the deterministic backstop that bounds
# any provider: a chapter force-closes once it has played this many turns without
# resolving. Generous above the natural chapter length (~6 turns observed) so it
# rarely triggers on a well-behaved director, yet caps a runaway (FR-501).
CHAPTER_TURN_CAP = 16


def chapter_should_close(doc: dict, cid: str, n: int) -> bool:
    """Whether chapter ``cid`` should close after its turn ``n`` (FR-501).

    True when the director reported ``scene_complete`` for the turn, OR the chapter
    has played its full per-chapter turn budget (``CHAPTER_TURN_CAP``) without ever
    resolving — the safety valve that stops a director which never declares the
    scene complete from running the chapter away with the whole book budget.
    """
    if turn_direction(doc, cid, n).get("scene_complete"):
        return True
    return n >= CHAPTER_TURN_CAP


# ── Scene lifecycle (FR-493 J5) ──────────────────────────────────────────────
#
# The chapter-play phase, named as one unit. It answers the reader's question
# "how does a planned chapter become final text?" with a single contract:
#
#     {plan, cast, world_state_in} → play turns (map → director → recap)
#                                  → {final_text, world_state_out}
#
# The four load-bearing functions below run in that order:
#
#   running_scene     build the play context — this chapter's plan + the
#                     inherited world_state + its own prior recaps (the START).
#   invoke_turn       play ONE turn: map → director → recap, re-rolled together.
#   final_cut_context assemble the finished arc — beats, climax, recaps.
#   invoke_final_cut  compose the chapter's final prose from that arc.
#
# The fifth function, ``chapter_ops.close_chapter``, is the adapter-facing entry
# that derives ``world_state_out`` + final text by calling ``invoke_final_cut``;
# it stays in ``chapter_ops`` (it is invoked from ``doc_ops.apply_chapter_close``)
# but belongs to this same lifecycle. The two generative seams the live witness
# exists to prove — chapter completion judged from the summary, and world_state
# threaded across chapters — both live here.


def _retrieve_turn_ledger(doc: dict, cid: str) -> dict:
    """The inherited ledger pruned to top-K cast-relevant relationships (FR-516).

    Turn context must not drag every bond from a long saga into every turn; rank
    the inherited active relationships by cast relevance × salience × recency and
    keep at most ``RETRIEVAL_TOPK``. When the allowed cast is empty (no reviewed
    roster yet) ranking would drop everything, so fall back to the full inherited
    ledger — FR-516 bounds context, it never blanks it.
    """
    inherited = parse_world_state(inherited_world_state(doc, cid))
    cast_names = build_allowed_scene_cast(doc, cid)
    if not cast_names:
        return inherited
    ranked = rank_relationships(
        inherited["relationships"], cast_names=cast_names, k=RETRIEVAL_TOPK
    )
    pruned = dict(inherited)
    pruned["relationships"] = ranked
    return pruned


def running_scene(doc: dict, cid: str, n: int) -> str:
    """Chapter ``cid``'s play context for turn ``n`` (FR-491): its own plan + history.

    The scene is built from *this chapter's* summary (the intended arc — the key
    events it drives toward, not events already past), the *inherited* world_state
    (the established START, carried from the previous chapter), and *this
    chapter's* own prior recaps (the real history). Labelling them apart stops the
    model from reading the plan's destination as established fact and replaying the
    aftermath — on turn 1 nothing has happened yet, so play begins at the start (J4).
    """
    card = _chapter_card(doc, cid)
    title = card.get("title") or f"Chapter {cid}"
    summary = card.get("summary", "")
    inherited = format_world_state(
        _retrieve_turn_ledger(doc, cid), relationships="active"
    ).strip()
    seam = format_seam_packet(inherited_seam_packet(doc, cid)).strip()
    start = inherited or (
        "This is the opening chapter — there is no prior world state. Establish "
        "the chapter from this chapter's summary alone."
    )
    turns = chapter_turns(doc, cid)
    prior = [t.get("recap", {}).get("text", "") for t in turns[: n - 1]]
    prior = [p for p in prior if p.strip()][-3:]
    so_far = (
        "\n\n".join(prior)
        if prior
        else (
            "Nothing has happened yet — the chapter is just beginning. Only the "
            "starting world state is true; none of the chapter's key events have "
            "occurred."
        )
    )
    scene = (
        f"THIS CHAPTER — {title} — its intended arc (the key events it drives "
        "toward, NOT events that have already happened):\n"
        f"{summary}\n\n"
        "STARTING WORLD STATE (established before this chapter begins — true at "
        "the START):\n"
        f"{start}\n\n"
        "WHAT HAS HAPPENED SO FAR IN THIS CHAPTER:\n"
        f"{so_far}"
        f"{_beats_block(doc, cid, n)}"
    )
    if n == 1 and seam:
        scene += (
            "\n\nCHAPTER SEAM CONTRACT (must honor at chapter opening):\n" f"{seam}"
        )
    if n == 1:
        onepager = _format_opening_onepager(_compile_opening_onepager(doc, cid))
        if onepager:
            scene += f"\n\n{onepager}"
    return scene


def _beats_block(doc: dict, cid: str, n: int) -> str:
    """The chapter's finite beat ledger as scene context (FR-503; empty if none).

    Surfaces the enumerated beats as a 1-based numbered list (so the director can
    return the numbers it judges satisfied) and a separate "beats still to portray"
    block — the forward pull both the characters and the director read, derived
    from the prior turn's cumulative satisfied set. Empty for a chapter with no
    enumerated beats, leaving the pre-FR-503 scene unchanged.
    """
    beats = chapter_beat_list(doc, cid)
    if not beats:
        return ""
    satisfied = set(turn_direction(doc, cid, n - 1).get("beats_satisfied") or [])
    numbered = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(beats))
    pending = [b for b in beats if b not in satisfied]
    if pending:
        pending_lines = "\n".join(f"- {b}" for b in pending)
        pending_block = (
            "\n\nBEATS STILL TO PORTRAY — drive toward the FIRST of these next; do "
            "not skip past it, and do not replay a beat already portrayed:\n"
            f"{pending_lines}"
        )
    else:
        pending_block = (
            "\n\nBEATS STILL TO PORTRAY — none remain; every key beat has been "
            "portrayed. Bring the chapter to its close rather than prolonging it."
        )
    return (
        "\n\nTHE CHAPTER'S KEY BEATS (numbered) — the finite events this chapter "
        f"must portray, in order:\n{numbered}{pending_block}"
    )


async def invoke_turn(
    doc: dict, chars: dict, cid: str, n: int, instruction: str = ""
) -> str:
    """Run the turn graph for chapter ``cid``'s turn ``n``: write intents + direction, return its recap.

    Builds one ``{name, sheet, previous}`` bundle per reviewed character (J1), the
    bounded running scene (this chapter's plan + inherited world_state + last-3
    recaps, J4) and each character's prior intent, runs ``turn.yaml`` once (map →
    direct → recap), records ``chapters.cards[cid].turns[n].intents`` keyed by
    character id and the director's ``direction`` side-channel (FR-479 J4), and
    returns the recap text. The stage interface stays a pure ``str -> str``; this
    turn path owns both structured side-channels (J3).
    """
    roster = [
        char_id
        for char_id in chars["roster"]
        if chars["cards"].get(char_id, {}).get("reviewed")
    ]
    roster = _filter_roster_for_lifecycle(doc, chars, cid, n, roster)
    prev = prior_intents(doc, cid, n)
    cast = [
        {
            "name": chars["cards"][char_id].get("name") or char_id,
            "sheet": chars["cards"][char_id].get("text", ""),
            "previous": prev.get(char_id, ""),
        }
        for char_id in roster
    ]
    _enforce_memory_precedence_gate(doc, cid, n)
    _enforce_lifecycle_gate(doc, cid, n, cast)
    result = await get_app(TURN_GRAPH).ainvoke(
        {
            "cast": cast,
            "scene": running_scene(doc, cid, n),
            "turn_n": str(n),
            "instruction": instruction,
            "intents": [],
            "direction": {},
            "recap": "",
        }
    )
    items = result.get("intents") or []
    record = turn_record(doc, cid, n)
    record["intents"] = {
        char_id: {
            "thinking": field(item, "thinking"),
            "intent": field(item, "intent"),
            "dialogue": field(item, "dialogue"),
            "expression": field(item, "expression"),
        }
        for char_id, item in zip(roster, items, strict=False)
    }
    direction = _direction_dict(result.get("direction"))
    prior = turn_direction(doc, cid, n - 1)
    _apply_beat_ledger(direction, chapter_beat_list(doc, cid), prior)
    record["direction"] = direction
    return clean_text(result.get("recap"))


def _phase_for_count(satisfied: int, total: int) -> str:
    """Map a satisfied-beat count to the arc phase (FR-503 J3 truth table).

    ``opening`` at zero, ``resolved`` only once every beat is satisfied, ``climax``
    on the final beat, ``rising`` while partway. Because the satisfied set is
    accumulated monotonically (``_apply_beat_ledger`` unions with the prior turn),
    the computed phase is monotonic by construction — subsuming the retired FR-481
    ``_clamp_phase`` (FR-504).
    """
    if total >= 1 and satisfied >= total:
        return "resolved"
    if satisfied <= 0:
        return "opening"
    if satisfied >= total - 1:
        return "climax"
    return "rising"


def _satisfied_indices(raw: object, beats: list[str]) -> set[int]:
    """Parse the director's satisfied-beat selection into 0-based indices (FR-503).

    The scene presents the beats as a 1-based numbered list, so the director
    returns those numbers; this maps them to 0-based indices, ignoring anything
    out of range or unparseable (boundary: trust no provider's type). A model that
    echoes the beat TEXT instead of its number still resolves via a match against
    the enumerated list, so a disobedient provider does not silently drop a beat.
    """
    n = len(beats)
    lowered = [b.lower() for b in beats]
    out: set[int] = set()
    for v in raw or []:
        if isinstance(v, bool):
            continue
        if isinstance(v, int):
            i = v - 1
            if 0 <= i < n:
                out.add(i)
            continue
        s = str(v).strip()
        if not s:
            continue
        token = s.lstrip("Bb#").strip()
        if token.isdigit():
            i = int(token) - 1
            if 0 <= i < n:
                out.add(i)
            continue
        sl = s.lower()
        for i, b in enumerate(lowered):
            if sl == b or sl in b or b in sl:
                out.add(i)
                break
    return out


def _apply_beat_ledger(direction: dict, beats: list[str], prior: dict) -> None:
    """Resolve satisfied-beat indices to text, accumulate, and compute phase (FR-503).

    The director selects from a finite, enumerated beat list rather than inventing
    free-text phrases, so the satisfied set is bounded and ``beats_satisfied`` can
    no longer inflate past ``len(beats)``. The returned indices are unioned with
    the prior turn's satisfied set (cumulative), resolved back to canonical beat
    TEXT so every downstream consumer reads the same ``list[str]`` shape (J1), and
    ``phase`` / ``scene_complete`` are COMPUTED from k / N (J3) — the rails are
    code, the model judges only WHICH enumerated beats are now true. ``beats`` is a
    non-empty boundary contract (FR-504 ``_require_beats``); the FR-491 free-text
    ``N == 0`` fallback has been retired.
    """
    n = len(beats)
    cur = _satisfied_indices(direction.get("beats_satisfied"), beats)
    prior_text = (prior or {}).get("beats_satisfied") or []
    prior_idx = {beats.index(t) for t in prior_text if t in beats}
    satisfied = sorted(prior_idx | cur)
    k = len(satisfied)
    direction["beats_satisfied"] = [beats[i] for i in satisfied]
    direction["beats_total"] = n
    direction["phase"] = _phase_for_count(k, n)
    direction["scene_complete"] = k == n


def _direction_dict(raw: object) -> dict:
    """Normalise the director's output (dict or pydantic) to a typed dict (J4).

    Unlike ``field`` (which coerces to ``str``), this preserves ``scene_complete``
    as a bool and the list fields as lists, since the session and UI branch on them.
    """
    if not raw:
        return {}

    def _get(key: str, default: object) -> object:
        val = (
            raw.get(key, default)
            if isinstance(raw, dict)
            else getattr(raw, key, default)
        )
        return default if val is None else val

    return {
        "phase": str(_get("phase", "")),
        "establishing": str(_get("establishing", "")),
        "beats_satisfied": list(_get("beats_satisfied", []) or []),
        "scene_complete": bool(_get("scene_complete", False)),
        "steer": str(_get("steer", "")),
        "continuity": list(_get("continuity", []) or []),
        "cast_exits": list(_get("cast_exits", []) or []),
    }


def climax_turn(doc: dict, cid: str) -> int:
    """The 1-based turn index chapter ``cid`` turns on, derived from the phases (FR-492).

    The director's ``phase`` is monotonic (FR-481), so the first turn to reach
    ``"climax"`` is the pivotal beat. When no turn ever recorded a climax phase,
    fall back to the turn that reported ``scene_complete``; failing even that, the
    last turn. Pure code over **this chapter's** played turns
    (``chapters.cards[cid].turns``) — the Final Cut is handed this marker rather
    than asked to recompute what the recorded arc already knows (FR-482 law).
    """
    turns = chapter_turns(doc, cid)
    for t in turns:
        if (t.get("direction") or {}).get("phase") == "climax":
            return int(t.get("n", turns.index(t) + 1))
    for t in turns:
        if (t.get("direction") or {}).get("scene_complete"):
            return int(t.get("n", turns.index(t) + 1))
    return int(turns[-1].get("n", len(turns))) if turns else 0


def chapter_beats(doc: dict, cid: str) -> list[str]:
    """The beats chapter ``cid`` satisfied, accumulated across its turns (FR-492).

    The fidelity signal the Final Cut must preserve. The director records
    ``beats_satisfied`` cumulatively per turn as canonical beat TEXT resolved from
    the finite enumerated list (``_apply_beat_ledger``, FR-503/FR-504). This unions
    the chapter's turns' beats, de-duplicated and order-preserving, so the finish
    is handed the canonical beats the play loop confirmed rather than re-deriving
    them.
    """
    beats: list[str] = []
    for t in chapter_turns(doc, cid):
        for b in (t.get("direction") or {}).get("beats_satisfied") or []:
            if b not in beats:
                beats.append(b)
    return beats


def _cast_order(doc: dict) -> list[tuple[str, str]]:
    """Return cast order as ``[(char_id, display_name), ...]``."""
    chars = doc.get("characters", {})
    roster = list(chars.get("roster") or [])
    cards = chars.get("cards") or {}
    return [
        (char_id, (cards.get(char_id, {}).get("name") or char_id)) for char_id in roster
    ]


def _turn_performance_cards(doc: dict, turn: dict) -> list[dict]:
    """Stable-schema performance cards for one turn in cast order (FR-505 C1)."""
    intents = (turn.get("intents") or {}) if isinstance(turn, dict) else {}
    cards: list[dict] = []
    for char_id, name in _cast_order(doc):
        perf = intents.get(char_id) or {}
        cards.append(
            {
                "name": name,
                "intent": _trim_value(perf.get("intent", "")),
                "dialogue": _trim_value(perf.get("dialogue", "")),
                "expression": _trim_value(perf.get("expression", "")),
            }
        )
    return cards


def beat_turn_groups(doc: dict, cid: str) -> list[dict]:
    """Group chapter turns by first-advanced beat with connective carryover.

    Each turn is assigned to exactly one beat group. A turn that advances no new
    beats attaches to the most-recently-advanced beat (or the first beat when no
    beat has advanced yet), so no recap/performance card is orphaned.
    """
    turns = chapter_turns(doc, cid)
    beats = chapter_beat_list(doc, cid) or chapter_beats(doc, cid)
    if not beats:
        return []

    # Preserve beat order while admitting any unexpected director beat text.
    ordered = list(
        dict.fromkeys(beats + [b for b in chapter_beats(doc, cid) if b not in beats])
    )
    groups = {beat: {"beat": beat, "turns": [], "is_climax": False} for beat in ordered}

    seen: set[str] = set()
    owner = ordered[0]
    climax_n = climax_turn(doc, cid)

    for t in turns:
        n = int(t.get("n", len(groups) + 1))
        rec = (t.get("direction") or {}).get("beats_satisfied") or []
        current = [b for b in rec if isinstance(b, str) and b in groups]
        advanced = [b for b in current if b not in seen]
        seen.update(current)
        if advanced:
            owner = advanced[-1]

        groups[owner]["turns"].append(
            {
                "n": n,
                "recap": _trim_value(
                    (t.get("recap") or {}).get("text", ""), max_chars=600
                ),
                "intents": _turn_performance_cards(doc, t),
                "advanced_beats": advanced,
            }
        )

        if n == climax_n:
            groups[owner]["is_climax"] = True

    return [groups[b] for b in ordered]


def _format_beat_groups(groups: list[dict]) -> str:
    """Render beat groups for prompt consumption."""
    blocks: list[str] = []
    for i, group in enumerate(groups, start=1):
        beat = group.get("beat", "")
        climax = "  <-- CLIMAX BEAT" if group.get("is_climax") else ""
        lines = [f"Beat {i}: {beat}{climax}"]
        for turn in group.get("turns") or []:
            lines.append(f"  Turn {turn.get('n')}: {turn.get('recap', '')}")
            for perf in turn.get("intents") or []:
                name = perf.get("name", "")
                intent = perf.get("intent", "")
                dialogue = perf.get("dialogue", "")
                expression = perf.get("expression", "")
                lines.append(f"    - {name} intent: {intent}")
                if dialogue:
                    lines.append(f"      dialogue: {dialogue}")
                if expression:
                    lines.append(f"      expression: {expression}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


# FR-519: status tokens that mean a character has died (within-chapter death
# signal from the close-graph world_state lane).
_DEAD_STATUS_TOKENS = {"dead", "slain", "killed", "deceased", "fallen"}

# FR-521 J2: within a chapter, "presumed dead / swept away" is a death-point too —
# the character must not keep acting after it. The widening is chapter-scoped: it
# feeds ONLY the within-chapter lane (read from this chapter's ``closed``). The
# before-open bar stays confirmed_dead only, so a legitimate synopsis return
# (presumed-dead → reappears) is never barred at the next chapter's open.
_PRESUMED_DEAD_TOKENS = {"missing_presumed_dead", "presumed_dead"}
_WITHIN_DEATH_STATUS_TOKENS = _DEAD_STATUS_TOKENS | _PRESUMED_DEAD_TOKENS
_WITHIN_DEATH_EXISTENCE_STATES = {"confirmed_dead"} | _PRESUMED_DEAD_TOKENS


def dead_character_names(
    doc: dict, cid: str, closed: dict | None = None
) -> tuple[list[str], list[str]]:
    """``(dead_before_open, dead_within_chapter)`` display names for chapter ``cid``.

    Two distinct lifecycle classes the final cut must treat differently (FR-519):

    - ``dead_before_open``: confirmed-dead at chapter open, read from the
      **inherited** seam (the prior chapter's close) — the FR-510 cross-chapter
      case; these characters must not appear at all.
    - ``dead_within_chapter``: died **during** this chapter, read from the
      close-graph output ``closed`` (its ``world_state`` dead-status characters and
      its closing seam ``character_lifecycle`` rows). They act legitimately up to
      their death and must not act after it.

    ``closed`` must be threaded in, not read back from the doc: at final-cut time
    the chapter's own ``world_state`` is not yet committed (it is derived *after*
    ``invoke_final_cut`` returns), so reading the doc card would see the stale
    prior state (FR-519 B1). A character dead at open is never re-listed as within.
    """
    prior_seam = parse_seam_packet(inherited_seam_packet(doc, cid))
    before: dict[str, str] = {}
    for item in prior_seam.get("character_lifecycle") or []:
        if str(item.get("existence_state") or "").strip() != "confirmed_dead":
            continue
        name = str(item.get("name") or "").strip()
        if name:
            before.setdefault(_norm_name(name), name)

    within: dict[str, str] = {}
    if isinstance(closed, dict):
        ws = parse_world_state(closed.get("world_state"))
        for c in ws.get("characters", []):
            if (
                str(c.get("status") or "").strip().lower()
                in _WITHIN_DEATH_STATUS_TOKENS
            ):
                name = str(c.get("name") or "").strip()
                if name:
                    within.setdefault(_norm_name(name), name)
        close_seam = parse_seam_packet(closed.get("seam_packet"))
        for item in close_seam.get("character_lifecycle") or []:
            if (
                str(item.get("existence_state") or "").strip()
                not in _WITHIN_DEATH_EXISTENCE_STATES
            ):
                continue
            name = str(item.get("name") or "").strip()
            if name:
                within.setdefault(_norm_name(name), name)

    for key in list(within):
        if key in before:
            within.pop(key, None)

    return list(before.values()), list(within.values())


def _possession_facts(doc: dict, cid: str, closed: dict | None = None) -> str:
    """Lines of who-holds-what the chapter's prose must not contradict (FR-519).

    Sourced from the **inherited** ledger (the prior chapter's committed
    ``world_state`` — the persistent, correct possession truth at chapter open),
    overlaid with the close-graph ``closed`` emission when present so an object
    picked up within the chapter is also covered. Deterministic order: inherited
    first, then close-emission overrides in place. ``""`` when nothing is tracked.
    """
    char_inv: dict[str, tuple[str, list[str]]] = {}
    obj_holder: dict[str, tuple[str, str]] = {}

    def _absorb(ws: dict) -> None:
        for c in ws.get("characters", []):
            name = str(c.get("name") or "").strip()
            items = [
                str(i).strip() for i in (c.get("inventory") or []) if str(i).strip()
            ]
            if name and items:
                char_inv[_norm_name(name)] = (name, items)
        for o in ws.get("objects", []):
            name = str(o.get("name") or "").strip()
            holder = str(o.get("holder") or "").strip()
            if name and holder:
                obj_holder[_norm_name(name)] = (name, holder)

    _absorb(parse_world_state(inherited_world_state(doc, cid)))
    if isinstance(closed, dict):
        _absorb(parse_world_state(closed.get("world_state")))

    lines = [f"{disp} holds: {', '.join(items)}" for disp, items in char_inv.values()]
    lines += [f"the {disp} is held by {holder}" for disp, holder in obj_holder.values()]
    return "\n".join(lines)


def final_cut_context(doc: dict, cid: str, closed: dict | None = None) -> dict:
    """Assemble chapter ``cid``'s finished arc as Final Cut graph variables (FR-492).

    A pure function over the story ``doc``: the chapter ``summary`` as the scene
    plan (standing in for the retired ``key_scene``), **every** played turn recap
    in order (``chapters.cards[cid].turns``, not the flat ``doc["turns"]`` the
    pre-chapter shape used), each turn's director ``phase`` with the pivotal turn
    marked, the beats the director confirmed (:func:`chapter_beats`), and a derived
    ``climax`` marker. This is the deterministic seam — the model is handed the
    assembled context and asked only for prose, never to recompute the arc's
    structure.

    FR-519 threads the chapter's committed physical state into the prompt as a hard
    constraint: ``dead_before_open`` / ``dead_within_chapter`` (lifecycle split, the
    within class sourced from the close-graph ``closed`` since the chapter's own
    ``world_state`` is not yet committed) and ``possession_facts`` (who-holds-what
    from the inherited ledger). Each is an empty string when nothing applies, so a
    chapter with no deaths or tracked objects renders an unchanged prompt.
    """
    card = _chapter_card(doc, cid)
    summary = card.get("summary", "")
    turns = chapter_turns(doc, cid)
    climax_n = climax_turn(doc, cid)
    groups = beat_turn_groups(doc, cid)
    beats = chapter_beats(doc, cid)
    before_open, within_chapter = dead_character_names(doc, cid, closed)
    allowed_cast = build_allowed_scene_cast(doc, cid)
    return {
        "key_scene": summary,
        "arc": _format_beat_groups(groups),
        "beats": "\n".join(f"- {b}" for b in beats),
        "climax": f"Turn {climax_n}" if turns else "",
        "beat_groups": _format_beat_groups(groups),
        "dead_before_open": ", ".join(before_open),
        "dead_within_chapter": ", ".join(within_chapter),
        "possession_facts": _possession_facts(doc, cid, closed),
        "allowed_cast": ", ".join(allowed_cast),
    }


async def invoke_final_cut(
    doc: dict,
    cid: str,
    instruction: str = "",
    draft: str = "",
    closed: dict | None = None,
) -> str:
    """Compose chapter ``cid``'s continuous final text from its whole arc (FR-492).

    Runs ``final_cut.yaml`` once over :func:`final_cut_context` plus the current
    draft and a writer's instruction, and returns the cleaned narration — the
    chapter's beat-faithful final text. Reads the chapter's played turns; writes
    none of them. ``closed`` (the close-graph output) is threaded through so the
    within-chapter death constraint is available before the chapter's own
    ``world_state`` is committed (FR-519).
    """
    result = await get_app(FINAL_CUT_GRAPH).ainvoke(
        {
            **final_cut_context(doc, cid, closed),
            "draft": draft,
            "instruction": instruction,
            "final_cut": "",
        }
    )
    return clean_text(result.get("final_cut"))
