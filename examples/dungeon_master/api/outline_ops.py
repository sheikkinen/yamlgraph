"""Whole-book outline operations: synopsis -> ordered chapter partition.

Split out of ``chapter_ops`` (FR-536 Workstream C). Owns the two outline graph
invocations (initial partition + state-aware re-outline) and the deterministic
outline-quality gates that re-roll the partitioner: the FR-525 removal-and-return
reversal pack and the FR-528 unplayable time-skip epilogue. Both public functions
are PURE reads of the story ``doc`` — they invoke a graph and return its
normalized output, never mutating ``doc`` (the adapter owns the writes).
"""

from __future__ import annotations

from examples.dungeon_master.api import chapter_nav
from examples.dungeon_master.api.card_gate import gate_chapter_card
from examples.dungeon_master.api.composition_gap import composition_gap
from examples.dungeon_master.api.graph_app import field, get_app
from examples.dungeon_master.api.seam_packet import format_seam_packet
from examples.dungeon_master.api.tree import (
    CHAPTER_OUTLINE_GRAPH,
    CHAPTER_REOUTLINE_GRAPH,
)
from examples.dungeon_master.api.world_state import format_world_state


def _beat_list(item: object) -> list[str]:
    """The ordered key-event beats from an outline entry (FR-503; ``[]`` if absent).

    The director selects satisfied beats by number from this finite list, so the
    phrases are kept verbatim (not coerced through ``field``, which flattens to a
    single string). Blank entries are dropped; a missing/non-list ``beats`` yields
    an empty list, which :func:`_require_beats` then rejects at the boundary.
    """
    raw = item.get("beats") if isinstance(item, dict) else getattr(item, "beats", None)
    if not isinstance(raw, list):
        return []
    return [str(b).strip() for b in raw if str(b).strip()]


def _cast_list(item: object) -> list[str]:
    """The focal cast names from an outline entry (FR-537; ``[]`` if absent).

    The principals the chapter is *about* — the scope the play loop narrows the
    animated roster to. Kept as verbatim display strings (not coerced through
    ``field``); blank entries dropped; a missing/non-list ``cast`` yields ``[]``,
    which the ``expand_chapters`` boundary then normalizes against the roster.
    """
    raw = item.get("cast") if isinstance(item, dict) else getattr(item, "cast", None)
    if not isinstance(raw, list):
        return []
    return [str(c).strip() for c in raw if str(c).strip()]


def _state_field(item: object, key: str) -> str:
    """An authored entry/exit state contract from an outline entry (FR-540; ``""`` if absent).

    The 1-2 sentence configuration true at a chapter's open (``entry_state``) or
    close (``exit_state``) -- the outline-time *state* seam the composition gate
    validates. A missing or non-string value yields ``""`` so a pre-FR-540 outline
    (no contracts) degrades additively to today's behavior (``the_one_law``: the
    absent contract is normalized at the outline boundary, not downstream).
    """
    raw = item.get(key) if isinstance(item, dict) else getattr(item, key, None)
    return str(raw).strip() if isinstance(raw, str) else ""


def _require_beats(chapters: list[dict]) -> list[dict]:
    """Reject any chapter that carries no enumerated ``beats`` (FR-504 contract).

    FR-503 replaced the director's unbounded free-text beat judgement with a
    finite, enumerated beat ledger but kept the FR-491 free-text path alive as the
    ``N == 0`` fallback. FR-504 retires that fallback: a non-empty ``beats`` list
    is now a validated boundary contract, normalized where the outline enters
    (``the_one_law``), so there is exactly one beat-judgement regime downstream and
    no chapter can silently fall back. Returns ``chapters`` unchanged when every
    one carries beats; raises otherwise (Commandment 6: no silent fallback).
    """
    for i, ch in enumerate(chapters, start=1):
        if not ch.get("beats"):
            raise ValueError(
                f"chapter {i} ({ch.get('title') or '?'!r}) outline carries no beats; "
                "every chapter must enumerate its key-event beats (FR-504)"
            )
    return chapters


# FR-525: how many times the outliner re-rolls when a chapter packs a removal AND
# return for one actor before raising (Commandment 6: no silent fallback). Three
# attempts = the first roll plus two corrected re-rolls.
_OUTLINE_MAX_ATTEMPTS = 3


