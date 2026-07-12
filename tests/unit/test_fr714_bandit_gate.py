"""FR-714 witnesses: bandit gate + nosec confession coverage.

The gate-truth contract: every documented quality claim has a gate, and
the confession discipline covers both suppression dialects (ruff noqa,
bandit nosec).
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestNosecConfessionCoverage:
    """AC-03: nosec markers are counted by the confession scanner."""

    @pytest.mark.req("REQ-YG-542")
    def test_nosec_markers_are_found(self, tmp_path):
        from scripts.noqa_coverage import find_noqa_in_file

        # Markers assembled at runtime so the confession scanner does not
        # match this test file's own source.
        nosec = "# " + "nosec"
        noqa = "# " + "noqa"
        f = tmp_path / "sample.py"
        f.write_text(f"x = 1  {nosec} B602\ny = 2  {noqa}: E402\nz = 3  {nosec}\n")
        found = find_noqa_in_file(f)
        assert (1, "B602") in found, "specific nosec must be counted"
        assert (2, "E402") in found, "noqa must still be counted"
        assert (3, "ALL") in found, "blanket nosec must be counted"

    @pytest.mark.req("REQ-YG-542")
    def test_bandit_hook_is_wired(self):
        """The gate exists in pre-commit — a claim with no gate decays
        into a lie (detection_without_enforcement)."""
        config = (REPO_ROOT / ".pre-commit-config.yaml").read_text()
        assert "bandit-security" in config
        assert "-ll" in config, "gate must block medium+ severity"

    @pytest.mark.req("REQ-YG-542")
    def test_coverage_gate_matches_doc_claim(self):
        """AC-04: CLAUDE.md's documented threshold == enforced threshold."""
        import re

        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        claude = (REPO_ROOT / "CLAUDE.md").read_text()
        enforced = re.search(r"--cov-fail-under=(\d+)", pyproject).group(1)
        assert f"{enforced}% coverage threshold" in claude, (
            f"CLAUDE.md must document the enforced gate ({enforced}%) — "
            "doc and gate disagreed before FR-714"
        )
