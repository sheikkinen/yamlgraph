"""Outline-time continuity gap detectors (FR-536 Workstream C split).

The pure, state-blind witnesses run *before* prose generation: each reads only
authored beats / summary and (for two) the carried or committed ``world_state``
ledger, never an LLM and never ``turn_ops``. Split from ``witness_metrics`` so the
metrics-aggregation surface and the gap-detection surface stay under the 450-line
ceiling.

- :func:`seam_precondition_gap` — unbridged lethal seam (carried-alive actor
  killed by a hazard with no reposition beat bridging the move).
- :func:`beat_coverage_gap` — phantom-promise beats in a CLOSED chapter.
- :func:`reversal_pack_gap` — its outline-time dual (removal AND return packed
  into one chapter's authored text).
- :func:`unplayable_beat_gap` — a final beat authored as an unplayable time-skip
  epilogue the bounded scene can never enact.

A leaf over ``chapter_nav`` and ``world_state``; it never reaches ``turn_ops``.
"""

from __future__ import annotations

import re

from examples.dungeon_master.api import chapter_nav
from examples.dungeon_master.api.world_state import parse_world_state

# ── seam precondition gap (state-blind outliner witness) ─────────────────────
#
# Heuristic instrument (not a gate): the chapter outliner writes each chapter's
# beats from the synopsis ALONE, blind to the physical end-state the prior chapter
# carried forward. When a beat kills/loses an actor by an environmental hazard but
# the carried world_state places that actor at a non-hazard position and no beat
# moves them into reach first, the generator must silently teleport the actor to
# satisfy the beat — the "Arnulf safe on the higher bank → swept away by the flood"
# seam contradiction. This metric measures that *unbridged lethal seam* structurally
# over beats + carried state, so the defect is visible before any prose is read.

# Lethal/loss verbs an outline beat uses to remove an actor from the chapter.
_LIFECYCLE_EXIT_TOKENS = (
    "swept away",
    "swept down",
    "swept off",
    "drowned",
    "drowns",
    "drown",
    "lost to the",
    "carried downstream",
    "carried off",
    "taken by the",
    "pulled under",
    "killed",
    "slain",
    "dies",
    "death of",
)

# Verbs a beat uses to MOVE an actor from a carried safe position toward the
# hazard — the bridge the planner must author (in a preceding beat or inside the
# lethal beat itself) before a lethal exit is physically plausible.
_REPOSITION_TOKENS = (
    "edge",
    "back for",
    "goes back",
    "returns to",
    "slips",
    "loses footing",
    "loses his footing",
    "loses her footing",
    "pulled toward",
    "falls into",
    "reaches the water",
    "to the water",
    "into the water",
    "into the current",
    "down the bank",
    "off the bank",
    "off the ledge",
)


# Terminal lifecycle states a closed chapter's committed ``world_state`` records
# for an actor the play removed (dead/missing/lost). When a chapter's OWN beats
# also promise that actor's return/presence, the play could not have fulfilled
# both within its turn budget — the phantom-promise the FR-501 cap leaves behind.
_TERMINAL_STATUS_TOKENS = (
    "dead",
    "deceased",
    "missing",
    "presumed",
    "drowned",
    "lost",
    "swept",
    "gone",
)

# Tokens a beat uses to assert an actor is alive / returns / is present again —
# the claim a terminal committed status contradicts.
_RETURN_PRESENCE_TOKENS = (
    "reappear",
    "returns",
    "return of",
    "comes back",
    "back from",
    "back among",
    "alive",
    "survives",
    "survived",
    "rejoin",
    "found alive",
    "is found",
    "resurfaces",
    "washes up",
)


def _text_has_token(text: str, tokens: tuple[str, ...]) -> bool:
    """Whether ``text`` contains any token (case-insensitive substring)."""
    low = (text or "").lower()
    return any(tok in low for tok in tokens)


