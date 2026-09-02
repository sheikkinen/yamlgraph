"""FR-571 — Validator tests: lifecycle, grounding, affect closure (AC#6)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from schema import PlotPlan
from validators import validate_plan

FIXTURES = sorted(
    (Path(__file__).resolve().parent.parent / "fixtures" / "ground-truth").glob(
        "*.yaml"
    )
)


# --- All ground-truth fixtures validate cleanly ---


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: p.stem)
def test_ground_truth_validates(fixture: Path) -> None:
    plan = PlotPlan.model_validate(yaml.safe_load(fixture.read_text(encoding="utf-8")))
    flaws = validate_plan(plan)
    assert flaws == [], f"unexpected flaws: {flaws}"


# --- Lifecycle violation ---


def test_lifecycle_violation_caught() -> None:
    """Dead character resurrected in world-truth is a flaw."""
    plan = PlotPlan.model_validate(
        {
            "functions": [
                {
                    "id": "F1",
                    "kind": "death",
                    "chapter": 1,
                    "eff_world": [{"pred": "alive", "args": ["Alice"], "value": False}],
                },
                {
                    "id": "F2",
                    "kind": "rescue",
                    "chapter": 2,
                    "eff_world": [{"pred": "alive", "args": ["Alice"], "value": True}],
                },
            ]
        }
    )
    flaws = validate_plan(plan)
    assert len(flaws) == 1
    assert "alive(Alice)" in flaws[0]
    assert "F2" in flaws[0]


# --- Ungrounded reveal ---


def test_ungrounded_reveal_caught() -> None:
    """Reveal alive without prior non-True belief is a flaw."""
    plan = PlotPlan.model_validate(
        {
            "functions": [
                {
                    "id": "F1",
                    "kind": "recognition",
                    "chapter": 1,
                    "eff_belief": [
                        {
                            "observer": "Bob",
                            "fluent": {"pred": "alive", "args": ["Carol"]},
                            "held": True,
                        }
                    ],
                }
            ]
        }
    )
    flaws = validate_plan(plan)
    assert len(flaws) == 1
    assert "F1" in flaws[0]
    assert "Carol" in flaws[0]


def test_grounded_reveal_passes() -> None:
    """Reveal after prior False belief is not a flaw."""
    plan = PlotPlan.model_validate(
        {
            "initial_belief": [
                {
                    "observer": "Bob",
                    "fluent": {"pred": "alive", "args": ["Carol"]},
                    "held": False,
                }
            ],
            "functions": [
                {
                    "id": "F1",
                    "kind": "recognition",
                    "chapter": 1,
                    "eff_belief": [
                        {
                            "observer": "Bob",
                            "fluent": {"pred": "alive", "args": ["Carol"]},
                            "held": True,
                        }
                    ],
                }
            ],
        }
    )
    assert validate_plan(plan) == []


def test_grounded_reveal_from_unknown() -> None:
    """Reveal after prior 'unknown' string belief is not a flaw (held: str)."""
    plan = PlotPlan.model_validate(
        {
            "initial_belief": [
                {
                    "observer": "Bob",
                    "fluent": {"pred": "alive", "args": ["Carol"]},
                    "held": "unknown",
                }
            ],
            "functions": [
                {
                    "id": "F1",
                    "kind": "recognition",
                    "chapter": 1,
                    "eff_belief": [
                        {
                            "observer": "Bob",
                            "fluent": {"pred": "alive", "args": ["Carol"]},
                            "held": True,
                        }
                    ],
                }
            ],
        }
    )
    assert validate_plan(plan) == []


# --- Affect closure ---


def test_unclosed_affect_caught_with_strict_policy() -> None:
    """Unclosed affect thread is a flaw when policy requires closure."""
    plan = PlotPlan.model_validate(
        {
            "affect_policy": {"unclosed_is_error": True},
            "functions": [
                {
                    "id": "F1",
                    "kind": "villainy",
                    "chapter": 1,
                    "eff_affect": [{"op": "open", "char": "Hero", "kind": "loss"}],
                }
            ],
        }
    )
    flaws = validate_plan(plan)
    assert len(flaws) == 1
    assert "unclosed" in flaws[0]
    assert "loss" in flaws[0]


def test_unclosed_affect_allowed_with_lenient_policy() -> None:
    """Unclosed affect is OK when unclosed_is_error=False (horror genre)."""
    plan = PlotPlan.model_validate(
        {
            "affect_policy": {"unclosed_is_error": False},
            "functions": [
                {
                    "id": "F1",
                    "kind": "villainy",
                    "chapter": 1,
                    "eff_affect": [{"op": "open", "char": "Hero", "kind": "loss"}],
                }
            ],
        }
    )
    assert validate_plan(plan) == []


def test_closed_affect_passes() -> None:
    """An opened and closed affect is clean."""
    plan = PlotPlan.model_validate(
        {
            "affect_policy": {"unclosed_is_error": True},
            "functions": [
                {
                    "id": "F1",
                    "kind": "villainy",
                    "chapter": 1,
                    "eff_affect": [{"op": "open", "char": "Hero", "kind": "loss"}],
                },
                {
                    "id": "F2",
                    "kind": "victory",
                    "chapter": 2,
                    "eff_affect": [{"op": "close", "char": "Hero", "kind": "loss"}],
                },
            ],
        }
    )
    assert validate_plan(plan) == []
