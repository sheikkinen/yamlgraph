"""FR-571 — Schema tests: fixture parse, enum counts, coercion boundaries."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from schema import (
    AffectDelta,
    AffectKind,
    Belief,
    Fluent,
    FunctionKind,
    PlotPlan,
)

FIXTURES = sorted(
    (Path(__file__).resolve().parent.parent / "fixtures" / "ground-truth").glob(
        "*.yaml"
    )
)


# --- AC#1: fixture parse with extra="forbid" ---


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: p.stem)
def test_fixture_parses_into_plot_plan(fixture: Path) -> None:
    """Every ground-truth fixture must parse without error (extra=forbid)."""
    data = yaml.safe_load(fixture.read_text(encoding="utf-8"))
    plan = PlotPlan.model_validate(data)
    assert len(plan.functions) > 0


def test_extra_forbid_rejects_unknown_field() -> None:
    """extra='forbid' must reject unmodeled fields (J:C2)."""
    with pytest.raises(ValidationError):
        PlotPlan.model_validate({"meta": {"title": "x", "bogus": "y"}})


def test_extra_forbid_rejects_unknown_function_field() -> None:
    with pytest.raises(ValidationError):
        PlotPlan.model_validate(
            {
                "functions": [
                    {"id": "F1", "kind": "villainy", "chapter": 1, "grain": "chapter"}
                ]
            }
        )


# --- AC#2: FunctionKind has exactly 17 members ---


def test_function_kind_count() -> None:
    assert len(FunctionKind) == 17


def test_function_kind_return_value() -> None:
    """The ``return_`` Python name maps to ``"return"`` YAML value."""
    assert FunctionKind.return_.value == "return"


# --- AC#3: AffectKind has exactly 6 members ---


def test_affect_kind_count() -> None:
    assert len(AffectKind) == 6


# --- AC#4: AffectDelta.toward is optional ---


def test_toward_defaults_to_none() -> None:
    delta = AffectDelta(op="open", char="A", kind="loss")
    assert delta.toward is None


def test_toward_accepts_string() -> None:
    delta = AffectDelta(op="open", char="A", kind="guilt", toward="B")
    assert delta.toward == "B"


# --- AC#5: Belief.held accepts bool and str, string "true" stays str ---


def test_held_accepts_true() -> None:
    b = Belief(observer="A", fluent=Fluent(pred="alive", args=["A"]), held=True)
    assert b.held is True
    assert isinstance(b.held, bool)


def test_held_accepts_false() -> None:
    b = Belief(observer="A", fluent=Fluent(pred="alive", args=["A"]), held=False)
    assert b.held is False
    assert isinstance(b.held, bool)


def test_held_accepts_str_software() -> None:
    b = Belief(observer="A", fluent=Fluent(pred="alive", args=["A"]), held="software")
    assert b.held == "software"
    assert isinstance(b.held, str)


def test_held_accepts_str_worthy() -> None:
    b = Belief(observer="A", fluent=Fluent(pred="alive", args=["A"]), held="worthy")
    assert b.held == "worthy"
    assert isinstance(b.held, str)


def test_held_string_true_stays_str() -> None:
    """The string ``"true"`` must NOT coerce to ``bool True`` (J:Note)."""
    b = Belief(observer="A", fluent=Fluent(pred="alive", args=["A"]), held="true")
    assert b.held == "true"
    assert isinstance(b.held, str)


def test_held_string_false_stays_str() -> None:
    b = Belief(observer="A", fluent=Fluent(pred="alive", args=["A"]), held="false")
    assert b.held == "false"
    assert isinstance(b.held, str)
