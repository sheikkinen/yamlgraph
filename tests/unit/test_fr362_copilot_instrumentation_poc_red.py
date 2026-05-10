"""RED tests for FR-362: Copilot instrumentation process-mining POC.

All tests expected to FAIL before implementation.
Run with: pytest tests/unit/test_fr362_copilot_instrumentation_poc_red.py -q --no-cov
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
INSTRUMENT_SCRIPT = REPO_ROOT / "scripts" / "copilot_instrument.sh"
EXTRACTOR_SCRIPT = REPO_ROOT / "scripts" / "extract_copilot_events.py"
FINDINGS_DOC = REPO_ROOT / "docs" / "copilot-instrumentation-poc.md"


@pytest.mark.req("REQ-YG-105")
def test_instrument_script_exists_and_defines_two_phase_contract():
    """Assert run script exists and documents plan/implement/--resume contract."""
    assert INSTRUMENT_SCRIPT.exists(), f"Missing: {INSTRUMENT_SCRIPT}"
    text = INSTRUMENT_SCRIPT.read_text()
    assert "plan" in text, "Script must contain 'plan' phase label"
    assert "implement" in text, "Script must contain 'implement' phase label"
    assert (
        "--resume" in text
    ), "Script must reference --resume flag for phase continuation"


@pytest.mark.req("REQ-YG-047")
def test_extractor_exists_and_emits_pydantic_valid_events(tmp_path):
    """Assert extractor exists, runs against synthetic fixture, emits valid JSONL events."""
    assert EXTRACTOR_SCRIPT.exists(), f"Missing: {EXTRACTOR_SCRIPT}"

    # Minimal synthetic run fixture
    run_dir = tmp_path / "run-001"
    otel_dir = run_dir / "plan"
    otel_dir.mkdir(parents=True)
    otel_event = {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "name": "copilot.plan",
                                "startTimeUnixNano": "1700000000000000000",
                                "endTimeUnixNano": "1700000001000000000",
                            }
                        ]
                    }
                ]
            }
        ]
    }
    (otel_dir / "otel.jsonl").write_text(json.dumps(otel_event) + "\n")

    # Run extractor
    result = subprocess.run(
        [sys.executable, str(EXTRACTOR_SCRIPT), str(run_dir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Extractor failed:\n{result.stderr}"

    # Parse JSONL output
    events = [json.loads(line) for line in result.stdout.strip().splitlines() if line]
    assert len(events) > 0, "Extractor must emit at least one event"

    required_fields = {"case_id", "phase", "event_type", "timestamp", "summary"}
    for event in events:
        missing = required_fields - set(event.keys())
        assert not missing, f"Event missing fields {missing}: {event}"


@pytest.mark.req("REQ-YG-047")
def test_findings_doc_exists_with_required_sections():
    """Assert findings doc exists and contains required headings."""
    assert FINDINGS_DOC.exists(), f"Missing: {FINDINGS_DOC}"
    text = FINDINGS_DOC.read_text()
    required_headings = [
        "Captured Artifacts",
        "Observed Event Sequence",
        "Candidate Node Types",
        "Next FR",
    ]
    for heading in required_headings:
        assert heading in text, f"Missing required section: '{heading}'"
