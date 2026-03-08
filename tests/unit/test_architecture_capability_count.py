"""Tests for ARCHITECTURE.md capability/requirement count consistency.

FR-154: Ensures the capability and requirement counts in the ARCHITECTURE.md
summary sentence match the actual capability table.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.req("REQ-YG-150")
class TestArchitectureCapabilityCount:
    """ARCHITECTURE.md summary must reflect actual capability table counts."""

    def test_capability_count_matches_table(self) -> None:
        """Capability count in summary sentence must equal table row count."""
        arch_path = REPO_ROOT / "ARCHITECTURE.md"
        text = arch_path.read_text()

        # Count data rows in capability summary table (lines starting with "| <digit>")
        table_rows = re.findall(r"^\| \d+", text, re.MULTILINE)
        actual_cap_count = len(table_rows)

        # Extract count from summary sentence
        match = re.search(r"implements \*\*(\d+) capabilities\*\*", text)
        assert match, "Could not find capability count in ARCHITECTURE.md"
        documented_count = int(match.group(1))

        assert documented_count == actual_cap_count, (
            f"ARCHITECTURE.md says {documented_count} capabilities "
            f"but table has {actual_cap_count} rows"
        )

    def test_requirement_count_matches_table(self) -> None:
        """Requirement count in summary sentence must equal unique REQ-YG-IDs in document."""
        arch_path = REPO_ROOT / "ARCHITECTURE.md"
        text = arch_path.read_text()

        # Extract all unique REQ-YG-IDs from the entire document
        all_reqs = set(re.findall(r"REQ-YG-\d+", text))
        actual_req_count = len(all_reqs)

        # Extract count from summary sentence
        match = re.search(r"covering \*\*(\d+) requirements\*\*", text)
        assert match, "Could not find requirement count in ARCHITECTURE.md"
        documented_count = int(match.group(1))

        assert documented_count == actual_req_count, (
            f"ARCHITECTURE.md says {documented_count} requirements "
            f"but document contains {actual_req_count} unique REQ-YG-IDs"
        )
