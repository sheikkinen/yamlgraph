"""FR-995 outsider wrapper — behavioural contracts (REQ-YG-663).

No real model calls: `yamlgraph` and `gh` are replaced by fakes on PATH.
The ledger is redirected to a temp file via OUTSIDER_LEDGER.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / ".github/skills/outsider-view"
WRAPPER = REPO / "scripts/outsider.sh"
PY = Path(sys.executable)  # CI has no .venv; use the interpreter running the tests

pytestmark = pytest.mark.process  # runs scripts/outsider.sh with fakes on PATH (FR-756)

VALID_REPORT = """## 1. In my own words

This change adds a checker.

## 2. Could I decide whether to merge this from the description alone?

YES

It says what changed.

## 3. Words and references I could not understand

nothing

## 4. What a merge decision would still need

- [ ] Test results.
"""


@pytest.fixture(scope="module")
def script() -> str:
    return WRAPPER.read_text(encoding="utf-8")


def _fake_bin(tmp: Path, *, graph_ok: bool, comment_ok: bool, report_text: str) -> Path:
    """Fake `yamlgraph` (runs the real finalize tool on canned model text) and fake `gh`."""
    b = tmp / "bin"
    b.mkdir(parents=True)
    model_out = tmp / "model_output.md"
    model_out.write_text(report_text, encoding="utf-8")
    tools = SKILL / "adapters/outsider_tools.py"
    yg = b / "yamlgraph"
    yg.write_text(
        "#!/usr/bin/env bash\n"
        + ("exit 1\n" if not graph_ok else "")
        + 'for a in "$@"; do case "$a" in report_path=*) R="${a#report_path=}";; input_path=*) I="${a#input_path=}";; esac; done\n'
        + f'"{PY}" - "$R" "$I" <<\'EOF\'\n'
        "import importlib.util, sys\n"
        f'spec = importlib.util.spec_from_file_location("ot", "{tools}"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n'
        f'out = open("{model_out}").read()\n'
        'm.finalize_report({"outsider_result": {"output": out}, "report_path": sys.argv[1], "model": "fake", "input_path": sys.argv[2]})\n'
        "EOF\n",
        encoding="utf-8",
    )
    sha = "a" * 40
    gh = b / "gh"
    gh.write_text(
        "#!/usr/bin/env bash\n"
        f'if [ "$1" = pr ] && [ "$2" = view ]; then echo \'{{"title":"T","body":"B body","headRefOid":"{sha}"}}\'; exit 0; fi\n'
        f'if [ "$1" = pr ] && [ "$2" = comment ]; then echo posted >> "{tmp}/comments"; exit {0 if comment_ok else 1}; fi\n'
        "exit 2\n",
        encoding="utf-8",
    )
    for f in (yg, gh):
        f.chmod(f.stat().st_mode | stat.S_IXUSR)
    return b


def _run(
    tmp: Path,
    *args: str,
    graph_ok: bool = True,
    comment_ok: bool = True,
    report_text: str = VALID_REPORT,
):
    b = _fake_bin(
        tmp, graph_ok=graph_ok, comment_ok=comment_ok, report_text=report_text
    )
    work = tmp / "work"
    work.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "OUTSIDER_EXECUTION"}
    env["PATH"] = f"{b}:{env['PATH']}"
    env["OUTSIDER_WORKDIR"] = str(work)
    env["OUTSIDER_LEDGER"] = str(tmp / "ledger.jsonl")
    proc = subprocess.run(
        ["bash", str(WRAPPER), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    ledger = tmp / "ledger.jsonl"
    rows = (
        [json.loads(ln) for ln in ledger.read_text().splitlines() if ln.strip()]
        if ledger.exists()
        else []
    )
    return proc, rows, work


@pytest.mark.req("REQ-YG-663")
def test_adapter_pins_model_and_grants_no_access():
    text = (SKILL / "adapters/graph.yaml").read_text(encoding="utf-8")
    node = yaml.safe_load(text)["nodes"]["outsider"]
    assert node["type"] == "copilot" and node["cli_flags"]["model"] == "gpt-5.6-sol"
    assert "allow_all" not in text


@pytest.mark.req("REQ-YG-663")
def test_doctrine_within_sixty_lines():
    assert len((SKILL / "doctrine.md").read_text(encoding="utf-8").splitlines()) <= 60


@pytest.mark.req("REQ-YG-663")
def test_wrapper_is_executable_in_the_index():
    # FR-889 lock strips disk perms on main; the committed mode is the contract
    mode = subprocess.run(
        ["git", "ls-files", "-s", "scripts/outsider.sh"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()[0]
    assert (
        mode == "100755"
    ), f"scripts/outsider.sh committed as {mode}; ./scripts/outsider.sh would fail"


@pytest.mark.req("REQ-YG-663")
def test_child_cwd_is_a_fresh_temp_dir_outside_repo(script: str):
    assert re.search(
        r'CHILD_CWD="\$\(mktemp -d "\$\{TMPDIR:-/tmp\}/outsider-XXXXXX"\)"', script
    )
    assert not str(Path(tempfile.gettempdir()).resolve()).startswith(
        str(REPO.resolve())
    )
    assert re.search(
        r'\( cd "\$CHILD_CWD" && OUTSIDER_EXECUTION=1 "\$\{YG\[@\]\}" graph run "\$GRAPH"',
        script,
    )


@pytest.mark.req("REQ-YG-663")
def test_losing_process_leaves_the_lock_intact(tmp_path: Path):
    work = tmp_path / "work"
    (work / "tmp/.outsider.lock").mkdir(parents=True)
    (work / "tmp/.outsider.lock/holder").write_text("pid=1 started=now")
    env = {k: v for k, v in os.environ.items() if k != "OUTSIDER_EXECUTION"}
    env["OUTSIDER_WORKDIR"] = str(work)
    proc = subprocess.run(
        ["bash", str(WRAPPER), "--selftest"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 73
    assert (work / "tmp/.outsider.lock/holder").read_text() == "pid=1 started=now"


@pytest.mark.req("REQ-YG-663")
def test_input_mode_success_writes_report_and_no_ledger(tmp_path: Path):
    src = tmp_path / "in.md"
    src.write_text("# t\n\nbody", encoding="utf-8")
    proc, rows, work = _run(tmp_path, "--input", str(src), "--label", "t")
    assert proc.returncode == 0, proc.stderr
    reports = list((work / "tmp").glob("outsider-t-*.md"))
    assert len(reports) == 1 and reports[0].read_text().startswith(
        "**Derived verdict:** YES"
    )
    assert rows == []
    assert not list(Path(tempfile.gettempdir()).glob("outsider-*/input.md"))


@pytest.mark.req("REQ-YG-663")
def test_pr_mode_success_writes_one_attributable_row(tmp_path: Path):
    proc, rows, work = _run(tmp_path, "4242", "--comment")
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "comments").exists()
    assert len(rows) == 1
    row = rows[0]
    assert (
        row["pr"] == 4242
        and row["head_sha"] == "a" * 40
        and row["derived_verdict"] == "YES"
    )
    assert not Path(row["report_path"]).is_absolute()
    # fetched PR text lived only in the child directory, which is gone
    assert not list(Path(tempfile.gettempdir()).glob("outsider-*/pr-4242.md"))
    assert not list((work / "tmp").glob("*input*"))


@pytest.mark.req("REQ-YG-663")
def test_graph_failure_and_parse_failure_fail_closed(tmp_path: Path):
    src = tmp_path / "in.md"
    src.write_text("# t\n\nbody", encoding="utf-8")
    p1, rows1, _ = _run(tmp_path / "a", "--input", str(src), graph_ok=False)
    assert p1.returncode == 1 and "NO VALID REPORT" in p1.stderr and rows1 == []
    p2, rows2, _ = _run(
        tmp_path / "b",
        "4242",
        "--comment",
        report_text="## 1. In my own words\n\nonly one section\n",
    )
    assert p2.returncode == 1 and "NO VALID REPORT" in p2.stderr and rows2 == []
    assert not (tmp_path / "b" / "comments").exists()


@pytest.mark.req("REQ-YG-663")
def test_comment_failure_writes_no_ledger_row(tmp_path: Path):
    proc, rows, _ = _run(tmp_path, "4242", "--comment", comment_ok=False)
    assert proc.returncode == 1 and "no ledger row written" in proc.stderr
    assert rows == []


@pytest.mark.req("REQ-YG-663")
def test_comment_is_opt_in_and_only_path_to_gh_pr_comment(script: str):
    assert "COMMENT=0" in script
    calls = [m.start() for m in re.finditer(r"gh pr comment", script)]
    assert len(calls) == 1
    guard = script[: calls[0]].rstrip().splitlines()[-1]
    assert 'if [ "$COMMENT" -eq 1 ]' in guard
    assert "dry-run" not in script


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
