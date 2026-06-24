"""FR-571 — Monotonic lifecycle: alive → dead is one-way in world-truth."""

from __future__ import annotations

from schema import Function, PlotPlan


def check_lifecycle(plan: PlotPlan, order: list[Function]) -> list[str]:
    """Once world-truth says not-alive(c), no later beat may assert alive(c).

    Belief revival (believes alive) is fine — that is the presumed-dead case.
    """
    flaws: list[str] = []
    dead: set[str] = {
        f.args[0] for f in plan.initial_world if f.pred == "alive" and f.value is False
    }
    for fn in order:
        for eff in fn.eff_world:
            if eff.pred != "alive":
                continue
            char = eff.args[0]
            if eff.value is False:
                dead.add(char)
            elif eff.value is True and char in dead:
                flaws.append(f"{fn.id}: asserts alive({char}) after {char} died")
    return flaws
