"""RED acceptance tests for FR-418 fallback confession gate."""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import hedging_check


@pytest.mark.req("REQ-YG-408")
class TestFR418FallbackConfessionGate:
    """Acceptance tests mapped to FR-418 AC-01..AC-06."""

    def test_ac01_flags_fallback_in_identifier_name(self, tmp_path: Path) -> None:
        py_file = tmp_path / "identifier_case.py"
        py_file.write_text("fallback_value = 1\n")

        findings = hedging_check.scan_file(py_file)

        assert any("FB001" in finding for finding in findings)

    def test_ac02_flags_fallback_in_comment(self, tmp_path: Path) -> None:
        py_file = tmp_path / "comment_case.py"
        py_file.write_text("value = 1  # fallback path for parse errors\n")

        findings = hedging_check.scan_file(py_file)

        assert any("FB001" in finding for finding in findings)

    def test_ac02_flags_fallback_in_docstring(self, tmp_path: Path) -> None:
        py_file = tmp_path / "docstring_case.py"
        py_file.write_text(
            'def parse() -> str:\n    """fallback parser description."""\n    return "ok"\n'
        )

        findings = hedging_check.scan_file(py_file)

        assert any("FB001" in finding for finding in findings)

    def test_ac03_strict_mode_fails_on_unconfessed_fb001(self, tmp_path: Path) -> None:
        py_file = tmp_path / "strict_case.py"
        py_file.write_text("fallback_name = 1\n")

        with patch.object(
            hedging_check.sys,
            "argv",
            ["hedging_check.py", str(tmp_path), "--strict"],
        ):
            exit_code = hedging_check.main()

        assert exit_code == 1

    def test_ac04_strict_mode_fails_on_invalid_confession_mapping(
        self, tmp_path: Path
    ) -> None:
        py_file = tmp_path / "allowlist_case.py"
        py_file.write_text("fallback_name = 1\n")
        key = f"{py_file}:1"

        with (
            patch.object(hedging_check, "ALLOWLIST", {key: "CONF-999"}),
            patch.object(
                hedging_check.sys,
                "argv",
                ["hedging_check.py", str(tmp_path), "--strict"],
            ),
        ):
            exit_code = hedging_check.main()

        assert exit_code == 1

    def test_ac05_detects_pattern2_or_fallback_assignment(self, tmp_path: Path) -> None:
        py_file = tmp_path / "pattern2_case.py"
        py_file.write_text("selected = preferred_items or fallback_items\n")

        findings = hedging_check.scan_file(py_file)

        assert any("or fallback" in finding for finding in findings)

    def test_ac06_existing_pattern1_detection_still_works(self, tmp_path: Path) -> None:
        py_file = tmp_path / "pattern1_case.py"
        py_file.write_text(
            "result = filter_data(items)\nif not result:\n    result = all_items\n"
        )

        findings = hedging_check.scan_file(py_file)

        assert any("if not result: result = ..." in finding for finding in findings)
