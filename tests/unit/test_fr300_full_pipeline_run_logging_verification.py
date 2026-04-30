"""RED acceptance tests for FR-300 full pipeline run logging verification."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
SCRIPT_PATH = WORKTREE / ".chaplain" / "scripts" / "validate-fsm-single.sh"
DOCS_DIR = WORKTREE / "docs"
INTEGRATION_TEST_PATH = (
    WORKTREE
    / "tests"
    / "integration"
    / "test_fr300_full_pipeline_run_logging_verification.py"
)


def _read_script() -> str:
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    return SCRIPT_PATH.read_text(encoding="utf-8")


@pytest.mark.req("REQ-YG-315")
@pytest.mark.skip(reason="FR-300 RED: awaiting implementation")
class TestFR300FullPipelineRunLoggingVerification:
    """Acceptance criteria coverage for FR-300."""

    def test_ac01_success_gate_requires_full_pipeline_verification(self) -> None:
        """AC-01: Exit 0 only when full pipeline checks pass."""
        script = _read_script()
        assert re.search(r'"\$PASS"\s*-(ge|eq)\s*[0-9]+', script), (
            "Success path must require an explicit minimum PASS threshold "
            "for full-pipeline verification, not only FAIL==0."
        )

    def test_ac02_dispatcher_log_must_exist_and_be_non_empty(self) -> None:
        """AC-02: Fail if logs/fsm-validation/validate-*.log is missing/empty."""
        script = _read_script()
        assert re.search(r'\[\s+-s\s+"\$LOG_FILE"\s+\]', script), (
            "Script must assert dispatcher validation log exists and is non-empty "
            'using a size check (`-s "$LOG_FILE"`).'
        )

    def test_ac03_pipeline_log_must_exist_and_be_non_empty(self) -> None:
        """AC-03: Fail if logs/fsm-pipeline-<topic>-*.log is missing/empty."""
        script = _read_script()
        assert (
            "fsm-pipeline-" in script
        ), "Script must resolve per-topic pipeline log file."
        assert re.search(
            r"PIPELINE_LOG[A-Z_]*=", script
        ), "Script must define a pipeline log path variable."
        assert re.search(
            r'\[\s+-s\s+"\$PIPELINE_LOG[A-Z_]*"\s+\]', script
        ), "Script must fail when the matching pipeline log is missing/empty."

    def test_ac04_progression_markers_are_verified_in_post_run_assertions(self) -> None:
        """AC-04: Verify completion/progression markers from log output."""
        script = _read_script()
        marker = "# --- Post-run assertions ---"
        assert marker in script, "Script must have a post-run assertions section."
        post_run = script.split(marker, 1)[1]
        for required in ("topic_done", "cleaning_up", "completed"):
            assert required in post_run, (
                "Post-run verification must explicitly check progression markers: "
                "topic_done, cleaning_up, completed."
            )

    def test_ac05_output_reports_dispatcher_and_pipeline_log_paths(self) -> None:
        """AC-05: Output includes resolved dispatcher + pipeline log paths."""
        script = _read_script()
        assert (
            "Dispatcher log:" in script
        ), "Script output must print dispatcher log path."
        assert "Pipeline log:" in script, "Script output must print pipeline log path."

    def test_ac06_companion_smoke_test_exists_for_full_run_contract(self) -> None:
        """AC-06: Tests added."""
        assert (
            INTEGRATION_TEST_PATH.exists()
        ), "A companion smoke test for FR-300 must exist in tests/integration/."
        content = INTEGRATION_TEST_PATH.read_text(encoding="utf-8")
        assert "@pytest.mark.integration" in content
        assert "validate-fsm-single.sh" in content

    def test_ac07_docs_include_canonical_command_and_log_expectations(self) -> None:
        """AC-07: Documentation updated."""
        assert DOCS_DIR.exists(), f"Missing docs directory: {DOCS_DIR}"

        matches: list[tuple[Path, str]] = []
        for path in DOCS_DIR.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            if (
                "validate-fsm-single.sh" in text
                and ".chaplain/inbox-fsm/test-pipeline-run.md" in text
            ):
                matches.append((path, text.lower()))

        assert matches, (
            "Docs must include the canonical command:\n"
            "bash .chaplain/scripts/validate-fsm-single.sh "
            ".chaplain/inbox-fsm/test-pipeline-run.md"
        )

        assert any(
            "dispatcher log" in lowered and "pipeline log" in lowered
            for _, lowered in matches
        ), "Docs must describe both dispatcher and per-topic pipeline logs."