# Proper-name candidates in authored chapter text (summary/beats), used by the
# OUTLINE-time reversal detector where no committed ledger roster exists yet. A
# name is only counted when it co-occurs in a removal-bearing AND a return-bearing
# unit (see :func:`reversal_pack_gap`), so sentence-initial noise that lands in only
# one context is filtered by the intersection; the stopword set drops the most common
# capitalized non-names to keep the positive signal exact.
_PROPER_NAME_RE = re.compile(r"\b[A-Z][a-z]{2,}\b")
_NAME_STOPWORDS = frozenset(
    {
        "The",
        "Then",
        "When",
        "While",
        "And",
        "But",
        "Her",
        "His",
        "Their",
        "They",
        "She",
        "Him",
        "That",
        "This",
        "With",
        "From",
        "Into",
        "Over",
        "After",
        "Before",
        "Meanwhile",
    }
)


def _subjects_near(text: str, tokens: tuple[str, ...], window: int = 40) -> set[str]:
    """Names that are the likely SUBJECT of any ``tokens`` occurrence in ``text``.

    For each token occurrence, the nearest proper name in the ``window`` characters
    immediately BEFORE it is taken as the subject (e.g. "Arnulf is swept" → Arnulf).
    This proximity rule makes the outline-time reversal detector precise: a paragraph
    naming several characters around one death/return word no longer tars them all
    (FR-525, validated against 10024-BC where whole-unit co-occurrence over-fired).
    """
    low = (text or "").lower()
    out: set[str] = set()
    for tok in tokens:
        start = 0
        while True:
            i = low.find(tok, start)
            if i == -1:
                break
            pre = text[max(0, i - window) : i]
            names = [
                m.group(0)
                for m in _PROPER_NAME_RE.finditer(pre)
                if m.group(0) not in _NAME_STOPWORDS
            ]
            if names:
                out.add(names[-1])  # nearest name before the token = the subject
            start = i + len(tok)
    return out


def _beat_names_actor(beat: str, actor: str) -> bool:
    """Whether a beat string names ``actor`` (case-insensitive substring)."""
    a = (actor or "").lower()
    return bool(a) and a in (beat or "").lower()


def _carried_living_characters(story_doc: dict, cid: str) -> list[dict]:
    """Characters the prior chapter carried forward as alive AND located.

    These are exactly the actors whose physical position the next chapter inherits
    as a hard fact — and therefore the actors a state-blind lethal beat can
    contradict.
    """
    prev = chapter_nav.previous_chapter_id(story_doc, cid)
    if prev is None:
        return []
    cards = (story_doc.get("chapters") or {}).get("cards") or {}
    # Normalize at the boundary (the_one_law): older books (pre-FR-499A) store
    # ``world_state`` as a free-prose string, not a typed ledger; parse_world_state
    # yields the empty typed ledger for those rather than crashing on ``str.get``.
    ws = parse_world_state((cards.get(prev) or {}).get("world_state"))
    out: list[dict] = []
    for c in ws.get("characters") or []:
        status = str((c or {}).get("status") or "").lower()
        location = str((c or {}).get("location") or "").strip()
        if "alive" in status and location:
            out.append(
                {
                    "name": str((c or {}).get("name") or "").strip(),
                    "status": status,
                    "location": location,
                }
            )
    return out


def seam_precondition_gap(story_doc: dict, cid: str) -> dict:
    """Detect unbridged lethal seams in chapter ``cid`` (state-blind-outliner bug).

    For each actor the prior chapter carried forward as alive-and-located, find the
    first beat of ``cid`` that kills/loses them by hazard. The seam is *bridged* when
    a reposition beat moves the actor toward the hazard before (or within) that
    lethal beat, and *unbridged* — a gap — when no such movement exists, meaning the
    carried position and the death are physically incompatible with nothing in
    between. Pure: reads only beats + carried world_state, no LLM, no turn_ops.

    Returns ``{chapter, gap_count, carried_count, gaps:[{actor, carried_status,
    carried_location, exit_beat, exit_beat_index, bridged}]}``.
    """
    cards = (story_doc.get("chapters") or {}).get("cards") or {}
    beats = [str(b) for b in ((cards.get(cid) or {}).get("beats") or [])]
    carried = _carried_living_characters(story_doc, cid)

    gaps: list[dict] = []
    for actor_info in carried:
        actor = actor_info["name"]
        exit_idxs = [
            i
            for i, b in enumerate(beats)
            if _beat_names_actor(b, actor)
            and _text_has_token(b, _LIFECYCLE_EXIT_TOKENS)
        ]
        if not exit_idxs:
            continue
        first_exit = min(exit_idxs)
        bridged_before = any(
            _beat_names_actor(b, actor) and _text_has_token(b, _REPOSITION_TOKENS)
            for b in beats[:first_exit]
        )
        bridged_in_exit = _text_has_token(beats[first_exit], _REPOSITION_TOKENS)
        bridged = bool(bridged_before or bridged_in_exit)
        if not bridged:
            gaps.append(
                {
                    "actor": actor,
                    "carried_status": actor_info["status"],
                    "carried_location": actor_info["location"],
                    "exit_beat": beats[first_exit],
                    "exit_beat_index": first_exit,
                    "bridged": False,
                }
            )
    return {
        "chapter": cid,
        "gap_count": len(gaps),
        "carried_count": len(carried),
        "gaps": gaps,
    }


