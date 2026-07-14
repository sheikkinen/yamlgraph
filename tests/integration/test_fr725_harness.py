"""FR-725 integration wrapper — run the crosscheck harness on demand.

Slow + key-guarded: generates one fresh run per labeled fixture, then
evaluates all attributable archives. The default (unit) harness path is
LLM-free; this wrapper is the CI-on-demand entry (Judgement pin).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "icpc-2-rfe"

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not (os.getenv("AZURE_AI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")),
        reason="FR-725 harness --runs needs an LLM provider key",
    ),
    pytest.mark.skipif(
        not (EXAMPLE / "data" / "icpc2_rfe_catalog.yaml").exists(),
        reason="generated catalog absent — run build_catalog.py first",
    ),
]


@pytest.mark.req("REQ-YG-554")
def test_harness_end_to_end_one_run():
    proc = subprocess.run(
        [
            sys.executable,
            str(EXAMPLE / "nodes" / "crosscheck.py"),
            "--runs",
            "1",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=900,
    )
    report = json.loads(proc.stdout)
    assert len(report["fixtures"]) == 6
    totals = report["totals"]
    # The harness is advisory (no CI gate per judgement) — the wrapper
    # asserts only that every fixture was scored or loudly skipped.
    assert totals["pass"] + totals["fail"] + totals["skip"] > 0
    for name, entry in report["fixtures"].items():
        assert entry["runs"] > 0, f"{name}: no attributable archives"
