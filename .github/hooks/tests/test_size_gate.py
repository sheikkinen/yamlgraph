#!/usr/bin/env python3
"""FR-889 AC-11: widened file-size gate covers enforcement infrastructure.

The gate errors above 450 lines for yamlgraph/, scripts/, .github/ and
*.sh files; pre-existing oversize files are held by a shrink-only
baseline ratchet (they may never grow), never silently exempted.

Infrastructure test scope (FR-436): outside REQ-YG marker coverage.

Run:  pytest .github/hooks/tests/test_size_gate.py -q --no-cov
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SIZE_GATE = REPO_ROOT / "scripts" / "size_gate.py"
pytestmark = pytest.mark.req("REQ-YG-527")


def run_gate(root: Path):
    return subprocess.run(
        [sys.executable, str(SIZE_GATE), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def _mk(root: Path, rel: str, lines: int):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# filler\n" * lines)


def test_oversize_hook_script_fails(tmp_path):
    _mk(tmp_path, ".github/hooks/scripts/big.sh", 500)
    r = run_gate(tmp_path)
    assert r.returncode == 1
    assert "big.sh" in r.stdout


def test_oversize_scripts_py_fails(tmp_path):
    _mk(tmp_path, "scripts/big.py", 460)
    assert run_gate(tmp_path).returncode == 1


def test_within_limit_passes(tmp_path):
    _mk(tmp_path, ".github/hooks/scripts/small.sh", 100)
    _mk(tmp_path, "scripts/small.py", 100)
    _mk(tmp_path, "yamlgraph/small.py", 100)
    assert run_gate(tmp_path).returncode == 0


def test_repo_passes_the_widened_gate():
    r = run_gate(REPO_ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_baseline_is_shrink_only_and_honest():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import size_gate  # noqa: PLC0415

    for rel, allowed in size_gate.BASELINE.items():
        p = REPO_ROOT / rel
        assert p.is_file(), f"stale baseline entry: {rel}"
        actual = len(p.read_text().splitlines())
        assert actual <= allowed, f"{rel} grew past its ratchet ({actual} > {allowed})"
        assert actual > size_gate.LIMIT or allowed >= actual
