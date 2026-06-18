"""Deterministic continuity witness metrics for FR-508 A5.

Pure utilities that parse generation logs and story artifacts to compute
objective pass/fail signals for continuity enforcement quality.
"""

from __future__ import annotations

import json
import re

from examples.dungeon_master.api.world_state import parse_world_state

_LOG_LINE_LIFECYCLE = re.compile(r"Lifecycle gate violation:")
_LOG_LINE_MEMORY = re.compile(r"Continuity memory conflict:")
_LOG_LINE_DEAD_PROSE = re.compile(r"Dead character prose violation:")
_LOG_LINE_FINAL_CUT_REVISE = re.compile(r"Final cut revise applied:")
_DEAD_ACTIVE = re.compile(
    r"(confirmed_dead character cannot be active|"
    r"missing_presumed_dead character cannot be active)"
)


def parse_generation_log_metrics(log_text: str) -> dict:
    """Extract deterministic continuity counters from generation log text."""
    lines = (log_text or "").splitlines()
    lifecycle = 0
    memory = 0
    dead_alive = 0
    dead_prose = 0
    revise_applied = 0

    for line in lines:
        if _LOG_LINE_LIFECYCLE.search(line):
            lifecycle += 1
            if _DEAD_ACTIVE.search(line):
                dead_alive += 1
        elif _LOG_LINE_MEMORY.search(line):
            memory += 1
            if _DEAD_ACTIVE.search(line):
                dead_alive += 1
        elif _LOG_LINE_DEAD_PROSE.search(line):
            dead_prose += 1
        elif _LOG_LINE_FINAL_CUT_REVISE.search(line):
            revise_applied += 1

    turn_cap_timeout = "book gate did not open within turn_cap" in (log_text or "")
    return {
        "lifecycle_gate_violation_count": lifecycle,
        "continuity_memory_conflict_count": memory,
        "dead_alive_opening_contradiction_count": dead_alive,
        "dead_character_prose_violation_count": dead_prose,
        "final_cut_revise_applied_count": revise_applied,
        "book_gate_opened": not turn_cap_timeout,
    }


def parse_story_progress_metrics(story_doc: dict) -> dict:
    """Extract chapter progression counters from story artifact dict."""
    chapters = dict(story_doc.get("chapters") or {})
    order = list(chapters.get("order") or [])
    cards = dict(chapters.get("cards") or {})

    completed = 0
    total_turns = 0
    for cid in order:
        card = dict(cards.get(cid) or {})
        text = str(card.get("text") or "").strip()
        if bool(card.get("reviewed")) and bool(text):
            completed += 1
        total_turns += len(list(card.get("turns") or []))

    return {
        "planned_chapter_count": len(order),
        "completed_chapter_count": completed,
        "total_turns_used": total_turns,
    }


def _actor_continuity_flags(direction: dict, actor: str) -> list[str]:
    """The director ``continuity`` strings that name ``actor`` (FR-522, J3/J4).

    Case-insensitive substring match on each flag string — the single per-turn
    extraction reused for both the baseline and the replayed doc, so the two
    measurements cannot drift apart.
    """
    a = (actor or "").lower()
    return [
        str(f)
        for f in (direction or {}).get("continuity") or []
        if a and a in str(f).lower()
    ]


def _actor_is_acting(intents: dict, actor: str) -> bool:
    """Whether ``actor`` takes an action this turn (FR-522 J4 definition).

    The actor is *acting* when a key in the turn's ``intents`` matches the actor
    (case-insensitive substring) and that intent carries a non-empty ``intent`` OR
    a non-empty ``dialogue``. This is the deterministic counterpart to the
    director's flag, so a reader can separate "the actor really acted" (an
    intent-map fact) from "the director echoed an injected warning" (FR-521's
    metric-pollution confound).
    """
    a = (actor or "").lower()
    if not a:
        return False
    for char_id, item in (intents or {}).items():
        if a not in str(char_id).lower():
            continue
        intent_txt = str((item or {}).get("intent") or "").strip()
        dialogue_txt = str((item or {}).get("dialogue") or "").strip()
        if intent_txt or dialogue_txt:
            return True
    return False


