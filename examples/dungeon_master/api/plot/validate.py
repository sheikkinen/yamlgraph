"""Plan validation: the causal satisfiability check + the pure narrative invariants (FR-560 M1).

Two responsibilities, split by who can own them:

* ``solve_status`` -- the *causal* check, discharged by ``unified-planning`` (an **optional**
  dependency; its import is lazy so the pure checks below run without it). Returns a typed
  three-way outcome: a real proof, a give-up, or no-engine.
* ``validate_plan`` -- the *narrative* checks the planner cannot enforce, both **pure**:
  - **monotonic lifecycle:** once world-truth says a character is dead, no later beat may assert
    world-truth alive again (belief revival is fine) -- the floodmark keystone;
  - **ungrounded reveal (FR-560 M1):** a reveal that sets ``believes(obs, alive(c))=True`` must
    un-tell a secret an earlier-ordered beat (or the initial belief) actually told. M1 is
    ungrounded-reveal ONLY (the "unclosed belief gap" branch is M3-adjacent and was cut, FR-560 J2).

**Engine reality.** No pip-installable UP engine on the target machine emits ``UNSOLVABLE_PROVEN``:
Fast Downward proves unsolvability ("Completely explored state space -- no solution!") yet exits 12,
which the wrapper maps to ``UNSOLVABLE_INCOMPLETELY``. So for a **complete** search config
(``fast-downward`` ``astar(blind())``) on a **finite** problem, ``UNSOLVABLE_INCOMPLETELY`` *is* the
proof. ``PROVEN_UNSOLVABLE`` therefore accepts both proven enums; ``GAVE_UP`` (TIMEOUT/MEMOUT/
INTERNAL_ERROR) is a distinct set that must FAIL the test; missing engine raises ``NoEngineAvailable``.
"""

from __future__ import annotations

from .project import ordered_functions
from .schema import Function, PlanFlaw, PlotPlan, ValidationResult

# Complete search config: blind A* exhausts a finite state space, so no-plan == a proof.
ENGINE_NAME = "fast-downward"
ENGINE_PARAMS = {"fast_downward_search_config": "astar(blind())"}

# Status-set constants depend on ``unified-planning``; defined only when the optional dep is present
# (the causal regression imports it via ``pytest.importorskip`` before touching these names).
try:  # pragma: no cover - exercised only with the optional engine installed
    from unified_planning.engines import PlanGenerationResultStatus as _St

    # A complete-search exhaustion is a proof even when this FD build labels it INCOMPLETELY.
    PROVEN_UNSOLVABLE = (_St.UNSOLVABLE_PROVEN, _St.UNSOLVABLE_INCOMPLETELY)
    # Ran out of road or crashed -- proves nothing about representability; must FAIL the test.
    GAVE_UP = (_St.TIMEOUT, _St.MEMOUT, _St.INTERNAL_ERROR)
except ImportError:  # pragma: no cover - pure callers never touch the status constants
    PROVEN_UNSOLVABLE = ()
    GAVE_UP = ()


class NoEngineAvailable(Exception):
    """Raised when no installed engine supports the problem kind -- caller SKIPs."""


def solve_status(plan: PlotPlan):
    """Compile ``plan`` and return the planner's typed outcome status.

    Positive: ``status in unified_planning.engines.results.POSITIVE_OUTCOMES``.
    Proven negative: ``status in PROVEN_UNSOLVABLE`` (complete search on a finite problem).
    ``GAVE_UP`` statuses are returned as-is so the caller can FAIL; missing engine raises
    ``NoEngineAvailable`` so the caller can SKIP. ``unified-planning`` is imported lazily here so
    the pure narrative checks run without the optional dependency.
    """
    import unified_planning as up
    from unified_planning.shortcuts import OneshotPlanner, get_environment

    from .up_model import build_problem

    get_environment().credits_stream = None  # suppress engine credit banners
    problem = build_problem(plan)
    try:
        with OneshotPlanner(name=ENGINE_NAME, params=ENGINE_PARAMS) as planner:
            return planner.solve(problem).status
    except up.exceptions.UPNoSuitableEngineAvailableError as e:
        raise NoEngineAvailable(str(e)) from e


def _check_monotonic_lifecycle(plan: PlotPlan, order: list[Function]) -> list[PlanFlaw]:
    """Once world-truth says not-alive(c), no later beat may assert world-truth alive(c).

    A beat MAY assert ``believes(obs, alive(c))`` -- that is the presumed-dead case. The planner
    will not enforce this because belief and world are independent fluents by design.
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


def _check_belief_grounding(plan: PlotPlan, order: list[Function]) -> list[PlanFlaw]:
    """A reveal must un-tell a secret an earlier beat told (FR-560 M1, ungrounded-reveal only).

    A function whose ``eff_belief`` flips ``believes(obs, alive(c))`` to True is ``ungrounded_reveal``
    unless that observer's belief was ``False`` at that point -- opened by an earlier-ordered beat or
    set False in ``initial_belief``. The planner cannot catch this: belief and world are independent
    fluents, so it happily flips a belief that was never opened.
    """
    flaws: list[PlanFlaw] = []
    held: dict[tuple[str, str], bool] = {}
    for b in plan.initial_belief:
        if b.fluent.pred == "alive" and b.fluent.args:
            held[(b.observer, b.fluent.args[0])] = b.held
    for fn in order:
        for b in fn.eff_belief:
            if b.fluent.pred != "alive" or not b.fluent.args:
                continue
            key = (b.observer, b.fluent.args[0])
            if b.held is True and held.get(key) is not False:
                flaws.append(
                    PlanFlaw(
                        code="ungrounded_reveal",
                        function_id=fn.id,
                        detail=(
                            f"{fn.id} reveals believes({b.observer}, alive({b.fluent.args[0]})) "
                            f"that no earlier beat ever set False -- nothing to un-tell."
                        ),
                    )
                )
            held[key] = b.held
    return flaws


def validate_plan(plan: PlotPlan) -> ValidationResult:
    """Run the pure narrative invariants (monotonic lifecycle + ungrounded reveal) over ``plan``."""
    order = ordered_functions(plan)
    flaws = _check_monotonic_lifecycle(plan, order) + _check_belief_grounding(
        plan, order
    )
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