def beat_coverage_gap(story_doc: dict, cid: str) -> dict:
    """Detect phantom-promise beats in a CLOSED chapter ``cid`` (FR-501 cap fallout).

    A chapter's ``beats`` are the finite checklist the chapter promises to portray,
    but the play loop closes a chapter at ``CHAPTER_TURN_CAP`` turns whether or not
    every beat was reached (FR-501). When the outliner packs a *reversal* into one
    capped chapter — an actor is removed AND returns — the play typically realizes
    only the removal; the cap force-closes; ``close_chapter`` then *faithfully*
    commits the actor as terminal (dead/missing). The return beat becomes a phantom
    promise rendered into ``story.md`` that later chapters correctly ignore — read
    by a reviewer as a continuity break.

    This pure witness flags exactly that contradiction: for each actor the chapter's
    OWN committed ``world_state`` records in a terminal state, any beat of the SAME
    chapter that names them with a return/presence claim. No LLM, no recap parsing,
    no ``turn_ops``. Naturally a no-op on chapters not yet closed (empty/legacy
    ``world_state`` normalizes to no terminal characters).

    Returns ``{chapter, beat_count, gap_count, terminal_count, gaps:[{actor,
    ledger_status, beat, beat_index, reason}]}`` where ``reason`` is always
    ``"ledger_contradicts_beat"``.
    """
    cards = (story_doc.get("chapters") or {}).get("cards") or {}
    card = cards.get(cid) or {}
    beats = [str(b) for b in (card.get("beats") or [])]
    # Normalize at the boundary: legacy prose-string ledgers yield no characters.
    ws = parse_world_state(card.get("world_state"))

    terminal: dict[str, str] = {}
    for c in ws.get("characters") or []:
        name = str((c or {}).get("name") or "").strip()
        status = str((c or {}).get("status") or "").lower()
        if name and _text_has_token(status, _TERMINAL_STATUS_TOKENS):
            terminal[name] = status

    gaps: list[dict] = []
    for i, beat in enumerate(beats):
        for name, status in terminal.items():
            if _beat_names_actor(beat, name) and _text_has_token(
                beat, _RETURN_PRESENCE_TOKENS
            ):
                gaps.append(
                    {
                        "actor": name,
                        "ledger_status": status,
                        "beat": beat,
                        "beat_index": i,
                        "reason": "ledger_contradicts_beat",
                    }
                )
    return {
        "chapter": cid,
        "beat_count": len(beats),
        "gap_count": len(gaps),
        "terminal_count": len(terminal),
        "gaps": gaps,
    }