def chapter_actor_flag_metrics(story_doc: dict, cid: str, actor: str) -> dict:
    """Per-turn continuity signal for ``actor`` within chapter ``cid`` (FR-522).

    Returns ``{chapter, actor, total, flag_turns, acting_turns, per_turn}`` where
    ``flag_turns`` counts turns whose director ``continuity`` names the actor and
    ``acting_turns`` counts turns where the actor takes an action (J4). The two are
    reported side by side so a continuity change that injects text into the scene
    (which ``running_scene`` feeds to all three turn nodes) cannot silently inflate
    the director-flag count without the independent intent-map acting count
    revealing it. Pure: reads only the doc shape, no LLM, no turn_ops import.
    """
    turns = list(
        ((story_doc.get("chapters") or {}).get("cards") or {}).get(cid, {}).get("turns")
        or []
    )
    per_turn: list[dict] = []
    flag_turns = 0
    acting_turns = 0
    for t in turns:
        flags = _actor_continuity_flags(t.get("direction") or {}, actor)
        acting = _actor_is_acting(t.get("intents") or {}, actor)
        if flags:
            flag_turns += 1
        if acting:
            acting_turns += 1
        per_turn.append(
            {
                "n": t.get("n"),
                "flags": flags,
                "flagged": bool(flags),
                "acting": acting,
            }
        )
    return {
        "chapter": cid,
        "actor": actor,
        "total": len(turns),
        "flag_turns": flag_turns,
        "acting_turns": acting_turns,
        "per_turn": per_turn,
    }


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

    For each occurrence of a token, the nearest proper name in the ``window``
    characters immediately BEFORE it is taken as the subject (e.g. "Arnulf is swept"
    → Arnulf; "presumed dead by the Aschenwulf" attributes nothing to Aschenwulf,
    which follows the token). This proximity rule is what makes the outline-time
    reversal detector precise: a summary paragraph naming several characters around
    a single death/return word no longer tars them all — only the grammatical
    subject of the removal/return is counted (FR-525, validated against 10024-BC
    where whole-unit co-occurrence over-fired on Hilde/Gunnar/Aschenwulf).
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


def _previous_chapter_id(story_doc: dict, cid: str) -> str | None:
    """The chapter id immediately before ``cid`` in play order, or None."""
    order = list(((story_doc.get("chapters") or {}).get("order")) or [])
    try:
        i = order.index(cid)
    except ValueError:
        return None
    return order[i - 1] if i > 0 else None


def _carried_living_characters(story_doc: dict, cid: str) -> list[dict]:
    """Characters the prior chapter carried forward as alive AND located.

    These are exactly the actors whose physical position the next chapter inherits
    as a hard fact — and therefore the actors a state-blind lethal beat can
    contradict.
    """
    prev = _previous_chapter_id(story_doc, cid)
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

    The OUTLINE-time dual of :func:`beat_coverage_gap` (FR-525). Where
    ``beat_coverage_gap`` reads a CLOSED chapter's committed ``world_state`` — which
    does not exist until the chapter is played — this reads only the chapter's
    AUTHORED text (``summary`` + ``beats``), so it runs at outline time, before any
    turn, where the fix belongs (``the_one_law``: normalize at the partitioner, not
    downstream).

    A chapter is an *over-pack* for an actor when the actor is the SUBJECT of a
    removal (``_TERMINAL_STATUS_TOKENS``) AND the SUBJECT of a return
    (``_RETURN_PRESENCE_TOKENS``) across the union ``[summary, *beats]`` — "subject"
    meaning the nearest proper name immediately before the token (:func:`_subjects_near`),
    not merely a name somewhere in the same paragraph (which over-fires on the many
    characters a summary names around one death/return word). The 16-turn cap (FR-501)
    cannot play both halves of such a reversal: the play realizes the removal, the cap
    force-closes, ``close_chapter`` commits the actor terminal, and the return becomes
    the phantom promise ``beat_coverage_gap`` later flags. Splitting the removal and
    the return into DIFFERENT chapters is the cure (FR-525).

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


