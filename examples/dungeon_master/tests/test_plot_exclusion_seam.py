"""FR-560 M1 live exclusion seam: plan-optional, byte-identical-when-absent.

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

The strangler-fig seam (FR-560 J3): when a validated ``PlotPlan`` is attached to the doc,
``compile_opening_onepager`` unions ``exclusion_set(plan, ordinal)`` ids into ``must_exclude``
BEFORE the existing ``[:12]`` truncation. Two impedance bridges are pinned and exercised here:

* **cid -> ordinal:** the director keys by chapter-id *string*; ``exclusion_set`` keys by integer
  ordinal. The bridge is ``chapter_open._chapter_index`` (1-based from ``chapters.order``). The doc
  below has order ``["1".."6"]`` so cid ``"3"`` -> ordinal 3 and cid ``"6"`` -> ordinal 6.
* **id -> display name:** M1 is scoped to ``id == display_name`` (frozen in the seam docstring), so
  the bare id string ``"Arnulf"`` is what lands in ``must_exclude``.

When no plan is attached the function is byte-for-byte unchanged -- the characterization test pins
that additive-only contract.
"""

from __future__ import annotations

from examples.dungeon_master.api import chapter_open
from examples.dungeon_master.api.plot import floodmark as fm


def _doc() -> dict:
    """A six-chapter doc whose ``chapters.order`` makes ``_chapter_index`` yield 1..6.

    Chapter 2's seam packet carries a pre-existing opening constraint so the characterization
    test proves the seam unions *additively* (never drops the reconstructed v2 constraint).
    """
    cards = {c: {} for c in ("1", "2", "3", "4", "5", "6")}
    cards["2"]["seam_packet"] = {"opening_constraints": ["FORBID: the flood recedes"]}
    return {"chapters": {"order": ["1", "2", "3", "4", "5", "6"], "cards": cards}}


def test_seam_adds_exclusion_before_reveal():
    """With the floodmark plan attached, ch3 must exclude the presumed-dead Arnulf."""
    doc = _doc()
    doc["plot_plan"] = fm.floodmark
    onepager = chapter_open.compile_opening_onepager(doc, "3")
    assert "Arnulf" in onepager["must_exclude"]


def test_seam_releases_exclusion_after_reveal():
    """At ch6 the reveal landed -- the seam adds nothing, so Arnulf is absent."""
    doc = _doc()
    doc["plot_plan"] = fm.floodmark
    onepager = chapter_open.compile_opening_onepager(doc, "6")
    assert "Arnulf" not in onepager["must_exclude"]


def test_seam_is_byte_identical_without_a_plan():
    """No plan attached -> must_exclude is exactly the reconstructed v2 constraints (additive-only)."""
    doc = _doc()
    onepager = chapter_open.compile_opening_onepager(doc, "3")
    assert onepager["must_exclude"] == ["FORBID: the flood recedes"]


def test_seam_preserves_reconstructed_constraint_when_adding():
    """The plan tightens, it never removes -- the v2 constraint and the plan exclusion coexist."""
    doc = _doc()
    doc["plot_plan"] = fm.floodmark
    onepager = chapter_open.compile_opening_onepager(doc, "3")
    assert "FORBID: the flood recedes" in onepager["must_exclude"]
    assert "Arnulf" in onepager["must_exclude"]
