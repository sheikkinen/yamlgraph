"""FR-758: contract tests for the sole-route judge/review wrappers.

Witnesses the ported csap NC-415/NC-413 wrappers (scripts/judge.sh,
scripts/review.sh) with a stubbed YAMLGRAPH_BIN — no API keys, no real
graph execution (judgement C-2). Exit-code taxonomy per REQ-YG-569.
"""

from __future__ import annotations

import os
import stat
import subprocess
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
JUDGE = REPO_ROOT / "scripts" / "judge.sh"
REVIEW = REPO_ROOT / "scripts" / "review.sh"


def _write_stub(path: Path, body: str) -> Path:
    """Write an executable stub standing in for the yamlgraph CLI."""
    path.write_text(f"#!/usr/bin/env bash\n{body}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _run(
    script: Path,
    args: list[str],
    workdir: Path,
    stub: Path | None,
    extra_env: dict | None = None,
):
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("JUDGE_EXECUTION", "REVIEW_EXECUTION", "YAMLGRAPH_BIN")
    }
    var = "JUDGE_WORKDIR" if script is JUDGE else "REVIEW_WORKDIR"
    env[var] = str(workdir)
    if stub is not None:
        env["YAMLGRAPH_BIN"] = str(stub)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.fixture()
def fr_file(tmp_path: Path) -> Path:
    fr = tmp_path / "FR-000-fixture.md"
    fr.write_text("# FR-000 fixture\n", encoding="utf-8")
    return fr


@pytest.fixture()
def judge_ok_stub(tmp_path: Path) -> Path:
    return _write_stub(
        tmp_path / "yg-ok",
        'mkdir -p "$JUDGE_WORKDIR/tmp"\n'
        # FR-960: the wrapper names the draft per backend and per FR.
        'printf "%s\\n" "**Verdict:** APPROVED" '
        '> "$JUDGE_WORKDIR/tmp/draft-judgement-copilot-FR-000-fixture.md"',
    )


@pytest.fixture()
def review_ok_stub(tmp_path: Path) -> Path:
    return _write_stub(
        tmp_path / "yg-ok",
        'mkdir -p "$REVIEW_WORKDIR/tmp"\n'
        'printf "%s\\n" "**Merge verdict:** MERGE" > "$REVIEW_WORKDIR/tmp/draft-review.md"',
    )


# --- usage / missing FR ---------------------------------------------------


@pytest.mark.req("REQ-YG-569")
def test_judge_usage_exit_64(tmp_path):
    assert _run(JUDGE, [], tmp_path, None).returncode == 64


@pytest.mark.req("REQ-YG-569")
def test_review_usage_exit_64(tmp_path):
    assert _run(REVIEW, ["123"], tmp_path, None).returncode == 64


@pytest.mark.req("REQ-YG-569")
def test_judge_missing_fr_exit_66(tmp_path):
    assert _run(JUDGE, [str(tmp_path / "nope.md")], tmp_path, None).returncode == 66


@pytest.mark.req("REQ-YG-569")
def test_review_missing_fr_exit_66(tmp_path):
    assert (
        _run(REVIEW, ["123", str(tmp_path / "nope.md")], tmp_path, None).returncode
        == 66
    )


# --- lineage sentinel re-entry guard (NC-414) ------------------------------


@pytest.mark.req("REQ-YG-569")
def test_judge_sentinel_exit_70(tmp_path, fr_file):
    result = _run(JUDGE, [str(fr_file)], tmp_path, None, {"JUDGE_EXECUTION": "1"})
    assert result.returncode == 70
    assert "do not re-invoke" in result.stderr


@pytest.mark.req("REQ-YG-569")
def test_review_sentinel_exit_70(tmp_path, fr_file):
    result = _run(
        REVIEW, ["123", str(fr_file)], tmp_path, None, {"REVIEW_EXECUTION": "1"}
    )
    assert result.returncode == 70
    assert "do not re-invoke" in result.stderr


# --- lock protocol ----------------------------------------------------------


@pytest.mark.req("REQ-YG-569")
def test_judge_fresh_lock_exit_73_prints_holder(tmp_path, fr_file):
    lock = tmp_path / "tmp" / ".judge.lock"
    lock.mkdir(parents=True)
    (lock / "holder").write_text(
        "pid=99999 started=2026-07-24T00:00:00Z\n", encoding="utf-8"
    )
    result = _run(JUDGE, [str(fr_file)], tmp_path, None)
    assert result.returncode == 73
    assert "pid=99999" in result.stderr
    assert lock.is_dir(), "fresh lock must not be removed"


