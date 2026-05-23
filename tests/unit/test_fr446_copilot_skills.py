"""FR-446: Copilot Skill Promotion — verify Tier 1 skills exist."""

from __future__ import annotations

from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / ".github" / "skills"

TIER_1_SKILLS = [
    "author-graph",
    "author-prompt",
    "release-version",
    "chaplain-ops",
    "run-code-analysis",
    "feature-request",
]


@pytest.mark.req("REQ-YG-423")
class TestCopilotSkillPromotion:
    """Verify all Tier 1 skills have SKILL.md files."""

    @pytest.mark.parametrize("skill_name", TIER_1_SKILLS)
    def test_skill_md_exists(self, skill_name: str) -> None:
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Missing SKILL.md for {skill_name}"

    @pytest.mark.parametrize("skill_name", TIER_1_SKILLS)
    def test_skill_md_not_empty(self, skill_name: str) -> None:
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_file.read_text()
        assert (
            len(content) > 100
        ), f"SKILL.md for {skill_name} too short ({len(content)} bytes)"
