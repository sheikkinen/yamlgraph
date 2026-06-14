"""Play-loop operations for DM v2 turns (FR-477).

Pure operations on the story ``doc`` plus the single turn-graph invocation, kept
apart from the stage adapter so the structured turn side-channel (per-character
``intents``) lives in one place and ``session`` stays under the size gate.

A turn's ``recap`` is a plain ``{text, reviewed}`` entry — the same shape every
stage uses — which is what lets the generic weave/edit/accept act on a turn (J3).
``intents`` is the structured side-channel, never a stage entry.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from examples.dungeon_master.api.graph_app import clean_text, field, get_app
from examples.dungeon_master.api.tree import TURN_GRAPH


def turn_record(doc: dict, n: int) -> dict:
    """The ``turns[n-1]`` record ``{n, intents, recap}`` (created if absent)."""
    turns = doc.setdefault("turns", [])
    while len(turns) < n:
        m = len(turns) + 1
        turns.append({"n": m, "intents": {}, "recap": {"text": "", "reviewed": False}})
    rec = turns[n - 1]
    rec.setdefault("intents", {})
    rec.setdefault("recap", {"text": "", "reviewed": False})
    return rec


def turn_direction(doc: dict, n: int) -> dict:
    """The director's ``direction`` side-channel for turn ``n`` (empty if absent).

    A structured ``{phase, establishing, beats_satisfied, scene_complete, steer,
    continuity}`` judgement produced alongside the turn's intents (FR-479 J4);
    the recap entry shape stays ``{text, reviewed}`` (FR-477 J3).
    """
    turns = doc.get("turns", [])
    if n < 1 or len(turns) < n:
        return {}
    return turns[n - 1].get("direction") or {}


def turn_intents(doc: dict, chars: dict, n: int) -> list[dict]:
    """The turn's intents as ordered ``[{name, thinking, intent}]`` cards."""
    turns = doc.get("turns", [])
    if n < 1 or len(turns) < n:
        return []
    intents = turns[n - 1].get("intents", {})
    out: list[dict] = []
    for cid in chars["roster"]:
        if cid in intents:
            out.append(
                {
                    "name": chars["cards"].get(cid, {}).get("name") or cid,
                    "thinking": intents[cid].get("thinking", ""),
                    "intent": intents[cid].get("intent", ""),
                }
            )
    return out


def prior_intents(doc: dict, n: int) -> dict:
    """Each character's intent from turn ``n-1`` (empty before turn 2, J4)."""
    turns = doc.get("turns", [])
    if n < 2 or len(turns) < n - 1:
        return {}
    prev = turns[n - 2].get("intents", {})
    return {cid: v.get("intent", "") for cid, v in prev.items()}


def running_scene(doc: dict, n: int) -> str:
    """The play context for turn ``n``: the scene plan + what has actually happened.

    The key scene is a *plan* (SUMMARY/BEATS/END describe the intended arc the
    scene drives toward, not events that have already happened); the accumulated
    recaps are the real history. Labelling them apart stops the model from
    reading the scene's ending as established fact and replaying the aftermath —
    on turn 1 nothing has happened yet, so play must begin at the START (J4).
    """
    plan = doc.get("key_scene", {}).get("text", "")
    turns = doc.get("turns", [])
    prior = [t.get("recap", {}).get("text", "") for t in turns[: n - 1]]
    prior = [p for p in prior if p.strip()][-3:]
    so_far = (
        "\n\n".join(prior)
        if prior
        else (
            "Nothing has happened yet — the scene is just beginning. Only the "
            "START state is true; none of the BEATS and not the END have occurred."
        )
    )
    return (
        "THE SCENE (the planned arc — its SUMMARY, BEATS, and END are the "
        "intended destination the scene drives toward, NOT events that have "
        "already happened):\n"
        f"{plan}\n\n"
        "WHAT HAS HAPPENED SO FAR:\n"
        f"{so_far}"
    )