def _packed_chapters(chapters: list[dict]) -> list[dict]:
    """Chapters that pack a same-actor removal-and-return (FR-525 over-pack).

    Pure: routes each authored chapter card through the shared per-card battery
    (:func:`card_gate.gate_chapter_card`) and returns ``[{index, title, actors}]``
    for every chapter with a ``reversal`` gap -- the un-playable reversals the
    16-turn cap (FR-501) would force-close mid-arc.
    """
    out: list[dict] = []
    for i, ch in enumerate(chapters, start=1):
        actors = sorted(
            {g["actor"] for g in gate_chapter_card(ch) if g["kind"] == "reversal"}
        )
        if actors:
            out.append(
                {
                    "index": i,
                    "title": str(ch.get("title") or ""),
                    "actors": actors,
                }
            )
    return out


def _reversal_feedback(packed: list[dict]) -> str:
    """The correction block appended to the synopsis on an outline re-roll (FR-525).

    Names each offending chapter and the actor(s) it both removes and returns, and
    restates the hard rule, so the re-invoked outliner moves the return to a later
    chapter rather than repeating the pack.
    """
    lines = [
        f'- Chapter {p["index"]} ("{p["title"]}") removes AND returns: '
        f"{', '.join(p['actors'])}"
        for p in packed
    ]
    return (
        "\n\nCORRECTION — your previous outline VIOLATED a hard rule: a character "
        "removed within a chapter must not also return within that same chapter. "
        "A chapter is played under a fixed turn budget and cannot portray both a "
        "loss and the return that reverses it. Re-author so each of these losses "
        "and its return are in DIFFERENT chapters (author the return as a beat of a "
        "LATER chapter):\n" + "\n".join(lines)
    )


def _unplayable_chapters(chapters: list[dict]) -> list[dict]:
    """Chapters whose FINAL beat is an unplayable time-skip epilogue (FR-528).

    Pure: routes each authored chapter card through the shared per-card battery
    (:func:`card_gate.gate_chapter_card`) and returns ``[{index, title, beat,
    marker}]`` for every chapter with an ``unplayable`` gap (last beat LEADS with a
    future-time-skip, "By autumn, …"). A bounded scene (FR-501) can never enact such
    a beat, so ``scene_complete = (k == n)`` never fires and the chapter rides the cap
    (the no-progress tail FR-527 mis-treated as a play symptom). The cure normalizes
    at the partitioner boundary (``the_one_law``).
    """
    out: list[dict] = []
    for i, ch in enumerate(chapters, start=1):
        unplayable = [g for g in gate_chapter_card(ch) if g["kind"] == "unplayable"]
        if unplayable:
            g = unplayable[0]
            out.append(
                {
                    "index": i,
                    "title": str(ch.get("title") or ""),
                    "beat": g["beat"],
                    "marker": g["marker"],
                }
            )
    return out


def _unplayable_feedback(unplayable: list[dict]) -> str:
    """The correction block appended to the synopsis on an outline re-roll (FR-528).

    Names each offending chapter and its time-skip final beat, and restates the hard
    rule, so the re-invoked outliner either re-authors the final beat as a
    present-tense in-scene resolution OR folds the epilogue into the chapter
    ``summary`` (narration), never leaving it as a beat the bounded scene cannot
    enact.
    """
    lines = [
        f'- Chapter {p["index"]} ("{p["title"]}") final beat leads with '
        f'"{p["marker"]}": {p["beat"]}'
        for p in unplayable
    ]
    return (
        "\n\nCORRECTION — your previous outline VIOLATED a hard rule: a chapter's "
        "FINAL beat must be a present-tense event the scene can enact within its "
        "turn budget. A beat that resolves only after a time-skip ('By autumn, …', "
        "'Years later, …') can never be played, so the chapter never completes. "
        "Re-author each of these final beats as an in-scene, present-tense "
        "resolution, OR move the time-skip aftermath into that chapter's SUMMARY "
        "as closing narration (not a beat):\n" + "\n".join(lines)
    )


def _composition_feedback(gaps: list[dict]) -> str:
    """The correction block appended to the synopsis on an outline re-roll (FR-540).

    Names each non-composing adjacent pair and the configuration it contradicts, and
    restates the hard rule, so the re-invoked outliner authors chapter N+1 to open
    FROM chapter N's close (or inserts a bridging chapter) rather than jumping the
    seam.
    """
    lines = [
        f'- Chapter {g["from_chapter"]} closes "{g["exit_state"]}" but '
        f'chapter {g["to_chapter"]} opens "{g["entry_state"]}" '
        f"({g['concept']} contradiction)"
        for g in gaps
    ]
    return (
        "\n\nCORRECTION — your previous outline VIOLATED a hard rule: each chapter "
        "must OPEN from the configuration the previous chapter LEFT. The following "
        "adjacent chapters do not compose — one ends in a configuration the next "
        "contradicts with no transition. Re-author so each chapter's entry_state "
        "follows from the prior chapter's exit_state, or insert a bridging chapter "
        "that carries the change:\n" + "\n".join(lines)
    )


