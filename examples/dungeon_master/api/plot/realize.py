"""Beat-driven turn instruction: ``PlotPlan`` -> prose directive (FR-564 M4b).

Pure, leaf (no turn-engine import -- ``api.plot`` is imported *by* the turn path, never the
reverse). Produces a **string** -- the one field the engine already exposes for caller intent
(``TurnRequest.instruction``).

``beat_instruction(plan, chapter) -> str`` renders the authored beat(s) scheduled at ``chapter``
in ``ordered_functions`` order. A chapter may carry MORE than one beat (floodmark ch6 has both
``Fr`` reveal and ``Ff`` reconciliation); directives are concatenated in order. Returns ``''``
when no beat maps to ``chapter`` -- so an un-planned chapter is byte-for-byte unchanged.

Belief is focalized: the instruction states what THIS beat's observers BELIEVE, never world-truth
the realizer cannot author (FR-564 J5a, via ``belief_at`` from ``project.py``).
"""

from __future__ import annotations

from .project import belief_at, ordered_functions
from .schema import Function, PlotPlan


def beat_instruction(plan: PlotPlan, chapter: int) -> str:
    """Render authored beat(s) at ``chapter`` as a turn instruction.

    Selects the ``Function``(s) whose ``chapter`` matches, in ``ordered_functions`` order.
    Returns ``''`` when no beat maps to ``chapter``.
    """
    fns = [fn for fn in ordered_functions(plan) if fn.chapter == chapter]
    if not fns:
        return ""
    beliefs = belief_at(plan, chapter)
    parts = [_render_beat(fn, beliefs) for fn in fns]
    return "\n\n".join(parts)


def _render_beat(fn: Function, beliefs: dict[tuple[str, str], bool]) -> str:
    """Render one ``Function`` as a prose directive, focalized on belief."""
    lines: list[str] = []
    lines.append(f"[{fn.id}] {fn.kind} — subject: {fn.subject}")

    # Effects: belief changes (focalized, not world-truth)
    for b in fn.eff_belief:
        if b.fluent.pred == "alive" and b.fluent.args:
            char = b.fluent.args[0]
            if b.held:
                lines.append(
                    f"  belief: {b.observer} now believes {char} is alive (reveal)"
                )
            else:
                lines.append(
                    f"  belief: {b.observer} now believes {char} is presumed dead"
                )

    # Effects: affect deltas
    for ad in fn.eff_affect:
        lines.append(f"  affect: {ad.op} {ad.kind}({ad.char})")

    # Observer focalization: what observers believe at this chapter
    if fn.observers:
        for obs in fn.observers:
            obs_beliefs = {
                char: held for (o, char), held in beliefs.items() if o == obs
            }
            if obs_beliefs:
                belief_strs = [
                    f"{char} {'alive' if held else 'presumed dead'}"
                    for char, held in obs_beliefs.items()
                ]
                lines.append(f"  {obs} believes: {', '.join(belief_strs)}")

    return "\n".join(lines)


def merge_beat_instruction(stage_instruction: str, beat: str) -> str:
    """Merge the beat directive into the stage instruction (additive, never replacing).

    When ``beat`` is empty the stage instruction passes through byte-for-byte (the FR-560/563
    dormancy invariant). When non-empty the beat intent is appended, separated by a blank line.
    """
    if not beat:
        return stage_instruction
    if not stage_instruction:
        return beat
    return f"{stage_instruction}\n\n{beat}"


__all__ = ["beat_instruction", "merge_beat_instruction"]