async def invoke_turn(doc: dict, chars: dict, n: int, instruction: str = "") -> str:
    """Run the turn graph for turn ``n``: write its intents + direction, return its recap.

    Builds one ``{name, sheet, previous}`` bundle per reviewed character (J1),
    the bounded running scene (key scene + last-3 recaps, J4) and each
    character's prior intent, runs ``turn.yaml`` once (map → direct → recap), records
    ``turns[n].intents`` keyed by character id and the director's
    ``turns[n].direction`` side-channel (FR-479 J4), and returns the recap text.
    The stage interface stays a pure ``str -> str``; this turn path owns both
    structured side-channels (J3).
    """
    roster = [
        cid for cid in chars["roster"] if chars["cards"].get(cid, {}).get("reviewed")
    ]
    prev = prior_intents(doc, n)
    cast = [
        {
            "name": chars["cards"][cid].get("name") or cid,
            "sheet": chars["cards"][cid].get("text", ""),
            "previous": prev.get(cid, ""),
        }
        for cid in roster
    ]
    result = await get_app(TURN_GRAPH).ainvoke(
        {
            "cast": cast,
            "scene": running_scene(doc, n),
            "turn_n": str(n),
            "instruction": instruction,
            "intents": [],
            "direction": {},
            "recap": "",
        }
    )
    items = result.get("intents") or []
    record = turn_record(doc, n)
    record["intents"] = {
        cid: {"thinking": field(item, "thinking"), "intent": field(item, "intent")}
        for cid, item in zip(roster, items, strict=False)
    }
    direction = _direction_dict(result.get("direction"))
    prior = turn_direction(doc, n - 1)
    _clamp_phase(direction, prior)
    _canonicalize_beats(direction, prior, doc.get("key_scene", {}).get("text", ""))
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


_SECTION_RE = re.compile(r"^[A-Z][A-Z/ ]*:")
_BEAT_FLOOR = 0.6
_BEAT_MARGIN = 0.1


def parse_beats(key_scene_text: str) -> list[str]:
    """The canonical ``BEATS`` bullets from a frozen key-scene card (FR-482).

    The key scene lists ``BEATS:`` as ``- `` bullets between that label and the
    next uppercase section label (e.g. ``END:``). Returns the beat phrases in
    scene order; empty when the card has no parseable BEATS block.
    """
    beats: list[str] = []
    in_beats = False
    for line in key_scene_text.splitlines():
        stripped = line.strip()
        if _SECTION_RE.match(stripped):
            in_beats = stripped.upper().startswith("BEATS:")
            continue
        if in_beats and stripped.startswith("- "):
            beats.append(stripped[2:].strip())
    return beats


def _norm(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — for fuzzy beat matching."""
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split())


def _match_beat(phrase: str, canonical: list[str]) -> int | None:
    """Index of the canonical beat ``phrase`` satisfies, or ``None`` (FR-482 M1).

    Ranks every canonical beat by ``difflib`` ratio on normalised text and
    accepts the best **only if** it clears an absolute floor AND beats the
    runner-up by a margin (so a phrase equally close to two beats is dropped, not
    mis-assigned). A phrase that clears nothing is dropped, never invented
    (Commandment 6).
    """
    p = _norm(phrase)
    scored = sorted(
        (
            (SequenceMatcher(None, p, _norm(b)).ratio(), i)
            for i, b in enumerate(canonical)
        ),
        reverse=True,
    )
    if not scored or scored[0][0] < _BEAT_FLOOR:
        return None
    if len(scored) > 1 and scored[0][0] - scored[1][0] < _BEAT_MARGIN:
        return None
    return scored[0][1]


def _canonicalize_beats(direction: dict, prior: dict, key_scene_text: str) -> None:
    """Bind ``beats_satisfied`` to the scene's canonical BEATS, cumulatively (FR-482).

    Matches each phrase the director reported this turn onto the frozen scene's
    BEATS vocabulary, unions it with the prior turn's satisfied set, and records
    the cumulative subset **in scene order** with a ``beats_total`` count. When
    the scene has no parseable BEATS block, there is nothing to bind to: the raw
    phrases are kept (still cumulative and de-duplicated) and ``beats_total`` is 0
    so the card shows no misleading ``k / 0`` (J4).
    """
    canonical = parse_beats(key_scene_text)
    prior_beats = list((prior or {}).get("beats_satisfied") or [])
    raw = list(direction.get("beats_satisfied") or [])
    if not canonical:
        merged: list[str] = []
        for b in prior_beats + raw:
            if b not in merged:
                merged.append(b)
        direction["beats_satisfied"] = merged
        direction["beats_total"] = 0
        return
    index_of = {b: i for i, b in enumerate(canonical)}
    satisfied: set[int] = {index_of[b] for b in prior_beats if b in index_of}
    for phrase in raw:
        i = _match_beat(phrase, canonical)
        if i is not None:
            satisfied.add(i)
    direction["beats_satisfied"] = [canonical[i] for i in sorted(satisfied)]
    direction["beats_total"] = len(canonical)


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
