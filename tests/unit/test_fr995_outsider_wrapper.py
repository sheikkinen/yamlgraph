"""FR-995 outsider wrapper — static contracts and the recursion sentinel (REQ-YG-663).

No model calls. The wrapper's cwd inversion, grants, cleanup and comment
gating are asserted on the script and adapter text; the sentinel is
exercised for real because it exits before any run.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / ".github/skills/outsider-view"
WRAPPER = REPO / "scripts/outsider.sh"

pytestmark = (
    pytest.mark.process
)  # reads scripts/ and runs the wrapper's sentinel path (FR-756)


@pytest.fixture(scope="module")
def script() -> str:
    return WRAPPER.read_text(encoding="utf-8")


@pytest.mark.req("REQ-YG-663")
def test_adapter_pins_model_and_grants_no_access():
    text = (SKILL / "adapters/graph.yaml").read_text(encoding="utf-8")
    node = yaml.safe_load(text)["nodes"]["outsider"]
    assert node["type"] == "copilot" and node["cli_flags"]["model"] == "gpt-5.6-sol"
    assert "allow_all" not in text


@pytest.mark.req("REQ-YG-663")
def test_child_cwd_is_a_fresh_temp_dir_outside_repo(script: str):
    # The child directory is created under the system temp root, never under the repo.
    assert re.search(
        r'CHILD_CWD="\$\(mktemp -d "\$\{TMPDIR:-/tmp\}/outsider-XXXXXX"\)"', script
    )
    temp_root = Path(tempfile.gettempdir()).resolve()
    assert not str(temp_root).startswith(str(REPO.resolve()))
    assert not (temp_root / ".github").exists()
    # The graph is launched from inside that directory with absolute paths.
    assert re.search(
        r'\( cd "\$CHILD_CWD" && OUTSIDER_EXECUTION=1 "\$\{YG\[@\]\}" graph run "\$GRAPH"',
        script,
    )
    assert 'GRAPH="$SKILL/adapters/graph.yaml"' in script
    assert 'REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"' in script


@pytest.mark.req("REQ-YG-663")
def test_cleanup_and_temp_input_removal(script: str):
    assert "trap cleanup EXIT INT TERM" in script
    assert 'cleanup() { rm -rf "$CHILD_CWD"; rm -rf "$LOCK"; }' in script
    run_idx = script.index('graph run "$GRAPH"')
    rm_idx = script.index('rm -f "$CHILD_CWD/input.md"')
    verify_idx = script.index("Verify by artifact and contract")
    assert run_idx < rm_idx < verify_idx


@pytest.mark.req("REQ-YG-663")
def test_comment_is_opt_in_and_only_path_to_gh_pr_comment(script: str):
    assert "COMMENT=0" in script
    calls = [m.start() for m in re.finditer(r"gh pr comment", script)]
    assert len(calls) == 1
    guard = script[: calls[0]].rstrip().splitlines()[-1]
    assert 'if [ "$COMMENT" -eq 1 ]' in guard


@pytest.mark.req("REQ-YG-663")
def test_no_dry_run_mode(script: str):
    assert "dry-run" not in script and "dry_run" not in script


@pytest.mark.req("REQ-YG-663")
def test_ledger_only_in_pr_mode(script: str):
    assert script.count('mode="pr"') == 1
    assert "no ledger row for --input" in script


@pytest.mark.req("REQ-YG-663")
def test_recursion_sentinel_rejected_before_any_run():
    proc = subprocess.run(
        ["bash", str(WRAPPER), "--selftest"],
        capture_output=True,
        text=True,
        env={**os.environ, "OUTSIDER_EXECUTION": "1"},
        check=False,
    )
    assert proc.returncode == 70 and "inside an outsider execution" in proc.stderr