def evaluate_fr508_a5(log_metrics: dict, story_metrics: dict) -> dict:
    """Evaluate FR-508 A5 pass/fail thresholds."""
    completed_equals_planned = int(
        story_metrics.get("completed_chapter_count") or 0
    ) == int(story_metrics.get("planned_chapter_count") or 0)
    checks = {
        "zero_lifecycle_gate_violations": (
            int(log_metrics.get("lifecycle_gate_violation_count") or 0) == 0
        ),
        "zero_continuity_memory_conflicts": (
            int(log_metrics.get("continuity_memory_conflict_count") or 0) == 0
        ),
        "zero_dead_alive_opening_contradictions": (
            int(log_metrics.get("dead_alive_opening_contradiction_count") or 0) == 0
        ),
        # A partial/in-progress artifact can lack timeout text while still
        # incomplete; require both gate-open signal and full completion.
        "book_gate_opened_before_turn_cap": (
            bool(log_metrics.get("book_gate_opened")) and completed_equals_planned
        ),
        "completed_equals_planned": completed_equals_planned,
    }
    return {
        "checks": checks,
        "pass": all(checks.values()),
    }


def _dead_prose_is_measurement_only(log_metrics: dict) -> bool:
    """FR-510: dead_character_prose_violation_count is a measurement target only."""
    return int(log_metrics.get("dead_character_prose_violation_count") or 0) == 0


def build_witness_summary(log_text: str, story_doc: dict) -> dict:
    """Compute full FR-508 A5 witness summary from raw artifacts."""
    log_metrics = parse_generation_log_metrics(log_text)
    story_metrics = parse_story_progress_metrics(story_doc)
    evaluation = evaluate_fr508_a5(log_metrics, story_metrics)
    return {
        "metrics": {**log_metrics, **story_metrics},
        "evaluation": evaluation,
    }


def render_markdown_table(summary: dict) -> str:
    """Render witness summary as a compact markdown table."""
    metrics = dict(summary.get("metrics") or {})
    checks = dict((summary.get("evaluation") or {}).get("checks") or {})
    lines = [
        "| Metric | Value |",
        "| --- | --- |",
        f"| lifecycle_gate_violation_count | {metrics.get('lifecycle_gate_violation_count', 0)} |",
        f"| continuity_memory_conflict_count | {metrics.get('continuity_memory_conflict_count', 0)} |",
        (
            "| dead_alive_opening_contradiction_count | "
            f"{metrics.get('dead_alive_opening_contradiction_count', 0)} |"
        ),
        (
            "| dead_character_prose_violation_count (measure) | "
            f"{metrics.get('dead_character_prose_violation_count', 0)} |"
        ),
        (
            "| final_cut_revise_applied_count (measure) | "
            f"{metrics.get('final_cut_revise_applied_count', 0)} |"
        ),
        f"| planned_chapter_count | {metrics.get('planned_chapter_count', 0)} |",
        f"| completed_chapter_count | {metrics.get('completed_chapter_count', 0)} |",
        f"| total_turns_used | {metrics.get('total_turns_used', 0)} |",
        f"| book_gate_opened | {metrics.get('book_gate_opened', False)} |",
        "",
        "| Check | Pass |",
        "| --- | --- |",
    ]
    for key, value in checks.items():
        lines.append(f"| {key} | {bool(value)} |")
    lines.append("")
    lines.append(f"Overall pass: {bool((summary.get('evaluation') or {}).get('pass'))}")
    return "\n".join(lines)


def render_json(summary: dict) -> str:
    """Render witness summary as deterministic JSON."""
    return json.dumps(summary, indent=2, sort_keys=True)
