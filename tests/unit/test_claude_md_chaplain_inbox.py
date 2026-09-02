"""FR-163 chaplain inbox instructions — retired under FR-942.

Operator amendment during FR-942 enforcement (2026-08-31): the chaplain
runtime is not running, so the Submitting Proposals section was deleted
from BOTH per-turn instruction files rather than deduplicated into the
doctrine. These witnesses pin the retirement so a stale copy cannot
silently return to either file.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.req("REQ-YG-153")
class TestSubmittingProposalsRetired:
    """The Submitting Proposals section must not exist in instruction files."""

    def test_claude_md_has_no_submitting_proposals_section(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        assert "### Submitting Proposals" not in content, (
            "Submitting Proposals was retired by FR-942 (operator amendment: "
            "chaplain runtime not running) — do not reintroduce in CLAUDE.md"
        )

    def test_doctrine_has_no_submitting_proposals_section(self):
        content = (REPO_ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        assert "### Submitting Proposals" not in content, (
            "Submitting Proposals was retired by FR-942 (operator amendment: "
            "chaplain runtime not running) — do not reintroduce in doctrine"
        )
