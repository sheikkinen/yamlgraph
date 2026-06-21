"""FR-560 M1 belief-lane projection: the pure derived-set queries.

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

Projection is a **pure** function of the authored ``PlotPlan``'s belief timeline -- it does NOT
import ``unified-planning`` and never touches a planner. These tests pin the three design-section-5
signatures (``chapter_cast``/``exclusion_set``/``protected_set``) and the load-bearing non-circular
``exclusion_set`` rule (FR-560 J3): a character is excluded at chapter ``c`` iff the latest belief
beat about ``alive(X)`` at chapter <= c sets ``held=False`` for some observer and no reveal restores
it at chapter <= c.
"""

from __future__ import annotations

from examples.dungeon_master.api.plot import floodmark as fm
from examples.dungeon_master.api.plot import project


def test_exclusion_set_excludes_presumed_dead_before_reveal():
    """Arnulf is believed dead (F1 flips belief at ch1); the reveal Fr is ch6."""
    assert "Arnulf" in project.exclusion_set(fm.floodmark, 3)


def test_exclusion_set_boundary_one_chapter_before_reveal():
    """Boundary (J3): ch5 is still pre-reveal -- the floodmark guard must stay active."""
    assert "Arnulf" in project.exclusion_set(fm.floodmark, 5)


def test_exclusion_set_releases_after_reveal():
    """At ch6 the reveal lands -- belief is restored, so Arnulf is no longer excluded."""
    assert "Arnulf" not in project.exclusion_set(fm.floodmark, 6)


def test_chapter_cast_includes_reveal_subject_and_observers():
    """The reveal Fr (subject Arnulf, observers [Clan]) and Ff (subject Hilde) play at ch6."""
    cast = project.chapter_cast(fm.floodmark, 6)
    assert "Arnulf" in cast
    assert "Clan" in cast


def test_protected_set_equals_plan_goals():
    """The author invariants G are the plan's goal characters -- here, Arnulf stays alive."""
    assert set(project.protected_set(fm.floodmark)) == {"Arnulf"}
