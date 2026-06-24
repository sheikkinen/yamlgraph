"""FR-571 — Plot Modeller validators (lifecycle, grounding, affect closure)."""

from __future__ import annotations

from schema import Function, PlotPlan

from .affects import check_affect_closure
from .grounding import check_grounding
from .lifecycle import check_lifecycle


def ordered_functions(plan: PlotPlan) -> list[Function]:
    """Order beats by chapter, then by position within the functions list.

    The Plot Modeller plans are linearly ordered (no partial-order edges yet).
    """
    return sorted(plan.functions, key=lambda fn: (fn.chapter, plan.functions.index(fn)))


def validate_plan(plan: PlotPlan) -> list[str]:
    """Run all narrative validators. Returns a list of flaw strings (empty = valid)."""
    order = ordered_functions(plan)
    return (
        check_lifecycle(plan, order)
        + check_grounding(plan, order)
        + check_affect_closure(plan, order)
    )


__all__ = [
    "check_affect_closure",
    "check_grounding",
    "check_lifecycle",
    "ordered_functions",
    "validate_plan",
]
