"""Tests for FR-160: CHANGELOG FR-154 REQ-ID correction.

Verifies that the CHANGELOG.md entry for FR-154 (Architecture Capability
Count Guard) references REQ-YG-150 (CAP-52), not REQ-YG-146 (CAP-48).
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


@pytest.mark.req("REQ-YG-150")
class TestFR154ChangelogReqId:
    """FR-154 CHANGELOG entry cites the correct requirement ID."""

    def test_fr154_entry_references_req_yg_150(self):
        """FR-154 line must contain (REQ-YG-150), not (REQ-YG-146)."""
        text = CHANGELOG.read_text()
        fr154_lines = [ln for ln in text.splitlines() if "FR-154" in ln]
        assert fr154_lines, "No FR-154 line found in CHANGELOG.md"
        entry = fr154_lines[0]
        assert (
            "(REQ-YG-150)" in entry
        ), f"FR-154 entry has wrong REQ-ID. Expected (REQ-YG-150), got: {entry}"

    def test_fr154_entry_does_not_reference_req_yg_146(self):
        """FR-154 line must NOT contain (REQ-YG-146) — that belongs to CAP-48."""
        text = CHANGELOG.read_text()
        fr154_lines = [ln for ln in text.splitlines() if "FR-154" in ln]
        assert fr154_lines, "No FR-154 line found in CHANGELOG.md"
        entry = fr154_lines[0]
        assert (
            "(REQ-YG-146)" not in entry
        ), f"FR-154 entry still cites wrong REQ-ID (REQ-YG-146): {entry}"
