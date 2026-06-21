"""FR-561 M2 -- the causal trio hardened: phantom-reversal, capped reachability, threat.

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

Two lanes, mirroring the design split (design-v3-plot-model-implementation.md S3):

* **Pure lane (no engine).** ``validate_plan`` runs the hand-written narrative invariants. M2 adds
  ``_check_causal_antecedent`` -- every precondition must have a producer (an earlier-ordered
  effect) or be in ``I``; else ``open_condition``. These tests import only the plan package, never
  ``unified-planning``, so the pure path the M1 projection/grounding tests rely on stays engine-free.

* **Engine lane (``importorskip``).** ``solve_status`` proves capped reachability (check 5, a new
  unary-counter budget) and the forced-window threat (check 6, against the *current* encoding --
  J1, no ``build_problem`` change). ``unified-planning`` stays optional; only these tests gate on it.

J5 (corrected during enforcement): the pure antecedent check is *existence-based*. It flags only the
no-producer-ever class. ``early_reveal_variant`` is NOT flagged -- its precondition IS in ``I`` -- so
its unsolvability remains a temporal *engine* proof (``test_plot_causal`` owns it, unchanged).
"""

from __future__ import annotations

import pytest

from examples.dungeon_master.api.plot import floodmark as fm
from examples.dungeon_master.api.plot import validate as v

# --- pure lane: phantom-reversal -> open_condition -----------------------------------------


def test_phantom_return_yields_one_open_condition():
    """A return whose belief precondition has no producer (not in I) is flagged at its function."""
    result = v.validate_plan(fm.phantom_return_variant)
    open_flaws = [f for f in result.flaws if f.code == "open_condition"]
    assert (
        len(open_flaws) == 1
    ), f"expected exactly one open_condition; got {result.flaws}"
    assert open_flaws[0].function_id == "Fphantom"
    assert result.ok is False


def test_floodmark_has_no_open_condition():
    """Every floodmark precondition is grounded (in I or produced earlier) -> no flaw, pure."""
    result = v.validate_plan(fm.floodmark)
    assert [f for f in result.flaws if f.code == "open_condition"] == []
    assert result.ok is True


def test_early_reveal_is_not_an_open_condition():
    """J5 corrected: Fonstage's precondition IS in I, so it is structurally grounded.

    Its unsolvability is temporal (F1 flips the belief before Ch3) -- an engine proof, not a
    missing-antecedent flaw. The pure check must NOT flag it.
    """
    result = v.validate_plan(fm.early_reveal_variant)
    assert [f for f in result.flaws if f.code == "open_condition"] == []


# --- engine lane: capped reachability + forced-window threat -------------------------------


def _engine():
    """Import the UP status helpers + plan package, or skip if the engine is unavailable."""
    pytest.importorskip(
        "unified_planning",
        reason="unified-planning not installed (optional dependency)",
    )
    from unified_planning.engines.results import POSITIVE_OUTCOMES

    return POSITIVE_OUTCOMES


def _solve_or_skip(plan):
    try:
        return v.solve_status(plan)
    except v.NoEngineAvailable as e:
        pytest.skip(f"no suitable unified-planning engine available: {e}")


def test_overbudget_is_proven_unsolvable():
    """Sum of cost_turns (3) exceeds turn_budget=2 -> the unary-counter runs out -> unsolvable."""
    _engine()
    status = _solve_or_skip(fm.overbudget_variant)
    assert status not in v.GAVE_UP, f"must be a proof, not a give-up; got {status.name}"
    assert (
        status in v.PROVEN_UNSOLVABLE
    ), f"overbudget must be proven unsolvable; got {status.name}"


def test_budget_ok_still_solves():
    """The same plan under a sufficient turn_budget=3 still solves -- the counter does not over-constrain."""
    positive_outcomes = _engine()
    status = _solve_or_skip(fm.budget_ok_variant)
    assert (
        status in positive_outcomes
    ), f"within-budget plan must solve; got {status.name}"


def test_threat_is_proven_unsolvable():
    """Forced-window threat: B clears holds(Ledger) between producer A and consumer C -> unsolvable.

    Proven against the *current* encoding -- no build_problem change (J1).
    """
    _engine()
    status = _solve_or_skip(fm.threat_variant)
    assert status not in v.GAVE_UP, f"must be a proof, not a give-up; got {status.name}"
    assert (
        status in v.PROVEN_UNSOLVABLE
    ), f"forced-window threat must be proven unsolvable; got {status.name}"


def test_floodmark_unbudgeted_still_solves():
    """turn_budget=None leaves the canonical plan untouched -> still solvable after the M2 encoding."""
    positive_outcomes = _engine()
    status = _solve_or_skip(fm.floodmark)
    assert status in positive_outcomes, f"floodmark must still plan; got {status.name}"
