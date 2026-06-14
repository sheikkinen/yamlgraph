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
    _clamp_phase(direction, turn_direction(doc, n - 1))
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
