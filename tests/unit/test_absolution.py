"""Tests for scripts/absolution.py — pre-commit summary hook.

FR-080: Infrastructure Script Unit Tests — Phase 5 (absolution).
"""

import pytest

from scripts import absolution


@pytest.mark.req("REQ-YG-063")
class TestMain:
    """Tests for main() function."""

    def test_returns_zero(self) -> None:
        """Main should always return 0 (success)."""
        exit_code = absolution.main()

        assert exit_code == 0

    def test_prints_absolution(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Main should print absolution message with Distill reminder."""
        absolution.main()

        captured = capsys.readouterr()
        assert "Absolution granted" in captured.out
        assert "Distill" in captured.out
        assert "diary/" in captured.out
