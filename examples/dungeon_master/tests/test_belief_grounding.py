"""FR-560 M1 belief-grounding: the ungrounded-reveal narrative invariant.

Example tests are requirement-exempt (FR-474 J3): NO ``@pytest.mark.req``, NO capability YAML.

M1's grounding check is **ungrounded-reveal ONLY** (FR-560 J2 -- the "unclosed belief gap" branch
was cut; it had no witness test and is M3-adjacent). A reveal that sets ``believes(obs, alive(c))``
true must un-tell a secret an earlier-ordered beat (or the initial belief) actually told -- otherwise
it is an ``ungrounded_reveal`` flaw (the code aligned to design section 2's ``PlanFlaw`` Literal, J1).
Pure: no ``unified-planning`` import.
"""

from __future__ import annotations

from examples.dungeon_master.api.plot import floodmark as fm
from examples.dungeon_master.api.plot import validate as v


def test_canonical_floodmark_is_grounded():
    """Fr's reveal is grounded by F1 flipping the clan's belief to dead first -- no flaw."""
    result = v.validate_plan(fm.floodmark)
    codes = [flaw.code for flaw in result.flaws]
    assert "ungrounded_reveal" not in codes
    assert result.ok is True


def test_ungrounded_reveal_variant_is_flagged():
    """A reveal flipping a belief no earlier beat ever opened is one ungrounded_reveal flaw."""
    result = v.validate_plan(fm.ungrounded_reveal_variant)
    codes = [flaw.code for flaw in result.flaws]
    assert codes.count("ungrounded_reveal") == 1
    assert result.ok is False