async def outline_chapters(doc: dict) -> list[dict]:
    """Split the accepted synopsis into an ordered list of ``{title, summary, beats}``.

    Runs ``chapter_outline.yaml`` once over the synopsis and returns the structured
    chapter list (J1: a titled paragraph per chapter — a shape a plain line-split
    cannot hold). Raises rather than substituting an empty book when the model
    returns no chapters, and rejects any chapter without enumerated ``beats``
    (:func:`_require_beats`, FR-504 contract) — both per Commandment 6: no silent
    fallback.

    FR-525 — split-gate: the partitioner can pack a death-and-return *reversal* into
    one chapter, but the play loop closes a chapter at ``CHAPTER_TURN_CAP`` turns
    (FR-501) and cannot portray both a loss and its reversing return. A chapter that
    removes AND returns the same actor therefore force-closes mid-reversal, leaving
    the return a phantom (``gap_detectors.beat_coverage_gap``). The cure normalizes
    at the partitioner boundary (``the_one_law``): after each outline the
    deterministic :func:`gap_detectors.reversal_pack_gap` checks every chapter; on a
    pack the outline is re-invoked with the violation fed back (bounded retry), then
    raises (no silent fallback) — never emitting a packed outline downstream.

    FR-528 — epilogue-gate: the partitioner can also author a chapter's FINAL beat as
    a time-skip epilogue ("By autumn, … a settlement that ends the feud"). A chapter
    resolves only when its director computes ``scene_complete = (k == n)`` over
    ``n = len(beats)``; a beat that resolves only after a season passes can never be
    enacted in the 16-turn cap, so ``scene_complete`` never fires and the chapter
    rides the cap (the no-progress tail FR-527 mis-treated downstream). The same
    boundary cure: :func:`gap_detectors.unplayable_beat_gap` checks every chapter;
    on a hit the outline is re-invoked instructing an in-scene resolution or a summary
    fold (bounded retry), then raises — never emitting a cap-riding chapter.
    """
    synopsis = doc.get("synopsis", {}).get("text", "")
    feedback = ""
    packed: list[dict] = []
    unplayable: list[dict] = []
    composition: list[dict] = []
    for _ in range(_OUTLINE_MAX_ATTEMPTS):
        result = await get_app(CHAPTER_OUTLINE_GRAPH).ainvoke(
            {"synopsis": synopsis + feedback, "outline": {}}
        )
        outline = result.get("outline") or {}
        raw = outline.get("chapters") if isinstance(outline, dict) else None
        chapters = [
            {
                "title": field(item, "title"),
                "summary": field(item, "summary"),
                "beats": _beat_list(item),
                "cast": _cast_list(item),
                "entry_state": _state_field(item, "entry_state"),
                "exit_state": _state_field(item, "exit_state"),
            }
            for item in (raw or [])
        ]
        if not chapters:
            raise ValueError("chapter outline returned no chapters")
        chapters = _require_beats(chapters)
        packed = _packed_chapters(chapters)
        unplayable = _unplayable_chapters(chapters)
        composition = composition_gap(chapters)["gaps"]
        if not packed and not unplayable and not composition:
            return chapters
        feedback = ""
        if packed:
            feedback += _reversal_feedback(packed)
        if unplayable:
            feedback += _unplayable_feedback(unplayable)
        if composition:
            feedback += _composition_feedback(composition)
    if packed:
        raise ValueError(
            "chapter outline packs a removal-and-return reversal into one chapter "
            f"after {_OUTLINE_MAX_ATTEMPTS} attempts (FR-525); a character lost within "
            f"a chapter must return in a LATER chapter: {packed}"
        )
    if unplayable:
        raise ValueError(
            "chapter outline authors an unplayable time-skip epilogue as a chapter's "
            f"final beat after {_OUTLINE_MAX_ATTEMPTS} attempts (FR-528); a final beat "
            "must be an in-scene present-tense resolution, not a post-time-skip aftermath: "
            f"{unplayable}"
        )
    raise ValueError(
        "chapter outline authors non-composing adjacent chapters after "
        f"{_OUTLINE_MAX_ATTEMPTS} attempts (FR-540); each chapter must open from the "
        f"configuration the previous chapter left: {composition}"
    )


