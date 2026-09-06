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


# --- FR-1022 round sentinel (REQ-YG-668) --------------------------------------

SENTINEL_LINE = (
    "**Verdict:** REJECTED — Operator: Rethink and rewrite the FR. "
    "It's getting too complicated as a planning document."
)


@pytest.fixture()
def marker_stub(tmp_path: Path) -> Path:
    """Executor stub that leaves a marker so its absence proves no run (C-7)."""
    return _write_stub(
        tmp_path / "yg-marker",
        'mkdir -p "$JUDGE_WORKDIR/tmp"\n'
        'touch "$JUDGE_WORKDIR/tmp/executor-ran"\n'
        'printf "%s\\n" "**Verdict:** APPROVED" '
        '> "$JUDGE_WORKDIR/tmp/draft-judgement-copilot-FR-000-fixture.md"',
    )


def _judgement(fr_file: Path, verdicts: int, *, rounds: bool = False) -> Path:
    path = fr_file.with_suffix(".judgement.md")
    parts = ["# Judgement: FR-000 fixture\n"]
    for i in range(verdicts):
        if rounds and i:
            parts.append(f"# Round {i + 1}\n")
        parts.append("**Verdict:** APPROVED WITH REVISIONS — round text\n")
    path.write_text("".join(parts), encoding="utf-8")
    return path


def _assert_sentinel_untouched(tmp_path: Path, backend: str = "copilot") -> None:
    assert not (tmp_path / "tmp" / "executor-ran").exists()
    assert not (tmp_path / "tmp" / ".judge.lock").exists()
    assert not (
        tmp_path / "tmp" / f"draft-judgement-{backend}-FR-000-fixture.md"
    ).exists()


@pytest.mark.req("REQ-YG-668")
def test_judge_round_1_runs_graph(tmp_path, fr_file, marker_stub):
    result = _run(JUDGE, [str(fr_file)], tmp_path, marker_stub)
    assert result.returncode == 0
    assert (tmp_path / "tmp" / "executor-ran").exists()
    assert "round 1" in result.stderr


@pytest.mark.req("REQ-YG-668")
def test_judge_round_2_runs_graph(tmp_path, fr_file, marker_stub):
    _judgement(fr_file, 1)
    result = _run(JUDGE, [str(fr_file)], tmp_path, marker_stub)
    assert result.returncode == 0
    assert (tmp_path / "tmp" / "executor-ran").exists()
    assert "round 2" in result.stderr


@pytest.mark.req("REQ-YG-668")
def test_judge_round_3_is_fixed_verdict_exit_77(tmp_path, fr_file, marker_stub):
    _judgement(fr_file, 2)
    result = _run(JUDGE, [str(fr_file)], tmp_path, marker_stub)
    assert result.returncode == 77
    assert not (tmp_path / "tmp" / "executor-ran").exists()
    assert not (tmp_path / "tmp" / ".judge.lock").exists()
    artifact = tmp_path / "tmp" / "draft-judgement-copilot-FR-000-fixture.md"
    assert artifact.read_text(encoding="utf-8") == SENTINEL_LINE + "\n"
    assert "round 3" in result.stderr


@pytest.mark.req("REQ-YG-668")
def test_judge_four_verdicts_with_round_headings_exit_77(
    tmp_path, fr_file, marker_stub
):
    _judgement(fr_file, 4, rounds=True)
    result = _run(JUDGE, [str(fr_file)], tmp_path, marker_stub)
    assert result.returncode == 77
    assert not (tmp_path / "tmp" / "executor-ran").exists()
    assert not (tmp_path / "tmp" / ".judge.lock").exists()
    artifact = tmp_path / "tmp" / "draft-judgement-copilot-FR-000-fixture.md"
    assert artifact.read_text(encoding="utf-8") == SENTINEL_LINE + "\n"


@pytest.mark.req("REQ-YG-668")
def test_judge_sentinel_applies_to_claude_backend(tmp_path, fr_file, marker_stub):
    _judgement(fr_file, 2)
    result = _run(
        JUDGE, [str(fr_file)], tmp_path, marker_stub, {"JUDGE_BACKEND": "claude"}
    )
    assert result.returncode == 77
    assert not (tmp_path / "tmp" / "executor-ran").exists()
    artifact = tmp_path / "tmp" / "draft-judgement-claude-FR-000-fixture.md"
    assert artifact.read_text(encoding="utf-8") == SENTINEL_LINE + "\n"


@pytest.mark.req("REQ-YG-668")
def test_judge_invalid_backend_wins_over_sentinel(tmp_path, fr_file, marker_stub):
    _judgement(fr_file, 2)
    result = _run(
        JUDGE, [str(fr_file)], tmp_path, marker_stub, {"JUDGE_BACKEND": "bogus"}
    )
    assert result.returncode == 64
    _assert_sentinel_untouched(tmp_path)
    _assert_sentinel_untouched(tmp_path, "bogus")


@pytest.mark.req("REQ-YG-668")
def test_judge_reentry_guard_wins_over_sentinel(tmp_path, fr_file, marker_stub):
    _judgement(fr_file, 2)
    result = _run(
        JUDGE, [str(fr_file)], tmp_path, marker_stub, {"JUDGE_EXECUTION": "1"}
    )
    assert result.returncode == 70
    _assert_sentinel_untouched(tmp_path)


@pytest.mark.req("REQ-YG-668")
def test_judge_unanchored_verdict_token_not_counted(tmp_path, fr_file, marker_stub):
    path = fr_file.with_suffix(".judgement.md")
    path.write_text(
        "# Judgement\n"
        "**Verdict:** APPROVED WITH REVISIONS\n"
        "The prior draft said **Verdict:** SPLIT, quoted here in prose.\n"
        "> **Verdict:** REJECTED — quoted from the old round\n",
        encoding="utf-8",
    )
    result = _run(JUDGE, [str(fr_file)], tmp_path, marker_stub)
    assert result.returncode == 0
    assert (tmp_path / "tmp" / "executor-ran").exists()
    assert "round 2" in result.stderr


@pytest.mark.req("REQ-YG-668")
def test_judge_no_force_bypass(tmp_path, fr_file, marker_stub):
    _judgement(fr_file, 2)
    result = _run(
        JUDGE, [str(fr_file), "--force"], tmp_path, marker_stub, {"JUDGE_FORCE": "1"}
    )
    assert result.returncode == 77
    assert not (tmp_path / "tmp" / "executor-ran").exists()
    artifact = tmp_path / "tmp" / "draft-judgement-copilot-FR-000-fixture.md"
    assert artifact.read_text(encoding="utf-8") == SENTINEL_LINE + "\n"


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
