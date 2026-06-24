"""FR-571 — Affect closure: every opened affect must close (policy-aware)."""

from __future__ import annotations

from schema import Function, PlotPlan


def check_affect_closure(plan: PlotPlan, order: list[Function]) -> list[str]:
    """Ordered pop-walk over affect open/close operations.

    If ``affect_policy.unclosed_is_error`` is False, unclosed threads are
    permitted (horror / tragic endings). Returns flaws only when the policy
    requires closure.
    """
    if not plan.affect_policy.unclosed_is_error:
        return []

    open_units: dict[tuple[str, str], str] = {}
    for fn in order:
        for delta in fn.eff_affect:
            key = (delta.char, delta.kind.value)
            if delta.op == "open":
                open_units[key] = fn.id
            else:
                open_units.pop(key, None)

    return [
        f"{opener}: unclosed affect {kind}({char})"
        for (char, kind), opener in open_units.items()
    ]
