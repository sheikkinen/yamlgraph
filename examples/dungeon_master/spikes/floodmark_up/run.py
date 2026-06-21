"""Run the floodmark spike: solve the plan and print the chapter order -- FR-559 spike ONLY.

This is the 'tell the floodmark story' skeleton: the realizer's input is the solver-ordered
sequence of authored beats. Run with::

    PYTHONPATH="$PWD" python -m examples.dungeon_master.spikes.floodmark_up.run

Requires the optional ``unified-planning[fast-downward]`` install (see README).
"""

from __future__ import annotations

from unified_planning.engines.results import POSITIVE_OUTCOMES
from unified_planning.shortcuts import OneshotPlanner, get_environment

from .floodmark import floodmark
from .up_model import build_problem
from .validate import ENGINE_NAME, ENGINE_PARAMS


def main() -> int:
    get_environment().credits_stream = None
    problem = build_problem(floodmark)
    with OneshotPlanner(name=ENGINE_NAME, params=ENGINE_PARAMS) as planner:
        result = planner.solve(problem)

    print(f"status: {result.status.name}")
    if result.status not in POSITIVE_OUTCOMES or result.plan is None:
        print("no plan -- floodmark should be solvable; check the engine install")
        return 1

    beats = [
        str(action.action.name).removeprefix("do_")
        for action in result.plan.actions
        if str(action.action.name).startswith("do_")
    ]
    by_id = {fn.id.lower(): fn for fn in floodmark.functions}
    print("solved chapter order (the realizer's input skeleton):")
    for beat in beats:
        fn = by_id.get(beat)
        if fn is not None:
            print(f"  ch{fn.chapter:>2}  {fn.id:<10} {fn.kind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
