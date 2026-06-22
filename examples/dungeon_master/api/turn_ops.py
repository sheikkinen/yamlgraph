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

from examples.dungeon_master.api import chapter_nav, turn_engine
from examples.dungeon_master.api.chapter_open import (
    _chapter_index,
    build_allowed_scene_cast,
    compile_opening_onepager,
    enforce_lifecycle_gate,
    enforce_memory_precedence_gate,
    filter_roster_for_lifecycle,
    format_opening_onepager,
    scope_roster_to_chapter_cast,
)
from examples.dungeon_master.api.character_overlay import derive_overlay
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
from examples.dungeon_master.api.turn_state import (
    _chapter_cast_exits,
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
        entry_state = str(card.get("entry_state") or "").strip()
        if entry_state:
            scene += (
                "\n\nCHAPTER ENTRY STATE (the configuration that is TRUE as this "
                "chapter opens — play turn 1 FROM this):\n"
                f"{entry_state}"
            )
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
    # FR-564 M4b: additive beat instruction merge, gated on attached plan (J6).
    plan = chapter_nav.attached_plot_plan(doc)
    if plan is not None:
        from examples.dungeon_master.api.plot.realize import (
            beat_instruction,
            merge_beat_instruction,
        )

        beat = beat_instruction(plan, _chapter_index(doc, cid))
        instruction = merge_beat_instruction(instruction, beat)
    req = turn_engine.TurnRequest(
        cast=cast,
        scene=running_scene(doc, cid, n),
        turn_n=n,
        instruction=instruction,
        beats=chapter_beat_list(doc, cid),
        prior_direction=turn_direction(doc, cid, n - 1),
        extras=turn_engine.TurnExtras(
            protected=", ".join(protected_cast_names(doc, cid)),
            gone_this_chapter=", ".join(_chapter_cast_exits(doc, cid, n)),
        ),
    )
    result = await turn_engine.play_turn(req)
    record = turn_record(doc, cid, n)
    record["intents"] = dict(zip(roster, result.intents, strict=False))
    record["direction"] = result.direction
    return result.recap
