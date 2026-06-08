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
    """Key scene + a bounded digest of the last 3 prior turn recaps (J4)."""
    scene = doc.get("key_scene", {}).get("text", "")
    turns = doc.get("turns", [])
    prior = [t.get("recap", {}).get("text", "") for t in turns[: n - 1]]
    prior = [p for p in prior if p.strip()][-3:]
    if prior:
        scene = scene + "\n\n" + "\n\n".join(prior)
    return scene


async def invoke_turn(doc: dict, chars: dict, n: int, instruction: str = "") -> str:
    """Run the turn graph for turn ``n``: write its intents, return its recap.

    Builds one ``{name, sheet, previous}`` bundle per reviewed character (J1),
    the bounded running scene (key scene + last-3 recaps, J4) and each
    character's prior intent, runs ``turn.yaml`` once, records ``turns[n].intents``
    keyed by character id, and returns the recap text. The stage interface stays a
    pure ``str -> str``; this turn path owns the structured side-channel (J3).
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
            "recap": "",
        }
    )
    items = result.get("intents") or []
    record = turn_record(doc, n)
    record["intents"] = {
        cid: {"thinking": field(item, "thinking"), "intent": field(item, "intent")}
        for cid, item in zip(roster, items, strict=False)
    }
    return clean_text(result.get("recap"))
