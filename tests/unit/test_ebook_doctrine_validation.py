"""Tests for FR-103: eBook Judge-Amend Subgraph.

Verifies that Ch01 Doctrine contains all 10 Commandments quoted verbatim.
REQ-YG-092: Chapter validation detects fabricated doctrine content.
"""

from pathlib import Path

import pytest

# The 10 Commandments — exact phrases that MUST appear verbatim
COMMANDMENTS = [
    "1. **Thou shalt research before coding**",
    "2. **Thou shalt demonstrate with example**",
    "3. **Thou shalt not utter code in vain**",
    "4. **Thou shalt honor existing patterns**",
    "5. **Thou shalt sanctify thy outputs with types**",
    "6. **Thou shalt bear witness of thy errors**",
    "7. **Thou shalt be faithful to TDD**",
    "8. **Thou shalt kill all entropy and false idols**",
    "9. **Thou shalt define and observe operational truth**",
    "10. **Thou shalt preserve and improve the doctrine**",
]

# Source file for reference
SOURCE_FILE = Path(".github/copilot-instructions.md")


def verify_commandments_verbatim(chapter_content: str) -> dict:
    """Check if all 10 Commandments appear verbatim in chapter content.

    Returns:
        {
            "passed": bool,
            "found": list[str],      # Commandments found verbatim
            "missing": list[str],    # Commandments not found
            "fabricated": list[str], # Lines containing "Thou shalt" not matching source
        }
    """
    found = []
    missing = []

    for cmd in COMMANDMENTS:
        if cmd in chapter_content:
            found.append(cmd)
        else:
            missing.append(cmd)

    # Detect fabrication: "Thou shalt" lines that don't match any commandment
    fabricated = []
    for line in chapter_content.split("\n"):
        if "Thou shalt" in line:
            # Check if this line contains a known commandment
            is_known = any(cmd in line for cmd in COMMANDMENTS)
            if not is_known:
                fabricated.append(line.strip())

    return {
        "passed": len(missing) == 0 and len(fabricated) == 0,
        "found": found,
        "missing": missing,
        "fabricated": fabricated,
    }


class TestDoctrineValidation:
    """Test suite for doctrine chapter validation."""

    @pytest.mark.req("REQ-YG-092")
    def test_detects_all_commandments_when_present(self):
        """Should pass when all 10 Commandments are quoted verbatim."""
        # Chapter with all commandments verbatim
        chapter = """# Doctrine: The Scripture Decoded

As defined in `.github/copilot-instructions.md`:

## The 10 Commandments

> 1. **Thou shalt research before coding**
> 2. **Thou shalt demonstrate with example**
> 3. **Thou shalt not utter code in vain**
> 4. **Thou shalt honor existing patterns**
> 5. **Thou shalt sanctify thy outputs with types**
> 6. **Thou shalt bear witness of thy errors**
> 7. **Thou shalt be faithful to TDD**
> 8. **Thou shalt kill all entropy and false idols**
> 9. **Thou shalt define and observe operational truth**
> 10. **Thou shalt preserve and improve the doctrine**
"""
        result = verify_commandments_verbatim(chapter)

        assert result["passed"] is True
        assert len(result["found"]) == 10
        assert len(result["missing"]) == 0
        assert len(result["fabricated"]) == 0

    @pytest.mark.req("REQ-YG-092")
    def test_detects_missing_commandments(self):
        """Should fail when commandments are missing."""
        # Chapter missing commandments 9 and 10
        chapter = """# Doctrine

> 1. **Thou shalt research before coding**
> 2. **Thou shalt demonstrate with example**
> 3. **Thou shalt not utter code in vain**
> 4. **Thou shalt honor existing patterns**
> 5. **Thou shalt sanctify thy outputs with types**
> 6. **Thou shalt bear witness of thy errors**
> 7. **Thou shalt be faithful to TDD**
> 8. **Thou shalt kill all entropy and false idols**
"""
        result = verify_commandments_verbatim(chapter)

        assert result["passed"] is False
        assert len(result["found"]) == 8
        assert len(result["missing"]) == 2
        assert (
            "9. **Thou shalt define and observe operational truth**"
            in result["missing"]
        )
        assert (
            "10. **Thou shalt preserve and improve the doctrine**" in result["missing"]
        )

    @pytest.mark.req("REQ-YG-092")
    def test_detects_fabricated_commandments(self):
        """Should detect fabricated commandments (the FR-100 bug)."""
        # Chapter with fabricated commandments (as happened in FR-100)
        chapter = """# Doctrine

> 1. **Thou shalt research before coding**
> 2. **Thou shalt always write tests first**
> 3. **Thou shalt never use global variables**
> 4. **Thou shalt document all functions**
"""
        result = verify_commandments_verbatim(chapter)

        assert result["passed"] is False
        assert len(result["fabricated"]) == 3  # 3 fabricated lines
        # The fabricated ones should be detected
        assert any("always write tests first" in f for f in result["fabricated"])
        assert any("never use global variables" in f for f in result["fabricated"])
        assert any("document all functions" in f for f in result["fabricated"])

    @pytest.mark.req("REQ-YG-092")
    def test_source_file_contains_commandments(self):
        """Verify source file has all 10 Commandments (sanity check)."""
        if not SOURCE_FILE.exists():
            pytest.skip("Source file not found (running outside repo root)")

        source_content = SOURCE_FILE.read_text(encoding="utf-8")

        for cmd in COMMANDMENTS:
            # Extract just the "Thou shalt..." part
            thou_shalt_part = cmd.split("**")[1]  # Gets "Thou shalt..."
            assert thou_shalt_part in source_content, f"Missing: {thou_shalt_part}"
