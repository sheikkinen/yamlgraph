"""FR-560 M1 re-homed M0 causal regression (graduated off the deleted FR-559 spike).

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

These are the FR-559 proven-negative assertions, re-homed onto ``api/plot/`` so the causal
regression survives the spike deletion (FR-560 J4d). ``unified-planning`` stays an **optional**
dependency: the imports are local to each test and skip gracefully when the engine is absent --
only this causal file is gated; projection/grounding/seam/report run pure.

J1 engine-reality: the installed Fast Downward build proves unsolvability ("Completely explored
state space -- no solution!") but reports it as ``UNSOLVABLE_INCOMPLETELY`` (exit 12), never
``UNSOLVABLE_PROVEN``. So ``PROVEN_UNSOLVABLE`` accepts both, while TIMEOUT/MEMOUT/INTERNAL_ERROR
still FAIL (distinct statuses, never produced by exhaustion of a finite space).
"""

from __future__ import annotations

import pytest


def _plot():
    """Import the graduated plot package + UP status helpers, or skip if unavailable."""
    pytest.importorskip(
        "unified_planning",
        reason="unified-planning not installed (optional dependency)",
    )
    from unified_planning.engines.results import POSITIVE_OUTCOMES

    from examples.dungeon_master.api.plot import floodmark as fm
    from examples.dungeon_master.api.plot import validate as v

    return POSITIVE_OUTCOMES, fm, v


def _solve_or_skip(v, plan):
    try:
        return v.solve_status(plan)
    except v.NoEngineAvailable as e:
        pytest.skip(f"no suitable unified-planning engine available: {e}")


def test_floodmark_presumed_dead_arc_is_solvable():
    """Belief-as-fluent lets a classical planner schedule the floodmark plan."""
    positive_outcomes, fm, v = _plot()
    status = _solve_or_skip(v, fm.floodmark)
    assert status in positive_outcomes, f"floodmark must plan; got {status.name}"


def test_early_reveal_is_proven_unsolvable():
    """Arnulf onstage at Ch3 needs a belief established only at Ch6 -> goal unreachable.

    Must be a *proof* (complete-search exhaustion), not a give-up: TIMEOUT/MEMOUT/INTERNAL_ERROR
    fail the test because they prove nothing about representability (J1).
    """
    _positive_outcomes, fm, v = _plot()
    status = _solve_or_skip(v, fm.early_reveal_variant)
    assert (
        status not in v.GAVE_UP
    ), f"negative must be a proof, not a give-up; got {status.name}"
    assert (
        status in v.PROVEN_UNSOLVABLE
    ), f"early reveal must be proven unsolvable; got {status.name}"


def test_world_revival_trips_monotonic_lifecycle():
    """Reviving Arnulf as world-truth (not belief) is the 'death that un-happens' bug.

    The planner cannot catch it -- belief and world are independent fluents by design -- so the
    hand-written lifecycle invariant owns it.
    """
    _positive_outcomes, fm, v = _plot()
    result = v.validate_plan(fm.world_revival_variant)
    codes = [flaw.code for flaw in result.flaws]
    assert "lifecycle_violation" in codes, f"expected lifecycle_violation; got {codes}"
    assert result.ok is False
