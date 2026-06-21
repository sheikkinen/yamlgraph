"""FR-562 M3 -- affect closure: the dropped-confrontation narrative invariant.

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

Check 4 (design-v3-plot-model-implementation.md S5) is the fourth and final hand-written narrative
pass: every opened affect unit (``AffectDelta(op="open", char, kind)``) must have a later ``close``
of the same ``(char, kind)``, unless the author lists that unit in ``PlotPlan.intentional_open``. A
residual open is an ``unclosed_affect`` flaw localized to the opening beat. Pure -- no
``unified-planning``; affect debt is narrative bookkeeping, not a precondition.

J3: the check is an *ordered* pop-walk, not a symmetric count -- a close-then-reopen of the same unit
is residual debt on the reopening beat (a ``Counter`` net-zero would wrongly pass it).
"""

from __future__ import annotations

from examples.dungeon_master.api.plot import floodmark as fm
from examples.dungeon_master.api.plot import validate as v


def test_canonical_floodmark_closes_cleanly():
    """floodmark opens loss+guilt and closes both -> no unclosed_affect, plan ok."""
    result = v.validate_plan(fm.floodmark)
    assert [f for f in result.flaws if f.code == "unclosed_affect"] == []
    assert result.ok is True


def test_dropped_confrontation_flagged():
    """Deleting the reconciliation close leaves guilt(Hilde) open at the reveal beat (Fr)."""
    result = v.validate_plan(fm.dropped_confrontation_variant)
    affect = [f for f in result.flaws if f.code == "unclosed_affect"]
    assert len(affect) == 1, f"expected exactly one unclosed_affect; got {result.flaws}"
    assert affect[0].function_id == "Fr"
    assert "guilt" in affect[0].detail and "Hilde" in affect[0].detail
    assert result.ok is False


def test_intentional_open_suppresses():
    """Listing (Hilde, guilt) in intentional_open exempts the dropped unit -> plan ok."""
    variant = fm.dropped_confrontation_variant.model_copy(deep=True)
    variant.intentional_open = [(fm.HILDE, "guilt")]
    result = v.validate_plan(variant)
    assert [f for f in result.flaws if f.code == "unclosed_affect"] == []
    assert result.ok is True


def test_unmatched_close_is_harmless():
    """A close with no prior open is narrative slack, not a defect (debt check, not symmetry)."""
    from examples.dungeon_master.api.plot.schema import (
        AffectDelta,
        Function,
        PlotPlan,
    )

    plan = PlotPlan(
        agents=[fm.HILDE],
        functions=[
            Function(
                id="LoneClose",
                kind="reconciliation",
                subject=fm.HILDE,
                chapter=1,
                eff_affect=[AffectDelta(op="close", char=fm.HILDE, kind="loss")],
            ),
        ],
    )
    result = v.validate_plan(plan)
    assert [f for f in result.flaws if f.code == "unclosed_affect"] == []
    assert result.ok is True


def test_close_then_reopen_is_debt_not_net_zero():
    """J3: an early close + later open of the same unit is debt on the reopening beat, not net-zero."""
    result = v.validate_plan(fm.reopened_affect_variant)
    affect = [f for f in result.flaws if f.code == "unclosed_affect"]
    assert len(affect) == 1, f"expected one unclosed_affect; got {result.flaws}"
    assert affect[0].function_id == "Yopen"
    assert "loss" in affect[0].detail


def test_report_renders_affect_ledger():
    """The report shows an affect column: zero debt for floodmark, the open guilt as debt for the drop."""
    from examples.dungeon_master.api.plot import report

    clean = report.render_report(fm.floodmark)
    assert "affect" in clean.lower()

    dropped = report.render_report(fm.dropped_confrontation_variant)
    assert "guilt" in dropped.lower()
