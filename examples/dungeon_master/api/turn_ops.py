"""Play-loop operations for DM v2 turns (FR-477).

Pure operations on the story ``doc`` plus the single turn-graph invocation, kept
apart from the stage adapter so the structured turn side-channel (per-character
``intents``) lives in one place and ``session`` stays under the size gate.

A turn's ``recap`` is a plain ``{text, reviewed}`` entry — the same shape every
stage uses — which is what lets the generic weave/edit/accept act on a turn (J3).
``intents`` is the structured side-channel, never a stage entry.
"""

from __future__ import annotations

from examples.dungeon_master.api.graph_app import clean_text, field, get_app
from examples.dungeon_master.api.tree import (
    FINAL_CUT_GRAPH,
    TURN_GRAPH,
)
from examples.dungeon_master.api.world_state import format_world_state


def _chapter_card(doc: dict, cid: str) -> dict:
    """Read-only view of chapter ``cid``'s card (empty if absent)."""
    return doc.get("chapters", {}).get("cards", {}).get(cid, {})


def chapter_turns(doc: dict, cid: str) -> list[dict]:
    """Read-only view of chapter ``cid``'s played turns (FR-491 C; empty if none)."""
    return _chapter_card(doc, cid).get("turns") or []


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
    inherited = format_world_state(inherited_world_state(doc, cid)).strip()
    start = inherited or (
        "This is the opening chapter — there is no prior world state. Establish "
        "the world from the synopsis and this chapter's summary."
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
    return (
        f"THIS CHAPTER — {title} — its intended arc (the key events it drives "
        "toward, NOT events that have already happened):\n"
        f"{summary}\n\n"
        "STARTING WORLD STATE (established before this chapter begins — true at "
        "the START):\n"
        f"{start}\n\n"
        "WHAT HAS HAPPENED SO FAR IN THIS CHAPTER:\n"
        f"{so_far}"
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
    prev = prior_intents(doc, cid, n)
    cast = [
        {
            "name": chars["cards"][char_id].get("name") or char_id,
            "sheet": chars["cards"][char_id].get("text", ""),
            "previous": prev.get(char_id, ""),
        }
        for char_id in roster
    ]
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
    _clamp_phase(direction, prior)
    _canonicalize_beats(direction, prior)
    record["direction"] = direction
    return clean_text(result.get("recap"))


_PHASE_ORDER = {"opening": 0, "rising": 1, "climax": 2, "resolved": 3}


def _clamp_phase(direction: dict, prior: dict) -> None:
    """Floor this turn's ``phase`` at the prior turn's — the arc never runs backwards.

    ``phase`` is "where the arc stands"; once a scene reaches a higher phase it
    cannot un-reach it (FR-481 B2). A model that regresses (e.g. climax → rising
    on a later beat) is clamped up to the phase already declared, deterministically,
    so the recorded arc is monotonic regardless of what the model returns. A
    forward advance is left untouched; an unknown phase string is left as-is.
    """
    prior_phase = prior.get("phase", "") if prior else ""
    cur = direction.get("phase", "")
    if (
        prior_phase in _PHASE_ORDER
        and cur in _PHASE_ORDER
        and _PHASE_ORDER[cur] < _PHASE_ORDER[prior_phase]
    ):
        direction["phase"] = prior_phase


def _canonicalize_beats(direction: dict, prior: dict) -> None:
    """Accumulate ``beats_satisfied`` as free-text phrases, cumulatively (FR-491).

    The chapter plan is a free-text summary, not a parseable BEATS block, so the
    director's reported phrases are the vocabulary. Union this turn's phrases with
    the prior turn's satisfied set, de-duplicated and order-preserving, and record
    ``beats_total`` as 0 so the card shows no misleading ``k / 0`` (J4).
    """
    prior_beats = list((prior or {}).get("beats_satisfied") or [])
    raw = list(direction.get("beats_satisfied") or [])
    merged: list[str] = []
    for b in prior_beats + raw:
        if b not in merged:
            merged.append(b)
    direction["beats_satisfied"] = merged
    direction["beats_total"] = 0


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

    The fidelity signal the Final Cut must preserve. A chapter plan is a free-text
    ``summary``, not a parseable ``BEATS:`` block, so there is nothing to parse —
    the director already records ``beats_satisfied`` cumulatively per turn
    (``_canonicalize_beats``). This unions the chapter's turns' phrases,
    de-duplicated and order-preserving, so the finish is handed the canonical
    beats the play loop confirmed rather than re-deriving them.
    """
    beats: list[str] = []
    for t in chapter_turns(doc, cid):
        for b in (t.get("direction") or {}).get("beats_satisfied") or []:
            if b not in beats:
                beats.append(b)
    return beats


def final_cut_context(doc: dict, cid: str) -> dict:
    """Assemble chapter ``cid``'s finished arc as Final Cut graph variables (FR-492).

    A pure function over the story ``doc``: the chapter ``summary`` as the scene
    plan (standing in for the retired ``key_scene``), **every** played turn recap
    in order (``chapters.cards[cid].turns``, not the flat ``doc["turns"]`` the
    pre-chapter shape used), each turn's director ``phase`` with the pivotal turn
    marked, the beats the director confirmed (:func:`chapter_beats`), and a derived
    ``climax`` marker. This is the deterministic seam — the model is handed the
    assembled context and asked only for prose, never to recompute the arc's
    structure.
    """
    card = _chapter_card(doc, cid)
    summary = card.get("summary", "")
    turns = chapter_turns(doc, cid)
    climax_n = climax_turn(doc, cid)
    lines: list[str] = []
    for t in turns:
        n = t.get("n")
        recap = (t.get("recap") or {}).get("text", "")
        phase = (t.get("direction") or {}).get("phase", "")
        tag = f" [{phase}]" if phase else ""
        mark = "  ← THE CLIMAX" if n == climax_n else ""
        lines.append(f"Turn {n}{tag}{mark}: {recap}")
    beats = chapter_beats(doc, cid)
    return {
        "key_scene": summary,
        "arc": "\n\n".join(lines),
        "beats": "\n".join(f"- {b}" for b in beats),
        "climax": f"Turn {climax_n}" if turns else "",
    }


async def invoke_final_cut(
    doc: dict, cid: str, instruction: str = "", draft: str = ""
) -> str:
    """Compose chapter ``cid``'s continuous final text from its whole arc (FR-492).

    Runs ``final_cut.yaml`` once over :func:`final_cut_context` plus the current
    draft and a writer's instruction, and returns the cleaned narration — the
    chapter's beat-faithful final text. Reads the chapter's played turns; writes
    none of them.
    """
    result = await get_app(FINAL_CUT_GRAPH).ainvoke(
        {
            **final_cut_context(doc, cid),
            "draft": draft,
            "instruction": instruction,
            "final_cut": "",
        }
    )
    return clean_text(result.get("final_cut"))
