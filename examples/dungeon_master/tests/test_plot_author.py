"""FR-563 M4a author + attach: the tolerant boundary parse, the gated setter, the live seam.

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

M4a flips the v3 plot lane from dormant verification to attachable steering. Four moving parts are
witnessed here, all deterministically (no live LLM):

* ``author.parse_plot_plan`` -- the tolerant boundary parse mirroring ``world_state.parse_world_state``:
  drop unknown fields, drop off-alphabet functions, never raise (the LLM JSON is untrusted input).
* ``author.plot_validate_plan`` -- the ``python``-node wrapper the ``plot_plan.yaml`` graph routes on;
  returns ``{"validation": {"ok", "flaws"}}`` merged at top level so the edge condition
  ``validation.ok == true`` resolves (J1: a python node merges a returned dict into state, so the
  wrapper nests under ``validation`` itself rather than relying on ``state_key``).
* ``chapter_nav.write_plot_plan`` -- the sole, GATED owner of ``doc["plot_plan"]`` (FR-558 doctrine,
  J3): it runs ``validate_plan`` and RAISES before committing, so the getter's "validated PlotPlan"
  contract is un-bypassable.
* the FR-560 exclusion seam, which comes alive the instant a plan is attached (AC3) -- the same
  Arnulf-excluded-at-ch3 behavior ``test_plot_exclusion_seam`` pins, re-witnessed through the setter.
"""

from __future__ import annotations

import copy
import pathlib
import re

import pytest

from examples.dungeon_master.api import chapter_nav, chapter_open
from examples.dungeon_master.api.plot import author
from examples.dungeon_master.api.plot import floodmark as fm
from examples.dungeon_master.api.plot.schema import PlotPlan
from examples.dungeon_master.api.plot.validate import validate_plan
from yamlgraph.utils.conditions import evaluate_condition

_DM_DIR = pathlib.Path(__file__).resolve().parent.parent
_PLOT_PLAN_GRAPH = _DM_DIR / "plot_plan.yaml"


def _six_chapter_doc() -> dict:
    """A doc whose ``chapters.order`` makes ``chapter_open._chapter_index`` yield 1..6."""
    cards = {c: {} for c in ("1", "2", "3", "4", "5", "6")}
    return {"chapters": {"order": ["1", "2", "3", "4", "5", "6"], "cards": cards}}


# --- AC1: tolerant parse drops junk -----------------------------------------------------------
def test_tolerant_parse_drops_junk():
    """An unknown top-level field and an off-alphabet function are dropped, never raised on."""
    raw = copy.deepcopy(fm.floodmark_json)
    raw["bogus_field"] = 1
    raw["functions"] = raw["functions"] + [
        {"id": "Bad", "kind": "not_a_kind", "subject": "X", "chapter": 2}
    ]

    plan = author.parse_plot_plan(raw)

    assert isinstance(plan, PlotPlan)
    assert not hasattr(plan, "bogus_field")
    assert [f.id for f in plan.functions] == ["F1", "Fr", "Ff"]  # "Bad" dropped


def test_tolerant_parse_never_raises_on_garbage():
    """Non-dict / structurally broken input yields an empty plan, not an exception."""
    assert author.parse_plot_plan(None) == PlotPlan()
    assert author.parse_plot_plan("a prose string") == PlotPlan()
    assert author.parse_plot_plan({"functions": "not a list"}) == PlotPlan()


# --- AC2: authored plan validates -------------------------------------------------------------
def test_authored_plan_round_trips_and_validates():
    """The floodmark JSON parsed through the boundary validates ok (round-trips the fixture)."""
    plan = author.parse_plot_plan(copy.deepcopy(fm.floodmark_json))
    result = validate_plan(plan)
    assert result.ok, result.flaws


# --- AC3: attach activates the seam -----------------------------------------------------------
def test_attach_activates_exclusion_seam():
    """Before attach ch3 does not exclude Arnulf; after ``write_plot_plan`` it does (the seam)."""
    doc = _six_chapter_doc()
    plan = author.parse_plot_plan(copy.deepcopy(fm.floodmark_json))

    before = chapter_open.compile_opening_onepager(doc, "3")["must_exclude"]
    assert "Arnulf" not in before

    chapter_nav.write_plot_plan(doc, plan)

    after = chapter_open.compile_opening_onepager(doc, "3")["must_exclude"]
    assert "Arnulf" in after


# --- AC4: setter is the sole owner AND gates the write ----------------------------------------
def test_setter_round_trips_through_the_getter():
    """``write_plot_plan`` then ``attached_plot_plan`` returns the same typed plan."""
    doc: dict = {}
    plan = author.parse_plot_plan(copy.deepcopy(fm.floodmark_json))
    chapter_nav.write_plot_plan(doc, plan)
    got = chapter_nav.attached_plot_plan(doc)
    assert got == plan


def test_setter_is_the_sole_api_writer_of_plot_plan():
    """No api/ module writes ``doc["plot_plan"]`` except ``chapter_nav`` (FR-556 discipline)."""
    api_dir = _DM_DIR / "api"
    pattern = re.compile(r"""\[['"]plot_plan['"]\]\s*=""")
    writers = sorted(
        p.name for p in api_dir.rglob("*.py") if pattern.search(p.read_text(encoding="utf-8"))
    )
    assert writers == ["chapter_nav.py"]


def test_setter_gates_the_write_and_raises_on_flaw():
    """A plan with a validation flaw raises ``InvalidPlotPlan`` and leaves the doc untouched (J3)."""
    doc: dict = {}
    bad = fm.world_revival_variant  # one lifecycle_violation
    assert not validate_plan(bad).ok  # guard: the fixture really is invalid

    with pytest.raises(chapter_nav.InvalidPlotPlan):
        chapter_nav.write_plot_plan(doc, bad)

    assert "plot_plan" not in doc


# --- AC5: graph lints & routes deterministically (no live LLM) --------------------------------
def test_plot_plan_graph_lints_clean():
    """``plot_plan.yaml`` has no error-severity lint issues."""
    from yamlgraph.linter import lint_graph

    result = lint_graph(_PLOT_PLAN_GRAPH, project_root=_DM_DIR)
    errors = [i for i in result.issues if i.severity == "error"]
    assert not errors, errors


def test_validator_routes_valid_plan_to_done():
    """A valid plan_raw yields ``validation.ok == true`` -> the edge to END fires."""
    state = author.plot_validate_plan({"raw": copy.deepcopy(fm.floodmark_json)})
    assert state["validation"]["ok"] is True
    assert evaluate_condition("validation.ok == true", state)
    assert not evaluate_condition("validation.ok == false", state)


def test_validator_routes_invalid_plan_to_repair():
    """An invalid plan_raw yields ``validation.ok == false`` -> the edge to repair_plan fires."""
    invalid_raw = fm.world_revival_variant.model_dump()
    state = author.plot_validate_plan({"raw": invalid_raw})
    assert state["validation"]["ok"] is False
    assert evaluate_condition("validation.ok == false", state)
    assert not evaluate_condition("validation.ok == true", state)
