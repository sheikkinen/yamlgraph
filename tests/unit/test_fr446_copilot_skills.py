"""FR-446: Copilot Skill Promotion — verify Tier 1 skills exist.

FR-765 extends the registry with the `graph-authoring` workflow skill and
upgrades the tests from presence checks to substance checks (judgement R-2:
`substance_over_presence` — a gate that checks "does X exist?" must also
check "does X say something?").
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / ".github" / "skills"

TIER_1_SKILLS = [
    "author-graph",
    "author-prompt",
    "release-version",
    "chaplain-ops",
    "run-code-analysis",
    "feature-request",
    "graph-authoring",
]


def _frontmatter(skill_name: str) -> dict:
    text = (SKILLS_DIR / skill_name / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{skill_name}: SKILL.md missing frontmatter"
    block = text.split("---", 2)[1]
    data = yaml.safe_load(block)
    assert isinstance(data, dict), f"{skill_name}: frontmatter is not a mapping"
    return data


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

    @pytest.mark.parametrize("skill_name", TIER_1_SKILLS)
    def test_skill_frontmatter_substance(self, skill_name: str) -> None:
        """Frontmatter must parse and carry a usable discovery contract:
        matching name, a description with a 'Use when:' trigger clause,
        and a non-empty argument-hint (FR-765 R-2)."""
        fm = _frontmatter(skill_name)
        assert fm.get("name") == skill_name
        description = fm.get("description") or ""
        assert "Use when:" in description, f"{skill_name}: no 'Use when:' triggers"
        assert (
            fm.get("argument-hint") or ""
        ).strip(), f"{skill_name}: no argument-hint"


@pytest.mark.req("REQ-YG-423")
class TestGraphAuthoringWorkflowSkill:
    """FR-765: the graph-authoring workflow skill's substance contract."""

    @pytest.fixture()
    def skill_text(self) -> str:
        return (SKILLS_DIR / "graph-authoring" / "SKILL.md").read_text(encoding="utf-8")

    @pytest.fixture()
    def doctrine_text(self) -> str:
        return (SKILLS_DIR / "graph-authoring" / "doctrine.md").read_text(
            encoding="utf-8"
        )

    def test_doctrine_has_required_headings(self, doctrine_text: str) -> None:
        """AC-02: doctrine defines the full workflow contract."""
        for heading in [
            "Input closure",
            "Precedent search",
            "Artifact report",
            "Validation",
            "Escalation",
            "Anti-patterns",
        ]:
            assert (
                heading.lower() in doctrine_text.lower()
            ), f"doctrine.md missing required section: {heading}"

    def test_composes_with_author_skills(self, skill_text: str) -> None:
        """AC-03: composes with author-graph and author-prompt as syntax
        references instead of duplicating them."""
        assert "author-graph" in skill_text
        assert "author-prompt" in skill_text

    def test_rejects_one_shot_generator_with_precedent(
        self, skill_text: str, doctrine_text: str
    ) -> None:
        """AC-04: rejects the one-shot yamlgraph_gen generator as the
        default path and cites the workspace_is_not_boundary / FR-763
        precedent."""
        combined = skill_text + doctrine_text
        assert "yamlgraph_gen" in combined
        assert "workspace_is_not_boundary" in combined
        assert "FR-763" in combined

    def test_requires_lint_and_blocked_command_honesty(
        self, doctrine_text: str
    ) -> None:
        """AC-05: local validation via `yamlgraph graph lint` is mandatory;
        blocked validation records the exact blocked command, never
        claims success."""
        assert "yamlgraph graph lint" in doctrine_text
        assert "blocked" in doctrine_text.lower()

    def test_artifact_closed_delegation_not_judgement(
        self, skill_text: str, doctrine_text: str
    ) -> None:
        """AC-06: uses artifact-closed delegation brief language and
        forbids invoking the judge/review routes (C-2/C-7)."""
        combined = skill_text + doctrine_text
        assert "artifact-closed delegation brief" in combined
        assert "judge-fr" in combined and "review-pr" in combined
        assert "must not invoke" in combined
