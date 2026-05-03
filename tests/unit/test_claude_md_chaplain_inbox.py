"""Tests for FR-163: Chaplain inbox instructions in CLAUDE.md.

Verifies that CLAUDE.md documents the .chaplain/inbox/ workflow
so Claude Code sessions can discover the autonomous proposal pipeline.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.req("REQ-YG-153")
class TestClaudeMdChaplainInbox:
    """Verify CLAUDE.md contains chaplain inbox instructions."""

    def test_claude_md_has_submitting_proposals_section(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text()
        assert (
            "### Submitting Proposals" in content
        ), "CLAUDE.md must have a 'Submitting Proposals' subsection (FR-163 AC-1)"

    def test_claude_md_mentions_chaplain_inbox(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text()
        assert (
            ".chaplain/inbox/" in content
        ), "CLAUDE.md must mention .chaplain/inbox/ path (FR-163 AC-4)"

    def test_claude_md_mentions_watch_daemon(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text()
        assert (
            ".chaplain/scripts/start-system.sh" in content
        ), "CLAUDE.md must reference the start-system.sh daemon"

    def test_claude_md_mentions_plan_judge_enforce(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text()
        assert (
            "Plan" in content and "Judge" in content and "Enforce" in content
        ), "CLAUDE.md must describe the Plan → ... → Judge → Enforce pipeline"

    def test_section_placed_before_development_commands(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text()
        proposals_pos = content.find("### Submitting Proposals")
        dev_commands_pos = content.find("## Development Commands")
        assert proposals_pos != -1, "Submitting Proposals section not found"
        assert dev_commands_pos != -1, "Development Commands section not found"
        assert (
            proposals_pos < dev_commands_pos
        ), "Submitting Proposals must appear before Development Commands"

    def test_section_placed_after_development_process(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text()
        reflect_pos = content.find("### 4. Reflect")
        proposals_pos = content.find("### Submitting Proposals")
        assert reflect_pos != -1, "'Reflect' section not found"
        assert proposals_pos != -1, "Submitting Proposals section not found"
        assert (
            reflect_pos < proposals_pos
        ), "Submitting Proposals must appear after the Reflect section"

    def test_matches_canonical_source(self):
        """Section text must match .github/copilot-instructions.md verbatim."""
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text()
        copilot_md = (REPO_ROOT / ".github" / "copilot-instructions.md").read_text()

        # Extract "### Submitting Proposals" section from both files
        for source, name in [
            (claude_md, "CLAUDE.md"),
            (copilot_md, "copilot-instructions.md"),
        ]:
            assert (
                "### Submitting Proposals" in source
            ), f"{name} missing 'Submitting Proposals' section"

        def extract_section(text: str) -> str:
            start = text.index("### Submitting Proposals")
            # Find next heading (## or ###) or end of file
            rest = text[start + len("### Submitting Proposals") :]
            for i, line in enumerate(rest.split("\n")):
                if i > 0 and line.startswith("#"):
                    end = (
                        start
                        + len("### Submitting Proposals")
                        + sum(len(line_text) + 1 for line_text in rest.split("\n")[:i])
                    )
                    return text[start:end].strip()
            return text[start:].strip()

        claude_section = extract_section(claude_md)
        copilot_section = extract_section(copilot_md)
        assert claude_section == copilot_section, (
            "Submitting Proposals section must match canonical source verbatim.\n"
            f"CLAUDE.md:\n{claude_section}\n\n"
            f"copilot-instructions.md:\n{copilot_section}"
        )