def reversal_pack_gap(card: dict) -> dict:
    """Detect a chapter that packs an actor's removal AND return into ONE chapter.

    The OUTLINE-time dual of :func:`beat_coverage_gap` (FR-525): it reads only the
    chapter's AUTHORED text (``summary`` + ``beats``), so it runs at outline time —
    before any turn, where the fix belongs (``the_one_law``: normalize at the
    partitioner, not downstream).

    A chapter is an *over-pack* for an actor when the actor is the SUBJECT of a removal
    (``_TERMINAL_STATUS_TOKENS``) AND the SUBJECT of a return (``_RETURN_PRESENCE_TOKENS``)
    across ``[summary, *beats]`` — "subject" = the nearest proper name immediately before
    the token (:func:`_subjects_near`), not merely any name in the same paragraph (which
    over-fires). The 16-turn cap (FR-501) cannot play both halves: the removal lands, the
    cap force-closes, and the return becomes the phantom promise ``beat_coverage_gap``
    flags. Splitting removal and return into DIFFERENT chapters is the cure (FR-525).

    Pure: reads only ``card``; no committed ledger, no LLM, no ``turn_ops``. Returns
    ``{gap_count, packed_actors, gaps:[{actor, removal_unit, return_unit,
    reason}]}`` where ``reason`` is always ``"removal_and_return_same_chapter"``.
    """
    units = [str(card.get("summary") or "")]
    units.extend(str(b) for b in (card.get("beats") or []))

    removal_unit: dict[str, str] = {}
    return_unit: dict[str, str] = {}
    for unit in units:
        for name in _subjects_near(unit, _TERMINAL_STATUS_TOKENS):
            removal_unit.setdefault(name, unit)
        for name in _subjects_near(unit, _RETURN_PRESENCE_TOKENS):
            return_unit.setdefault(name, unit)

    packed = sorted(set(removal_unit) & set(return_unit))
    gaps = [
        {
            "actor": name,
            "removal_unit": removal_unit[name],
            "return_unit": return_unit[name],
            "reason": "removal_and_return_same_chapter",
        }
        for name in packed
    ]
    return {
        "gap_count": len(gaps),
        "packed_actors": packed,
        "gaps": gaps,
    }


# FR-528: future-time-skip markers an EPILOGUE beat leads with. A chapter resolves
# only when its director marks every beat satisfied (``scene_complete = k == n``,
# turn_ops._apply_beat_ledger); a beat after a season passes can never be enacted
# inside the FR-501 16-turn cap, so it pins the chapter open. An epilogue OPENS with
# the jump ("By autumn, ..."), so the leading anchor (not mere co-occurrence of
# "settlement"/"feud") is the precise discriminator (validated against the 1002x-BC
# corpus: only 10025-BC CH8 flagged).
_TIME_SKIP_LEAD_TOKENS: tuple[str, ...] = (
    "by autumn",
    "by winter",
    "by spring",
    "by summer",
    "by the next",
    "by the following",
    "years later",
    "seasons later",
    "winters later",
    "moons later",
    "a year later",
    "a season later",
    "years after",
    "in the years",
    "in the seasons",
    "in the months",
    "generations later",
)


def unplayable_beat_gap(card: dict) -> dict:
    """Detect a chapter whose FINAL beat is an unplayable time-skip epilogue (FR-528).

    The OUTLINE-time cure for the no-progress tail FR-527 only treated as a symptom.
    A chapter's only natural exit is its director computing ``scene_complete =
    (k == n)`` (``turn_ops._apply_beat_ledger``). A FINAL beat authored as a time-skip
    epilogue (resolution arrives only after a season passes) can never be enacted in
    the bounded 16-turn scene (FR-501), so ``scene_complete`` never fires and the
    chapter rides the cap. Normalize at the partitioner boundary (``the_one_law``):
    catch the epilogue at outline time, never downstream.

    The signal is precise by leading-anchor: the final beat (case-insensitively,
    after stripping leading quotes/dashes) STARTS with a future-time-skip marker
    (:data:`_TIME_SKIP_LEAD_TOKENS`) — a beat that merely NAMES a settlement the scene
    CAN play is not flagged (avoids the ``plausible_wrong_answer`` over-fire). Only the
    FINAL beat is checked.

    Pure: reads only ``card['beats']``; no committed ledger, no LLM, no ``turn_ops``.
    Returns ``{gap_count, gaps:[{beat_index, beat, marker, reason}]}`` where ``reason``
    is always ``"final_beat_time_skip_epilogue"``.
    """
    beats = [str(b).strip() for b in (card.get("beats") or []) if str(b).strip()]
    if not beats:
        return {"gap_count": 0, "gaps": []}
    final = beats[-1]
    low = final.lower().lstrip("\"'\u2014\u2013- \t")
    marker = next((tok for tok in _TIME_SKIP_LEAD_TOKENS if low.startswith(tok)), None)
    if marker is None:
        return {"gap_count": 0, "gaps": []}
    return {
        "gap_count": 1,
        "gaps": [
            {
                "beat_index": len(beats) - 1,
                "beat": final,
                "marker": marker,
                "reason": "final_beat_time_skip_epilogue",
            }
        ],
    }
