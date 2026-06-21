"""FR-560 M1 report snapshot: the human-inspectable projection table.

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

``report.py`` lives under ``api/plot/`` (not ``examples/demos/``), so the demo-gate does not apply
(FR-560 J4e). Instead this fixture-asserted snapshot pins the rendered table: the protected set, the
per-chapter cast/exclusion rows, and the grounding verdict. Pure -- no ``unified-planning``.
"""

from __future__ import annotations

from examples.dungeon_master.api.plot import floodmark as fm
from examples.dungeon_master.api.plot import report


def test_report_renders_protected_set():
    text = report.render_report(fm.floodmark)
    assert "PROTECTED" in text
    assert "Arnulf" in text


def test_report_marks_presumed_dead_before_reveal():
    """Chapter 3 (pre-reveal) must list Arnulf as must-NOT-appear."""
    text = report.render_report(fm.floodmark)
    ch3 = next(line for line in text.splitlines() if line.lstrip().startswith("3 "))
    assert "Arnulf" in ch3.split("|")[-1]


def test_report_shows_reveal_cast_at_chapter_six():
    """Chapter 6 cast must carry the reveal observers (Clan)."""
    text = report.render_report(fm.floodmark)
    ch6 = next(line for line in text.splitlines() if line.lstrip().startswith("6 "))
    assert "Clan" in ch6


def test_report_states_grounding_verdict():
    text = report.render_report(fm.floodmark)
    assert "belief-grounding: OK" in text
