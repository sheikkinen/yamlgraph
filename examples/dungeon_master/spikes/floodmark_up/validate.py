"""Plan satisfiability + the hand-written monotonic-lifecycle invariant -- FR-559 spike ONLY.

Two responsibilities, split by who can own them:

* ``solve_status`` -- the *causal* check, discharged by ``unified-planning``. Returns a typed
  three-way outcome (J1): a real proof, a give-up, or no-engine.
* ``validate_plan`` -- the *narrative* check the planner cannot enforce: once world-truth says a
  character is dead, no later beat may assert world-truth alive again (belief revival is fine).
  This is the floodmark keystone.

**J1 engine reality.** No pip-installable UP engine on the target machine emits
``UNSOLVABLE_PROVEN``: Fast Downward proves unsolvability ("Completely explored state space -- no
solution!") yet exits 12, which the wrapper maps to ``UNSOLVABLE_INCOMPLETELY``; symk behaves the
same; aries hangs on untimed classical problems. So for a **complete** search config
(``fast-downward`` ``astar(blind())``) on a **finite** problem, ``UNSOLVABLE_INCOMPLETELY`` *is*
the proof. ``PROVEN_UNSOLVABLE`` therefore accepts both proven enums; ``GAVE_UP``
(TIMEOUT/MEMOUT/INTERNAL_ERROR) is a distinct set that must FAIL the test, and no-engine SKIPs.
This preserves the Judge's proof-vs-give-up distinction; it only corrects the enum the engines
actually use. (See FR-559 J1 engine-reality amendment.)
"""

from __future__ import annotations

import unified_planning as up
from unified_planning.engines import PlanGenerationResultStatus as St
from unified_planning.shortcuts import OneshotPlanner, get_environment

from .schema import Function, PlanFlaw, PlotPlan, ValidationResult
from .up_model import build_problem

# Complete search config: blind A* exhausts a finite state space, so no-plan == a proof.
ENGINE_NAME = "fast-downward"
ENGINE_PARAMS = {"fast_downward_search_config": "astar(blind())"}

# A complete-search exhaustion is a proof even when this FD build labels it INCOMPLETELY.
PROVEN_UNSOLVABLE = (St.UNSOLVABLE_PROVEN, St.UNSOLVABLE_INCOMPLETELY)
# Ran out of road or crashed -- proves nothing about representability; must FAIL the test.
GAVE_UP = (St.TIMEOUT, St.MEMOUT, St.INTERNAL_ERROR)


class NoEngineAvailable(Exception):
    """Raised when no installed engine supports the problem kind -- caller SKIPs."""


def solve_status(plan: PlotPlan) -> St:
    """Compile ``plan`` and return the planner's typed outcome status (J1).

    Positive: ``status in POSITIVE_OUTCOMES``.
    Proven negative: ``status in PROVEN_UNSOLVABLE`` (complete search on a finite problem).
    ``GAVE_UP`` statuses are returned as-is so the caller can FAIL; missing engine raises
    ``NoEngineAvailable`` so the caller can SKIP.
    """
    get_environment().credits_stream = None  # suppress engine credit banners
    problem = build_problem(plan)
    try:
        with OneshotPlanner(name=ENGINE_NAME, params=ENGINE_PARAMS) as planner:
            return planner.solve(problem).status
    except up.exceptions.UPNoSuitableEngineAvailableError as e:
        raise NoEngineAvailable(str(e)) from e


def _ordered(plan: PlotPlan) -> list[Function]:
    """Order beats by chapter, refined by E edges. Cheap topo sort; raises on cycle."""
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


def _check_monotonic_lifecycle(plan: PlotPlan, order: list[Function]) -> list[PlanFlaw]:
    """Once world-truth says not-alive(c), no later beat may assert world-truth alive(c).

    A beat MAY assert ``believes(obs, alive(c))`` -- that is the presumed-dead case. The planner
    will not enforce this because belief and world are independent fluents by design; that
    independence is the whole point of belief-as-fluent.
    """
    flaws: list[PlanFlaw] = []
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
                flaws.append(
                    PlanFlaw(
                        code="lifecycle_violation",
                        function_id=fn.id,
                        detail=(
                            f"{fn.id} asserts world-truth alive({char}) after {char} died. "
                            f"Encode revival as belief: believes(observers, alive({char}))."
                        ),
                    )
                )
    return flaws


def validate_plan(plan: PlotPlan) -> ValidationResult:
    """Run the M0 narrative invariant (monotonic lifecycle) over ``plan``.

    M0 scope: lifecycle only. Belief-grounding and affect-closure are production M1+ checks,
    intentionally absent from the spike.
    """
    flaws = _check_monotonic_lifecycle(plan, _ordered(plan))
    return ValidationResult(ok=not flaws, flaws=flaws)


__all__ = [
    "ENGINE_NAME",
    "ENGINE_PARAMS",
    "GAVE_UP",
    "PROVEN_UNSOLVABLE",
    "NoEngineAvailable",
    "solve_status",
    "validate_plan",
]
