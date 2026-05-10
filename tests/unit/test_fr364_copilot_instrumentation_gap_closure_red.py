"""RED acceptance tests for FR-364 Copilot instrumentation gap closure."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTRUMENT_SCRIPT = REPO_ROOT / "scripts" / "copilot_instrument.sh"
EXTRACTOR_SCRIPT = REPO_ROOT / "scripts" / "extract_copilot_events.py"
FINDINGS_DOC = REPO_ROOT / "docs" / "copilot-instrumentation-poc.md"


def _run_extractor(run_dir: Path) -> list[dict]:
    result = subprocess.run(
        [sys.executable, str(EXTRACTOR_SCRIPT), str(run_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def _write_semantic_fixture(run_dir: Path) -> None:
    phase_dir = run_dir / "implement"
    phase_dir.mkdir(parents=True)
    otel_lines = [
        {
            "type": "span",
            "name": "tool_call",
            "startTime": [1700000000, 0],
            "attributes": {
                "tool_name": "report_intent",
                "arguments": {"intent": "Running final verification"},
            },
        },
        {
            "type": "span",
            "name": "tool_call",
            "startTime": [1700000001, 0],
            "attributes": {
                "tool_name": "bash",
                "arguments": {"command": "pytest tests/unit -q"},
                "result": {"success": False, "exit_code": 1},
            },
        },
        {
            "type": "span",
            "name": "tool_call",
            "startTime": [1700000002, 0],
            "attributes": {
                "tool_name": "bash",
                "arguments": {"command": "ruff check yamlgraph/"},
                "result": {"success": True, "exit_code": 0},
            },
        },
        {
            "type": "span",
            "name": "tool_call",
            "startTime": [1700000003, 0],
            "attributes": {"tool_name": "create", "arguments": {"path": "a.py"}},
        },
        {
            "type": "span",
            "name": "tool_call",
            "startTime": [1700000004, 0],
            "attributes": {"tool_name": "edit", "arguments": {"path": "a.py"}},
        },
        {
            "type": "span",
            "name": "tool_call",
            "startTime": [1700000005, 0],
            "attributes": {
                "tool_name": "bash",
                "arguments": {"command": "pytest tests/unit -q"},
                "result": {"success": True, "exit_code": 0},
            },
        },
    ]
    (phase_dir / "otel.jsonl").write_text(
        "".join(json.dumps(line) + "\n" for line in otel_lines)
    )
    (phase_dir / "git-diff.patch").write_text("diff --git a/a.py b/a.py\n+pass\n")


@pytest.mark.req("REQ-YG-340")
def test_ac01_runner_includes_required_output_flags_for_both_phases() -> None:
    text = INSTRUMENT_SCRIPT.read_text()
    assert "--output-format" in text
    assert "--output-format json" in text
    assert "--log-dir" in text
    assert "--log-level debug" in text


@pytest.mark.req("REQ-YG-341")
def test_ac02_runner_sets_file_export_and_message_capture_env_vars() -> None:
    text = INSTRUMENT_SCRIPT.read_text()
    assert "COPILOT_OTEL_EXPORTER_TYPE=file" in text
    assert "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true" in text


@pytest.mark.req("REQ-YG-342")
def test_ac03_runner_contract_includes_before_and_after_git_snapshots() -> None:
    text = INSTRUMENT_SCRIPT.read_text()
    assert "git-status-before.txt" in text
    assert "git-diff-before.patch" in text
    assert "git-status-after.txt" in text
    assert "git-diff-after.patch" in text


@pytest.mark.req("REQ-YG-343")
def test_ac04_event_schema_includes_source_success_details(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-364-schema"
    _write_semantic_fixture(run_dir)
    events = _run_extractor(run_dir)
    assert events, "Extractor must emit events for fixture input"
    required = {
        "case_id",
        "phase",
        "event_type",
        "timestamp",
        "summary",
        "source",
        "success",
        "details",
    }
    for event in events:
        missing = required - set(event.keys())
        assert not missing, f"Missing fields {missing} in event {event}"


@pytest.mark.req("REQ-YG-344")
def test_ac05_extracts_phase_marker_from_report_intent_span(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-364-phase-marker"
    _write_semantic_fixture(run_dir)
    events = _run_extractor(run_dir)
    phase_markers = [e for e in events if e.get("event_type") == "phase_marker"]
    assert phase_markers, "Expected phase_marker event from report_intent span"
    assert any(
        marker.get("details", {}).get("intent") == "Running final verification"
        for marker in phase_markers
    )


@pytest.mark.req("REQ-YG-344")
def test_ac05_extracts_test_lint_file_and_failure_retry_semantic_events(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-364-semantic"
    _write_semantic_fixture(run_dir)
    events = _run_extractor(run_dir)
    event_types = {event.get("event_type") for event in events}
    assert "test_run" in event_types
    assert "lint_run" in event_types
    assert "file_create" in event_types
    assert "file_edit" in event_types
    assert "failure" in event_types
    assert "retry" in event_types


@pytest.mark.req("REQ-YG-345")
def test_ac06_conformance_table_output_is_deterministic_for_fixture(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-364-conformance"
    _write_semantic_fixture(run_dir)

    cmd = [sys.executable, str(EXTRACTOR_SCRIPT), str(run_dir), "--conformance-table"]
    first = subprocess.run(cmd, capture_output=True, text=True, check=False)
    second = subprocess.run(cmd, capture_output=True, text=True, check=False)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stdout == second.stdout
    assert "Phase" in first.stdout and "Conformance" in first.stdout


@pytest.mark.req("REQ-YG-346")
def test_ac07_docs_separate_raw_spans_from_normalized_events() -> None:
    text = FINDINGS_DOC.read_text()
    assert "## Raw Telemetry Artifacts" in text
    assert "## Normalized Semantic Events" in text