@pytest.mark.req("REQ-YG-569")
def test_judge_stale_lock_exit_75_never_auto_removed(tmp_path, fr_file):
    lock = tmp_path / "tmp" / ".judge.lock"
    lock.mkdir(parents=True)
    stale = time.time() - 11 * 60
    os.utime(lock, (stale, stale))
    result = _run(JUDGE, [str(fr_file)], tmp_path, None)
    assert result.returncode == 75
    assert "stale lock" in result.stderr
    assert lock.is_dir(), "stale lock is inspected by a human, never auto-removed"


@pytest.mark.req("REQ-YG-569")
def test_review_fresh_lock_exit_73(tmp_path, fr_file):
    lock = tmp_path / "tmp" / ".review.lock"
    lock.mkdir(parents=True)
    assert _run(REVIEW, ["123", str(fr_file)], tmp_path, None).returncode == 73


@pytest.mark.req("REQ-YG-569")
def test_judge_lock_removed_after_run(tmp_path, fr_file, judge_ok_stub):
    result = _run(JUDGE, [str(fr_file)], tmp_path, judge_ok_stub)
    assert result.returncode == 0
    assert not (tmp_path / "tmp" / ".judge.lock").exists()


@pytest.mark.req("REQ-YG-569")
def test_judge_lock_removed_after_contract_failure(tmp_path, fr_file):
    stub = _write_stub(tmp_path / "yg-noop", "exit 0")
    result = _run(JUDGE, [str(fr_file)], tmp_path, stub)
    assert result.returncode == 65
    assert not (tmp_path / "tmp" / ".judge.lock").exists()


# --- executor resolution ------------------------------------------------------


@pytest.mark.req("REQ-YG-569")
def test_judge_no_executor_exit_69(tmp_path, fr_file):
    # Core utils only — no yamlgraph, no uv (hermetic per judgement C-3).
    result = _run(JUDGE, [str(fr_file)], tmp_path, None, {"PATH": "/usr/bin:/bin"})
    assert result.returncode == 69
    assert "no yamlgraph executor found" in result.stderr


@pytest.mark.req("REQ-YG-569")
def test_judge_yamlgraph_bin_takes_precedence_over_path(
    tmp_path, fr_file, judge_ok_stub
):
    decoy_dir = tmp_path / "decoy"
    decoy_dir.mkdir()
    _write_stub(decoy_dir / "yamlgraph", "echo DECOY RAN >&2; exit 1")
    env_path = f"{decoy_dir}:{os.environ['PATH']}"
    result = _run(JUDGE, [str(fr_file)], tmp_path, judge_ok_stub, {"PATH": env_path})
    assert result.returncode == 0
    assert "DECOY RAN" not in result.stderr


# --- artifact contract (verify by artifact, never exit code) -----------------


@pytest.mark.req("REQ-YG-569")
def test_judge_missing_artifact_exit_65_despite_rc0(tmp_path, fr_file):
    stub = _write_stub(tmp_path / "yg-silent", "exit 0")
    result = _run(JUDGE, [str(fr_file)], tmp_path, stub)
    assert result.returncode == 65
    assert "missing or empty" in result.stderr


@pytest.mark.req("REQ-YG-569")
def test_judge_artifact_without_verdict_line_exit_65(tmp_path, fr_file):
    stub = _write_stub(
        tmp_path / "yg-noverdict",
        'mkdir -p "$JUDGE_WORKDIR/tmp"\n'
        'echo "prose, no verdict" '
        '> "$JUDGE_WORKDIR/tmp/draft-judgement-copilot-FR-000-fixture.md"',
    )
    result = _run(JUDGE, [str(fr_file)], tmp_path, stub)
    assert result.returncode == 65
    assert "no verdict line" in result.stderr


@pytest.mark.req("REQ-YG-569")
def test_review_merge_verdict_not_line_one_exit_65(tmp_path, fr_file):
    stub = _write_stub(
        tmp_path / "yg-buried",
        'mkdir -p "$REVIEW_WORKDIR/tmp"\n'
        'printf "preamble\\n**Merge verdict:** MERGE\\n" > "$REVIEW_WORKDIR/tmp/draft-review.md"',
    )
    result = _run(REVIEW, ["123", str(fr_file)], tmp_path, stub)
    assert result.returncode == 65
    assert "LINE ONE" in result.stderr


@pytest.mark.req("REQ-YG-569")
def test_judge_conforming_artifact_exit_0(tmp_path, fr_file, judge_ok_stub):
    result = _run(JUDGE, [str(fr_file)], tmp_path, judge_ok_stub)
    assert result.returncode == 0
    assert "advisory until human-reviewed" in result.stdout


@pytest.mark.req("REQ-YG-569")
def test_review_conforming_artifact_exit_0(tmp_path, fr_file, review_ok_stub):
    result = _run(REVIEW, ["123", str(fr_file)], tmp_path, review_ok_stub)
    assert result.returncode == 0
    assert "advisory until the human merge decision" in result.stdout
