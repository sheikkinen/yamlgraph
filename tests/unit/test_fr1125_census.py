"""FR-1125 AC-08 — the committed open-object ledger reproduces from the tree.

``scripts/fr1125_open_object_census.py`` is deterministic (PROVIDER env
ignored). The committed ledger's mechanical section must equal the script's
current output, and after the FR-1125 migration no static-Anthropic node may
still carry an open object.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "fr1125_open_object_census.py"
LEDGER = ROOT / "docs" / "issues-2026-09-27-fr1125-census.md"

pytestmark = pytest.mark.process


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    import os

    env = {k: v for k, v in os.environ.items() if k != "PROVIDER"}
    env["PYTHONUTF8"] = "1"
    return subprocess.run(  # noqa: S603  # CONF-FR1125: test drives the repository's own script
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        env=env,
        check=False,
    )


@pytest.mark.req("REQ-YG-712")
def test_ac08_ledger_matches_current_tree() -> None:
    proc = _run("--check", str(LEDGER))
    assert proc.returncode == 0, proc.stderr + proc.stdout


@pytest.mark.req("REQ-YG-712")
def test_ac08_no_static_anthropic_open_object_remains() -> None:
    proc = _run()
    assert proc.returncode == 0, proc.stderr
    summary = re.search(
        r"Rows: (\d+) — anthropic (\d+), runtime (\d+), other (\d+), error (\d+)",
        proc.stdout,
    )
    assert summary, proc.stdout[-400:]
    rows, anthropic, _runtime, _other, error = map(int, summary.groups())
    assert rows > 0, (
        "an empty census means the walk found nothing, not that all is well"
    )
    assert error == 0
    assert anthropic == 0, f"{anthropic} static-Anthropic open-object rows remain"
