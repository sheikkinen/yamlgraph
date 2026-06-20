"""Play-loop operations for DM v2 turns (FR-477).

Pure operations on the story ``doc`` plus the single turn-graph invocation, kept
apart from the stage adapter so the structured turn side-channel (per-character
``intents``) lives in one place and ``session`` stays under the size gate.

A turn's ``recap`` is a plain ``{text, reviewed}`` entry — the same shape every
stage uses — which is what lets the generic weave/edit/accept act on a turn (J3).
``intents`` is the structured side-channel, never a stage entry.

The chapter-play phase is one lifecycle (FR-493 J5): :func:`running_scene` builds
the play context (this chapter's plan + inherited world_state + its own prior
recaps), :func:`invoke_turn` plays ONE turn (map → director → recap). The
chapter-open gates and cast admission live in :mod:`chapter_open`; the finish
(``final_cut_context`` / ``invoke_final_cut``) in :mod:`final_cut`; the
turn-record primitives in :mod:`turn_state`.
"""

from __future__ import annotations

from examples.dungeon_master.api import chapter_nav
from examples.dungeon_master.api.chapter_open import (
    build_allowed_scene_cast,
    compile_opening_onepager,
    enforce_lifecycle_gate,
    enforce_memory_precedence_gate,
    filter_roster_for_lifecycle,
    format_opening_onepager,
    scope_roster_to_chapter_cast,
)
from examples.dungeon_master.api.character_overlay import derive_overlay
from examples.dungeon_master.api.graph_app import clean_text, field, get_app
from examples.dungeon_master.api.lifecycle_resolver import (
    _state_map_from_memory as _state_map_from_memory,
)
from examples.dungeon_master.api.lifecycle_resolver import (
    _state_map_from_seam as _state_map_from_seam,
)
from examples.dungeon_master.api.lifecycle_resolver import (
    _state_map_from_synopsis as _state_map_from_synopsis,
)
from examples.dungeon_master.api.lifecycle_resolver import protected_cast_names
from examples.dungeon_master.api.seam_packet import format_seam_packet
from examples.dungeon_master.api.tree import TURN_GRAPH
from examples.dungeon_master.api.turn_state import (
    chapter_beat_list,
    chapter_turns,
    prior_intents,
    turn_direction,
    turn_record,
)
from examples.dungeon_master.api.world_state import (
    RETRIEVAL_TOPK,
    format_world_state,
    parse_world_state,
    rank_relationships,
)


def _retrieve_turn_ledger(doc: dict, cid: str) -> dict:
    """The inherited ledger pruned to top-K cast-relevant relationships (FR-516).

    Turn context must not drag every bond from a long saga into every turn; rank
    the inherited active relationships by cast relevance × salience × recency and
    keep at most ``RETRIEVAL_TOPK``. When the allowed cast is empty (no reviewed
    roster yet) ranking would drop everything, so fall back to the full inherited
    ledger — FR-516 bounds context, it never blanks it.
    """
    inherited = parse_world_state(chapter_nav.inherited_world_state(doc, cid))
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
    card = chapter_nav.chapter_card(doc, cid)
    title = card.get("title") or f"Chapter {cid}"
    summary = card.get("summary", "")
    inherited = format_world_state(
        _retrieve_turn_ledger(doc, cid), relationships="active"
    ).strip()
    seam = format_seam_packet(chapter_nav.inherited_seam_packet(doc, cid)).strip()
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
        scene += f"\n\nCHAPTER SEAM CONTRACT (must honor at chapter opening):\n{seam}"
    if n == 1:
        onepager = format_opening_onepager(compile_opening_onepager(doc, cid))
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
    roster = scope_roster_to_chapter_cast(doc, chars, cid, roster)
    roster = filter_roster_for_lifecycle(doc, chars, cid, n, roster)
    prev = prior_intents(doc, cid, n)
    cast = [
        {
            "name": chars["cards"][char_id].get("name") or char_id,
            "sheet": chars["cards"][char_id].get("text", ""),
            "previous": prev.get(char_id, ""),
            "overlay": derive_overlay(
                doc, cid, chars["cards"][char_id].get("name") or char_id
            ),
        }
        for char_id in roster
    ]
    enforce_memory_precedence_gate(doc, cid, n)
    enforce_lifecycle_gate(doc, cid, n, cast)
    result = await get_app(TURN_GRAPH).ainvoke(
        {
            "cast": cast,
            "scene": running_scene(doc, cid, n),
            "turn_n": str(n),
            "instruction": instruction,
            "protected": ", ".join(protected_cast_names(doc, cid)),
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
