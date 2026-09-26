"""FR-1097 AC-13: adapter wrappers name graph rc 3 and keep the artifact verdict.

Each wrapper runs against a stub executor that exits 3 (completed with
errors). With a valid artifact the wrapper passes and reports the rc; without
one it fails with its unchanged contract status.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tests.unit.test_fr758_judge_review_wrappers import JUDGE, REVIEW, _run, _write_stub
from tests.unit.test_fr995_outsider_wrapper import WRAPPER as OUTSIDER
from tests.unit.test_fr995_outsider_wrapper import _fake_bin
from tests.unit.test_fr1028_provider_model_override import (
    CLEAN_BRIEF,
    TOOLS_PY,
    _load_module,
    _run_wrapper,
    _valid_artifact,
)

pytestmark = pytest.mark.process  # runs scripts/*.sh with stub executors (FR-756)

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTHOR = REPO_ROOT / "scripts" / "author.sh"


@pytest.fixture()
def fr_file(tmp_path: Path) -> Path:
    fr = tmp_path / "FR-000-fixture.md"
    fr.write_text("# FR-000 fixture\n", encoding="utf-8")
    return fr


def _stub(tmp_path: Path, body: str) -> Path:
    return _write_stub(tmp_path / "yg-rc3", f"{body}\nexit 3")


# --- judge.sh ---------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
def test_judge_rc3_with_artifact_passes(tmp_path, fr_file):
    stub = _stub(
        tmp_path,
        'mkdir -p "$JUDGE_WORKDIR/tmp"\n'
        'printf "%s\\n" "**Verdict:** APPROVED" '
        '> "$JUDGE_WORKDIR/tmp/draft-judgement-copilot-FR-000-fixture.md"',
    )
    result = _run(JUDGE, [str(fr_file)], tmp_path, stub)
    assert result.returncode == 0, result.stderr
    assert "judge.sh: graph completed with errors (rc=3)" in result.stderr


@pytest.mark.req("REQ-YG-700")
def test_judge_rc3_without_artifact_exits_65(tmp_path, fr_file):
    result = _run(JUDGE, [str(fr_file)], tmp_path, _stub(tmp_path, ":"))
    assert result.returncode == 65
    assert "judge.sh: graph completed with errors (rc=3)" in result.stderr


# --- review.sh --------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
def test_review_rc3_with_artifact_passes(tmp_path, fr_file):
    stub = _stub(
        tmp_path,
        'mkdir -p "$REVIEW_WORKDIR/tmp"\n'
        'printf "%s\\n" "**Merge verdict:** MERGE" > "$REVIEW_WORKDIR/tmp/draft-review.md"',
    )
    result = _run(REVIEW, ["123", str(fr_file)], tmp_path, stub)
    assert result.returncode == 0, result.stderr
    assert "review.sh: graph completed with errors (rc=3)" in result.stderr


@pytest.mark.req("REQ-YG-700")
def test_review_rc3_without_artifact_exits_65(tmp_path, fr_file):
    result = _run(REVIEW, ["123", str(fr_file)], tmp_path, _stub(tmp_path, ":"))
    assert result.returncode == 65
    assert "review.sh: graph completed with errors (rc=3)" in result.stderr


# --- research.sh ------------------------------------------------------------


@pytest.mark.req("REQ-YG-700")
def test_research_rc3_with_artifact_passes(tmp_path):
    tools = _load_module("research_tools_fr1097", TOOLS_PY)
    fixture = _valid_artifact(tools, tmp_path / "valid")
    stub = _stub(
        tmp_path,
        'mkdir -p "$RESEARCH_WORKDIR/tmp"\n'
        f'cp "{fixture}" "$RESEARCH_WORKDIR/tmp/draft-alternatives.md"',
    )
    result = _run_wrapper(tmp_path, stub)
    assert result.returncode == 0, result.stderr
    assert "research.sh: graph completed with errors (rc=3)" in result.stderr


@pytest.mark.req("REQ-YG-700")
def test_research_rc3_without_artifact_exits_65(tmp_path):
    result = _run_wrapper(tmp_path, _stub(tmp_path, ":"))
    assert result.returncode == 65
    assert "research.sh: graph completed with errors (rc=3)" in result.stderr


# --- author.sh --------------------------------------------------------------


def _run_author(tmp_path: Path, stub: Path) -> subprocess.CompletedProcess:
    brief = tmp_path / "brief.md"
    brief.write_text(CLEAN_BRIEF.read_text(encoding="utf-8"), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "AUTHOR_EXECUTION"}
    env["AUTHOR_WORKDIR"] = str(tmp_path)
    env["YAMLGRAPH_BIN"] = str(stub)
    return subprocess.run(
        ["bash", str(AUTHOR), str(brief)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=60,
    )


@pytest.mark.req("REQ-YG-700")
def test_author_rc3_with_artifact_passes(tmp_path):
    (tmp_path / "graphs").mkdir()
    (tmp_path / "graphs" / "made.yaml").write_text("name: made\n", encoding="utf-8")
    report = "\\n".join(
        [
            "## Artifacts",
            "- graphs/made.yaml",
            "## Precedent",
            "## Validation",
            "## Repairs",
            "## Blocked validation",
        ]
    )
    stub = _stub(
        tmp_path,
        'mkdir -p "$AUTHOR_WORKDIR/tmp"\n'
        f'printf "{report}\\n" > "$AUTHOR_WORKDIR/tmp/draft-authoring-report.md"',
    )
    result = _run_author(tmp_path, stub)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "author.sh: graph completed with errors (rc=3)" in result.stderr


@pytest.mark.req("REQ-YG-700")
def test_author_rc3_without_artifact_exits_65(tmp_path):
    result = _run_author(tmp_path, _stub(tmp_path, ":"))
    assert result.returncode == 65
    assert "author.sh: graph completed with errors (rc=3)" in result.stderr


# --- outsider.sh ------------------------------------------------------------


def _run_outsider(tmp_path: Path, *, with_report: bool):
    b = _fake_bin(tmp_path, graph_ok=with_report, comment_ok=True, report_text=VALID)
    yg = b / "yamlgraph"
    yg.write_text(
        yg.read_text(encoding="utf-8").replace("exit 1\n", "exit 3\n", 1) + "exit 3\n"
    )
    work = tmp_path / "work"
    work.mkdir()
    src = tmp_path / "in.md"
    src.write_text("# t\n\nbody", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "OUTSIDER_EXECUTION"}
    env["PATH"] = f"{b}:{env['PATH']}"
    env["OUTSIDER_WORKDIR"] = str(work)
    # Own TMPDIR: the FR-995 leak check globs the shared tempdir for outsider-*/.
    child_tmp = tmp_path / "childtmp"
    child_tmp.mkdir()
    env["TMPDIR"] = str(child_tmp)
    proc = subprocess.run(
        ["bash", str(OUTSIDER), "--input", str(src)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    logs = "".join(
        p.read_text(encoding="utf-8") for p in (work / "tmp").glob("outsider-*.log")
    )
    return proc, logs


VALID = """## 1. In my own words

This change adds a checker.

## 2. Could I decide whether to merge this from the description alone?

YES

It says what changed.

## 3. Words and references I could not understand

nothing

## 4. What a merge decision would still need

- [ ] Test results.
"""


@pytest.mark.req("REQ-YG-700")
def test_outsider_rc3_with_report_passes(tmp_path):
    proc, logs = _run_outsider(tmp_path, with_report=True)
    assert proc.returncode == 0, proc.stderr
    assert "outsider.sh: graph completed with errors (rc=3)" in logs


@pytest.mark.req("REQ-YG-700")
def test_outsider_rc3_without_report_keeps_no_valid_report(tmp_path):
    proc, logs = _run_outsider(tmp_path, with_report=False)
    assert proc.returncode == 1 and "NO VALID REPORT" in proc.stderr
    assert "outsider.sh: graph completed with errors (rc=3)" in logs
