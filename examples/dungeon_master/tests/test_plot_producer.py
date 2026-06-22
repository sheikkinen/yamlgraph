"""FR-565 producer integration: author_plot_plan + flag + graceful degradation.

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

The producer function ``doc_ops.author_plot_plan`` runs the ``plot_plan.yaml`` graph (mocked),
parses through the tolerant boundary, and attaches through the gated ``write_plot_plan`` seam.
Tests are deterministic (mocked graph, no LLM); the end-to-end render is witnessed by the demo
path (AC6).

AC1: producer→parse→gate→attach pipeline with mocked graph returning floodmark_json.
AC2: dormancy invariant — no call, no plan.
AC3: graceful degradation — flawed plan raises InvalidPlotPlan, doc has no plan.
AC4: CLI flag plumbing.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from examples.dungeon_master.api import chapter_nav, doc_ops, story_doc
from examples.dungeon_master.api.chapter_nav import InvalidPlotPlan
from examples.dungeon_master.api.plot import floodmark as fm


def _doc_with_synopsis(text: str = "A presumed-dead patriarch returns") -> dict:
    """Minimal doc with a synopsis, enough for ``author_plot_plan``."""
    return {"synopsis": {"text": text, "reviewed": True}}


# --- AC1: Producer→parse→gate→attach pipeline ------------------------------------


@pytest.mark.asyncio
async def test_producer_attaches_valid_plan(tmp_path: Path):
    """Mocked graph returns floodmark_json; plan is attached and persisted."""
    doc = _doc_with_synopsis()
    mock_result = {"plan_raw": fm.floodmark_json}

    with patch.object(
        doc_ops,
        "get_app",
        return_value=AsyncMock(ainvoke=AsyncMock(return_value=mock_result)),
    ):
        await doc_ops.author_plot_plan(doc, tmp_path)

    plan = chapter_nav.attached_plot_plan(doc)
    assert plan is not None, "plan must be attached after author_plot_plan"
    assert len(plan.functions) == 3
    assert plan.functions[0].id == "F1"

    # Verify persisted to disk
    persisted = story_doc.read(tmp_path)
    assert "plot_plan" in persisted


@pytest.mark.asyncio
async def test_producer_skips_empty_synopsis(tmp_path: Path):
    """Empty synopsis → author_plot_plan returns without invoking graph."""
    doc = _doc_with_synopsis("")

    with patch.object(
        doc_ops, "get_app", return_value=AsyncMock(ainvoke=AsyncMock())
    ) as mock_get:
        await doc_ops.author_plot_plan(doc, tmp_path)

    mock_get.return_value.ainvoke.assert_not_awaited()
    assert chapter_nav.attached_plot_plan(doc) is None


# --- AC2: Dormancy invariant ----------------------------------------------------


def test_dormancy_no_plan_without_call():
    """A fresh doc has no plan — dormancy invariant."""
    doc = _doc_with_synopsis()
    assert chapter_nav.attached_plot_plan(doc) is None


# --- AC3: Graceful degradation ---------------------------------------------------


@pytest.mark.asyncio
async def test_producer_raises_on_flawed_plan(tmp_path: Path):
    """A plan that fails validation raises InvalidPlotPlan — doc has no plan."""
    # world_revival_variant fails the lifecycle check
    flawed_json = fm.floodmark_json.copy()
    flawed_json["functions"] = [
        {
            **fm.floodmark_json["functions"][0],
            "eff_world": [{"pred": "alive", "args": ["Arnulf"], "value": False}],
            "eff_belief": [],
        },
        {
            **fm.floodmark_json["functions"][1],
            "eff_world": [{"pred": "alive", "args": ["Arnulf"], "value": True}],
            "eff_belief": [],
        },
        fm.floodmark_json["functions"][2],
    ]
    mock_result = {"plan_raw": flawed_json}
    doc = _doc_with_synopsis()

    with (
        patch.object(
            doc_ops,
            "get_app",
            return_value=AsyncMock(ainvoke=AsyncMock(return_value=mock_result)),
        ),
        pytest.raises(InvalidPlotPlan),
    ):
        await doc_ops.author_plot_plan(doc, tmp_path)

    assert chapter_nav.attached_plot_plan(doc) is None, "flawed plan must not attach"


@pytest.mark.asyncio
async def test_producer_returns_on_none_plan_raw(tmp_path: Path):
    """Graph returns no plan_raw → author_plot_plan returns silently."""
    doc = _doc_with_synopsis()
    mock_result = {"plan_raw": None}

    with patch.object(
        doc_ops,
        "get_app",
        return_value=AsyncMock(ainvoke=AsyncMock(return_value=mock_result)),
    ):
        await doc_ops.author_plot_plan(doc, tmp_path)

    assert chapter_nav.attached_plot_plan(doc) is None


# --- AC4: CLI flag ---------------------------------------------------------------


def test_cli_flag_exists():
    """generate.py's generate_story accepts enable_plot_plan parameter."""
    import inspect

    from examples.dungeon_master.scripts import generate

    sig = inspect.signature(generate.generate_story)
    assert (
        "enable_plot_plan" in sig.parameters
    ), "generate_story must accept enable_plot_plan"
