"""FR-559 M0 floodmark plot-model spike: the proven-negative characterization test.

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

This test is the deliverable's proof, not decoration. It asserts three things about an
off-the-shelf classical planner authoring the typed floodmark ``PlotPlan``:

  1. the presumed-dead arc is **solvable** (belief-as-fluent carries "world alive, clan believes
     dead" without any epistemic planner);
  2. the early-reveal variant (Arnulf onstage at Ch3) is **proven unsolvable** by a complete
     search -- not merely a timeout (J1); and
  3. the world-revival variant trips the hand-written monotonic-lifecycle invariant the planner
     cannot enforce (J2/keystone).

J1 engine-reality: the installed Fast Downward build proves unsolvability ("Completely explored
state space -- no solution!") but reports it as ``UNSOLVABLE_INCOMPLETELY`` (exit 12), never
``UNSOLVABLE_PROVEN``. So ``PROVEN_UNSOLVABLE`` accepts both, while ``TIMEOUT``/``MEMOUT``/
``INTERNAL_ERROR`` still FAIL (distinct statuses, never produced by exhaustion of a finite space).

Imports are local to each test so the module imports cleanly and skips gracefully when
``unified-planning`` or a suitable engine is unavailable -- it never breaks the default
``pytest tests/unit/`` run or the CI dependency audit.
"""

from __future__ import annotations

import pytest


def _spike():
    """Import the spike package + UP status helpers, or skip if unavailable."""
    pytest.importorskip(
        "unified_planning",
        reason="unified-planning not installed (optional spike dependency)",
    )
    from unified_planning.engines.results import POSITIVE_OUTCOMES

    from examples.dungeon_master.spikes.floodmark_up import floodmark as fm
    from examples.dungeon_master.spikes.floodmark_up import validate as v

    return POSITIVE_OUTCOMES, fm, v


def _solve_or_skip(v, plan):
    try:
        return v.solve_status(plan)
    except v.NoEngineAvailable as e:
        pytest.skip(f"no suitable unified-planning engine available: {e}")


def test_floodmark_presumed_dead_arc_is_solvable():
    """Belief-as-fluent lets a classical planner schedule the floodmark plan."""
    positive_outcomes, fm, v = _spike()
    status = _solve_or_skip(v, fm.floodmark)
    assert status in positive_outcomes, f"floodmark must plan; got {status.name}"


def test_early_reveal_is_proven_unsolvable():
    """Arnulf onstage at Ch3 needs a belief established only at Ch6 -> goal unreachable.

    Must be a *proof* (complete-search exhaustion), not a give-up: TIMEOUT/MEMOUT/INTERNAL_ERROR
    fail the test because they prove nothing about representability (J1).
    """
    _positive_outcomes, fm, v = _spike()
    status = _solve_or_skip(v, fm.early_reveal_variant)
    assert (
        status not in v.GAVE_UP
    ), f"early-reveal negative must be a proof, not a give-up; got {status.name}"
    assert (
        status in v.PROVEN_UNSOLVABLE
    ), f"early reveal must be proven unsolvable; got {status.name}"


def test_world_revival_trips_monotonic_lifecycle():
    """Reviving Arnulf as world-truth (not belief) is the 'death that un-happens' bug.

    The planner cannot catch it -- belief and world are independent fluents by design -- so the
    hand-written lifecycle invariant owns it.
    """
    _positive_outcomes, fm, v = _spike()
    result = v.validate_plan(fm.world_revival_variant)
    codes = [flaw.code for flaw in result.flaws]
    assert "lifecycle_violation" in codes, f"expected lifecycle_violation; got {codes}"
    assert result.ok is False