async def reoutline_chapter_beats(doc: dict, cid: str) -> list[str]:
    """Re-author chapter ``cid``'s beats from the prior chapter's carried state (FR-523).

    The chapter outliner is state-blind: it writes every chapter's beats from the
    synopsis alone (``outline_chapters``), so a lethal/exit beat can land on an actor
    the prior chapter left safe, with no beat bridging the two — the seam-teleport
    condemned by :func:`gap_detectors.seam_precondition_gap`. This re-derives the
    BEATS of one not-yet-played chapter from the synopsis + this chapter's FROZEN
    title/summary + the PRIOR chapter's committed ``world_state``/``seam_packet``, so
    the planner can author the bridging reposition beat the death requires — killing
    the contradiction in the spec (``the_one_law``: normalize at the outliner
    boundary, not downstream in the director/prose).

    Pure (J2): invokes ``CHAPTER_REOUTLINE_GRAPH`` and returns the parsed,
    ``_require_beats``-validated list; NEVER mutates ``doc`` and NEVER re-authors the
    title or summary (J4). Raises rather than substituting an empty beat list
    (Commandment 6: no silent fallback).

    FR-555 — reversal-gate the second authoring boundary: the partitioner gates its
    output with :func:`gap_detectors.reversal_pack_gap` (FR-525), but this re-outline
    re-authors beats from the FULL synopsis and previously committed them validating
    only ``_require_beats``. A synopsis that states an actor's loss AND later revival
    can therefore re-pack the removal-and-return reversal into one chapter through
    this ungated boundary (the 10036-BC Ch3 early-reveal: frozen summary "presumed
    dead" + a beat asserting the actor is "alive"). The cure mirrors
    ``outline_chapters``: after each re-outline build the candidate card from the
    FROZEN title/summary + the NEW beats, run the SAME per-card battery
    (``card_gate.gate_chapter_card``), re-invoke with the matching correction
    feedback (bounded by ``_OUTLINE_MAX_ATTEMPTS``), then raise (no silent fallback)
    -- never returning an un-playable beat list.

    FR-558 -- the battery generalized: this boundary routes through the SAME
    ``gate_chapter_card`` the typed setter and ``outline_chapters`` use, so it now
    also rejects an unplayable time-skip-epilogue final beat (FR-528), not only the
    removal-and-return reversal (FR-555) -- one gate, every authoring path.
    """
    card = doc.get("chapters", {}).get("cards", {}).get(cid, {})
    title = card.get("title", "")
    summary = card.get("summary", "")
    synopsis = doc.get("synopsis", {}).get("text", "")
    prior_world_state = format_world_state(chapter_nav.inherited_world_state(doc, cid))
    prior_seam_packet = format_seam_packet(chapter_nav.inherited_seam_packet(doc, cid))
    feedback = ""
    packed: list[dict] = []
    unplayable: list[dict] = []
    for _ in range(_OUTLINE_MAX_ATTEMPTS):
        result = await get_app(CHAPTER_REOUTLINE_GRAPH).ainvoke(
            {
                "synopsis": synopsis + feedback,
                "chapter_title": title,
                "chapter_summary": summary,
                "prior_world_state": prior_world_state,
                "prior_seam_packet": prior_seam_packet,
                "reoutline": {},
            }
        )
        beats = _beat_list(result.get("reoutline") or {})
        if not beats:
            raise ValueError(
                f"chapter {cid} re-outline returned no beats (FR-523); every chapter "
                "must enumerate its key-event beats"
            )
        candidate = {"title": title, "summary": summary, "beats": beats}
        gaps = gate_chapter_card(candidate)
        if not gaps:
            return beats
        actors = sorted({g["actor"] for g in gaps if g["kind"] == "reversal"})
        packed = [{"index": cid, "title": title, "actors": actors}] if actors else []
        unplayable = [
            {"index": cid, "title": title, "beat": g["beat"], "marker": g["marker"]}
            for g in gaps
            if g["kind"] == "unplayable"
        ]
        feedback = ""
        if packed:
            feedback += _reversal_feedback(packed)
        if unplayable:
            feedback += _unplayable_feedback(unplayable)
    if packed:
        raise ValueError(
            f"chapter {cid} re-outline packs a removal-and-return reversal after "
            f"{_OUTLINE_MAX_ATTEMPTS} attempts (FR-555); the frozen summary removes an "
            "actor the re-authored beats then return within the same chapter -- author "
            f"the return as a beat of a LATER chapter: {packed}"
        )
    raise ValueError(
        f"chapter {cid} re-outline authors an unplayable time-skip epilogue as its "
        f"final beat after {_OUTLINE_MAX_ATTEMPTS} attempts (FR-558); a final beat must "
        "be an in-scene present-tense resolution, not a post-time-skip aftermath: "
        f"{unplayable}"
    )
