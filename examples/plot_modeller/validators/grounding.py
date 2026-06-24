"""FR-571 — Belief grounding: can't reveal what no one was wrong about."""

from __future__ import annotations

from schema import Function, PlotPlan


def check_grounding(plan: PlotPlan, order: list[Function]) -> list[str]:
    """A reveal (eff_belief sets held=True for alive) is ungrounded unless
    that observer had a prior non-True belief about the same fluent.

    With ``held: bool | str``, valid precursors include ``False``,
    ``"unknown"``, ``"uncertain"`` — anything that is not ``True``.
    An absent prior (no belief at all) is ungrounded.
    """
    flaws: list[str] = []
    held: dict[tuple[str, str], bool | str | None] = {}
    for b in plan.initial_belief:
        if b.fluent.pred == "alive" and b.fluent.args:
            held[(b.observer, b.fluent.args[0])] = b.held
    for fn in order:
        for b in fn.eff_belief:
            if b.fluent.pred != "alive" or not b.fluent.args:
                continue
            key = (b.observer, b.fluent.args[0])
            prior = held.get(key)
            if b.held is True and (prior is None or prior is True):
                flaws.append(
                    f"{fn.id}: reveals alive({b.fluent.args[0]}) for "
                    f"{b.observer} without prior non-True belief"
                )
            held[key] = b.held
    return flaws
