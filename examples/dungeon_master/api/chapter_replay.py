"""FR-522: the single-chapter replay driver (the impure half of the witness).

Re-plays ONE chapter of a finished story from its inherited start, holding every
prior chapter constant, so a continuity change is measured as a controlled
experiment (one changed variable, same inherited state). This module owns the part
that awaits the LLM (``replay_chapter``); the deterministic measurement lives in
``witness_metrics.chapter_actor_flag_metrics`` so the two never share a module
(J3). The driver takes the doc as an argument and deep-copies it internally, so a
test can monkeypatch ``turn_ops.invoke_turn`` and prove isolation without a live
model (J2).

This is a **witness instrument, not a gate**: efficacy is a non-deterministic,
live-LLM property and must never be wired into CI (J6). Its measurement functions
are unit-tested; its live replay is run by hand.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from examples.dungeon_master.api import doc_ops, turn_ops


async def replay_chapter(doc: dict, cid: str, *, turn_cap: int | None = None) -> dict:
    """Return a fresh doc with chapter ``cid`` re-played from its inherited start.

    Deep-copies ``doc`` (the caller's doc is never mutated), wipes only chapter
    ``cid`` via :func:`turn_ops.reset_chapter_for_replay`, then drives the real
    ``turn_ops.invoke_turn`` (map → direct → recap) turn by turn until the
    director reports ``scene_complete`` or the per-chapter cap is hit — the exact
    loop the live play uses. ``turn_cap`` defaults to
    :data:`turn_ops.CHAPTER_TURN_CAP`.
    """
    replay = copy.deepcopy(doc)
    chars = doc_ops.characters(replay)
    turn_ops.reset_chapter_for_replay(replay, cid)
    cap = turn_cap if turn_cap is not None else turn_ops.CHAPTER_TURN_CAP
    for n in range(1, cap + 1):
        recap = await turn_ops.invoke_turn(replay, chars, cid, n)
        rec = turn_ops.turn_record(replay, cid, n)
        rec["recap"] = {"text": recap, "reviewed": False}
        if turn_ops.chapter_should_close(replay, cid, n):
            break
    return replay


def render_report(cid: str, actor: str, baseline: dict, replay: dict) -> str:
    """A compact baseline-vs-replay report for one chapter and actor (FR-522).

    ``baseline`` and ``replay`` are :func:`witness_metrics.chapter_actor_flag_metrics`
    dicts. Reports the director-flag count and the intent-map acting count for both
    runs side by side, so the confound (an injected scene change reaching the
    director it measures) is legible rather than hidden.
    """
    lines = [
        f"BASELINE  ch{cid}: {baseline['flag_turns']}/{baseline['total']} turns "
        f"flagged {actor} "
        f"(acting {baseline['acting_turns']}/{baseline['total']})",
        f"REPLAY    ch{cid}: {replay['flag_turns']}/{replay['total']} turns "
        f"flagged {actor} "
        f"(acting {replay['acting_turns']}/{replay['total']})",
    ]
    for t in replay["per_turn"]:
        mark = " ⚑" if t["flagged"] else "  "
        flag = t["flags"][0] if t["flags"] else ""
        lines.append(
            f"{mark} turn {t['n']:>2}: acting={'Y' if t['acting'] else 'n'} "
            f"flagged={'Y' if t['flagged'] else 'n'}  {flag}"
        )
    return "\n".join(lines)


def maybe_write_doc(doc: dict, out_path: str | None) -> bool:
    """Write the replayed ``doc`` to ``out_path`` when given; return whether it did.

    Empty/``None`` path → nothing written (the default; a replay need not be
    persisted to be read off the console). Returns ``True`` only when a file was
    written, so a caller/test can assert the plumbing without inspecting the disk.
    """
    if not out_path:
        return False
    Path(out_path).write_text(
        json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return True
