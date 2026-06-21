"""Pure projections over an authored ``PlotPlan`` -- the belief lane's derived sets (FR-560 M1).

Design-section-5 signatures. These are a **pure** function of the plan's belief timeline; they do
NOT import ``unified-planning`` and never touch a planner. ``exclusion_set`` is the load-bearing one
-- the floodmark guard that keeps a presumed-dead character offstage until the reveal.
"""

from __future__ import annotations

from .schema import Function, PlotPlan


def ordered_functions(plan: PlotPlan) -> list[Function]:
    """Order beats by chapter, refined by the explicit ``order`` (E) edges.

    Cheap topological sort; raises ``ValueError`` on a cycle. Shared with the validator so the
    causal and projection lanes agree on a single beat order.
    """
    by_id = {fn.id: fn for fn in plan.functions}
    after: dict[str, set[str]] = {fn.id: set() for fn in plan.functions}
    for before, aft in plan.order:
        if before in by_id and aft in by_id:
            after[aft].add(before)

    ordered: list[Function] = []
    placed: set[str] = set()
    remaining = list(plan.functions)
    while remaining:
        ready = [fn for fn in remaining if after[fn.id] <= placed]
        if not ready:
            raise ValueError("cycle in plan order (E)")
        ready.sort(key=lambda fn: fn.chapter)
        nxt = ready[0]
        ordered.append(nxt)
        placed.add(nxt.id)
        remaining.remove(nxt)
    return ordered


def chapter_cast(plan: PlotPlan, chapter: int) -> list[str]:
    """Subjects + targets + observers of the functions scheduled at ``chapter`` (ordered, de-duped)."""
    cast: list[str] = []

    def _add(name: str | None) -> None:
        if name and name not in cast:
            cast.append(name)

    for fn in ordered_functions(plan):
        if fn.chapter != chapter:
            continue
        _add(fn.subject)
        _add(fn.target)
        for obs in fn.observers:
            _add(obs)
    return cast


def exclusion_set(plan: PlotPlan, chapter: int) -> set[str]:
    """Characters the prose must NOT place onstage at ``chapter`` (non-circular M1 rule, FR-560 J3).

    ``X in exclusion_set(plan, c)`` iff the latest belief beat about ``alive(X)`` at chapter <= c
    sets ``held=False`` for some observer and no reveal restores ``held=True`` at chapter <= c.
    Derived from the belief timeline (``initial_belief`` then ``ordered_functions`` whose chapter
    <= c), never from the cast -- the v2 "every onstage observer" phrasing was circular. Multi-
    observer quantifiers are out of M1: a single presumed-dead observer suffices to exclude.
    """
    latest: dict[tuple[str, str], bool] = {}
    for b in plan.initial_belief:
        if b.fluent.pred == "alive" and b.fluent.args:
            latest[(b.observer, b.fluent.args[0])] = b.held
    for fn in ordered_functions(plan):
        if fn.chapter > chapter:
            continue
        for b in fn.eff_belief:
            if b.fluent.pred == "alive" and b.fluent.args:
                latest[(b.observer, b.fluent.args[0])] = b.held
    return {char for (_obs, char), held in latest.items() if held is False}


def protected_set(plan: PlotPlan) -> list[str]:
    """The author invariants G -- the goal fluents' subject characters (ordered, de-duped)."""
    protected: list[str] = []
    for gf in plan.goals:
        if gf.args:
            name = gf.args[0]
            if name not in protected:
                protected.append(name)
    return protected


__all__ = ["chapter_cast", "exclusion_set", "ordered_functions", "protected_set"]
