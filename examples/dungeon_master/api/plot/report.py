"""Human-inspectable projection report -- the M1 analogue of the M0 chapter-order print (FR-560).

Renders the pure projections (``protected_set`` / ``chapter_cast`` / ``exclusion_set``) and the
grounding verdict as a table, so the belief lane answers plain-language questions without a planner.
Lives under ``api/plot/`` (not ``examples/demos/``), so the demo-gate does not apply (FR-560 J4e);
a fixture-asserted snapshot test pins the table instead. Pure -- no ``unified-planning``.

    $ python -m examples.dungeon_master.api.plot.report floodmark
"""

from __future__ import annotations

import sys

from . import floodmark as _fixtures
from . import project
from .schema import PlotPlan
from .validate import validate_plan

_CAST_WIDTH = 22


def render_report(plan: PlotPlan) -> str:
    """Render the protected set, per-chapter cast/exclusion table, and grounding verdict."""
    protected = project.protected_set(plan)
    chapters = sorted({fn.chapter for fn in plan.functions}) or [1]
    last = chapters[-1]

    lines = [f"PROTECTED (author invariants G): {', '.join(protected) or '(none)'}", ""]
    header = (
        f"  ch | {'cast':<{_CAST_WIDTH}} | must-NOT-appear (presumed dead, pre-reveal)"
    )
    lines.append(header)
    lines.append(
        f"  ---+-{'-' * _CAST_WIDTH}-+--------------------------------------------"
    )
    for ch in range(1, last + 1):
        cast = ", ".join(project.chapter_cast(plan, ch)) or "(none)"
        excluded = ", ".join(sorted(project.exclusion_set(plan, ch))) or "(none)"
        lines.append(f"  {ch:>2} | {cast:<{_CAST_WIDTH}} | {excluded}")

    flaws = [f for f in validate_plan(plan).flaws if f.code == "ungrounded_reveal"]
    if flaws:
        verdict = "; ".join(f"{f.function_id}: {f.detail}" for f in flaws)
        lines.append(f"belief-grounding: FLAW -- {verdict}")
    else:
        lines.append(
            "belief-grounding: OK (every reveal un-tells a secret an earlier beat told)"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    name = argv[0] if argv else "floodmark"
    plan = getattr(_fixtures, name, None)
    if not isinstance(plan, PlotPlan):
        print(
            f"unknown plan {name!r}; available: floodmark, early_reveal_variant, "
            f"world_revival_variant, ungrounded_reveal_variant"
        )
        return 2
    print(render_report(plan))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
