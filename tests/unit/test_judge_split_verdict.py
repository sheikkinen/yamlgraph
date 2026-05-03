"""FR-136: Judge SPLIT Verdict — TDD tests.

Verifies that judge prompt files include the SPLIT verdict alongside
APPROVE, AMEND, and REJECT, and that a Scope Count evaluation criterion
exists for detecting multi-concern feature requests.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.req("REQ-YG-143")
class TestJudgeYamlSplitVerdict:
    """.chaplain/graphs/watcher-plan/prompts/judge.yaml must include SPLIT verdict."""

    @pytest.fixture()
    def judge_yaml_content(self) -> str:
        path = (
            REPO_ROOT
            / ".chaplain"
            / "graphs"
            / "watcher-plan"
            / "prompts"
            / "judge.yaml"
        )
        assert path.exists(), f"judge.yaml not found at {path}"
        return path.read_text()

    def test_split_verdict_present(self, judge_yaml_content: str) -> None:
        """SPLIT verdict must appear in the judge prompt."""
        assert "**SPLIT:**" in judge_yaml_content

    def test_approve_verdict_unchanged(self, judge_yaml_content: str) -> None:
        """APPROVE verdict must still be present."""
        assert "**APPROVE:**" in judge_yaml_content

    def test_amend_verdict_unchanged(self, judge_yaml_content: str) -> None:
        """AMEND verdict must still be present."""
        assert "**AMEND:**" in judge_yaml_content

    def test_reject_verdict_unchanged(self, judge_yaml_content: str) -> None:
        """REJECT verdict must still be present."""
        assert "**REJECT:**" in judge_yaml_content

    def test_split_mentions_inbox(self, judge_yaml_content: str) -> None:
        """SPLIT instructions must mention writing to .chaplain/inbox/."""
        assert ".chaplain/inbox/" in judge_yaml_content

    def test_split_mentions_delete_draft(self, judge_yaml_content: str) -> None:
        """SPLIT instructions must mention deleting the original draft."""
        # Accept either "delete" or "Delete" or "remove"
        content_lower = judge_yaml_content.lower()
        assert "delete" in content_lower or "remove" in content_lower

    def test_scope_count_criterion(self, judge_yaml_content: str) -> None:
        """A scope/responsibility evaluation criterion must exist."""
        content_lower = judge_yaml_content.lower()
        assert "single responsibility" in content_lower or "orthogonal" in content_lower


@pytest.mark.req("REQ-YG-143")
class TestJudgeMdSplitVerdict:
    """scripts/chaplain-prompts/judge.md must include SPLIT verdict and Scope Count."""

    @pytest.fixture()
    def judge_md_content(self) -> str:
        path = REPO_ROOT / "scripts" / "chaplain-prompts" / "judge.md"
        assert path.exists(), f"judge.md not found at {path}"
        return path.read_text()

    def test_split_verdict_present(self, judge_md_content: str) -> None:
        """SPLIT verdict must appear in the judge prompt."""
        assert "**SPLIT**" in judge_md_content

    def test_approve_verdict_unchanged(self, judge_md_content: str) -> None:
        """APPROVE verdict must still be present."""
        assert "**APPROVE**" in judge_md_content

    def test_amend_verdict_unchanged(self, judge_md_content: str) -> None:
        """AMEND verdict must still be present."""
        assert "**AMEND**" in judge_md_content

    def test_reject_verdict_unchanged(self, judge_md_content: str) -> None:
        """REJECT verdict must still be present."""
        assert "**REJECT**" in judge_md_content

    def test_scope_count_criterion(self, judge_md_content: str) -> None:
        """Scope Count must appear as an evaluation criterion."""
        assert "Scope Count" in judge_md_content

    def test_scope_count_is_criterion_8(self, judge_md_content: str) -> None:
        """Scope Count must be criterion number 8."""
        assert "8. **Scope Count**" in judge_md_content

    def test_split_mentions_inbox(self, judge_md_content: str) -> None:
        """SPLIT instructions must mention writing to .chaplain/inbox/."""
        assert ".chaplain/inbox/" in judge_md_content

    def test_split_mentions_delete_draft(self, judge_md_content: str) -> None:
        """SPLIT instructions must mention deleting the original draft."""
        content_lower = judge_md_content.lower()
        assert "delete" in content_lower


@pytest.mark.req("REQ-YG-143")
class TestMultiConcernFixture:
    """Smoke-test fixture for a topic that bundles two orthogonal concerns."""

    def test_fixture_exists(self) -> None:
        """Multi-concern fixture file must exist in tests/fixtures/chaplain/."""
        path = REPO_ROOT / "tests" / "fixtures" / "chaplain" / "multi-concern-topic.md"
        assert path.exists(), f"Fixture not found at {path}"

    def test_fixture_has_multiple_concerns(self) -> None:
        """Fixture must describe at least two independent concerns."""
        path = REPO_ROOT / "tests" / "fixtures" / "chaplain" / "multi-concern-topic.md"
        content = path.read_text()
        # Should mention at least two distinct topics
        assert len(content.strip()) > 50, "Fixture too short to describe two concerns"
        content_lower = content.lower()
        # Must explicitly label multiple concerns
        assert (
            "concern" in content_lower or "orthogonal" in content_lower
        ), "Fixture must describe orthogonal concerns"
