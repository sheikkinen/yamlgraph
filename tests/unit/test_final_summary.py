"""Tests for scripts/final_summary.py — pre-commit summary hook.

FR-080: Infrastructure Script Unit Tests — Phase 5 (final_summary).
"""

import pytest

from scripts import final_summary

pytestmark = pytest.mark.process


@pytest.mark.req("REQ-YG-063")
class TestMain:
    """Tests for main() function."""

    def test_returns_zero(self) -> None:
        """Main should always return 0 (success)."""
        exit_code = final_summary.main()

        assert exit_code == 0

    def test_prints_final_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Main should print final summary message with Distill reminder."""
        final_summary.main()

        captured = capsys.readouterr()
        assert "Final summary OK" in captured.out
        assert "Distill" in captured.out
        assert "diary/" in captured.out
