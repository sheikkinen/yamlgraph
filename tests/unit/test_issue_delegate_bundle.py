"""Offline tests for the FR-949 issue-delegate bundle beyond models/worker core.

Covers the canonical workflow shape (delegate.yml), control-side submit.sh
refusals and exact submission argv (AC-06), sync-worker.sh deterministic
deployment (AC-03), worker.py CLI dispatch used by the workflow and
submit.sh, and the static windows_job.ps1 contract markers (AC-11; live
witness is AC-17). No network, no real gh, no host mutation (AC-15).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLE = REPO_ROOT / ".github" / "skills" / "issue-delegate"

BUNDLE_FILES = [
    "delegate.yml",
    "models.py",
    "worker.py",
    "windows_job.ps1",
    "sync-worker.sh",
    "submit.sh",
]

DEPLOY_MAP = {
    "delegate.yml": ".github/workflows/delegate.yml",
    "models.py": ".github/delegate/models.py",
    "worker.py": ".github/delegate/worker.py",
    "windows_job.ps1": ".github/delegate/windows_job.ps1",
}

COMMS_REPO = "sheikkinen/yamlgraph-delegation"


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        b"blob %d\x00" % len(data) + data, usedforsecurity=False
    ).hexdigest()


# ---------------------------------------------------------------------------
# delegate.yml — canonical workflow shape
# ---------------------------------------------------------------------------


def _load_workflow() -> dict:
    wf = yaml.safe_load((BUNDLE / "delegate.yml").read_text())
    return wf


def _job(wf: dict) -> dict:
    jobs = wf["jobs"]
    assert len(jobs) == 1, "one delegation job"
    return next(iter(jobs.values()))


@pytest.mark.req("REQ-YG-637")
def test_workflow_trigger_is_issue_labeled_only():
    wf = _load_workflow()
    on = wf.get("on", wf.get(True))
    assert on == {"issues": {"types": ["labeled"]}}


@pytest.mark.req("REQ-YG-637")
def test_workflow_permissions_minimal():
    wf = _load_workflow()
    assert wf["permissions"] == {"contents": "read", "issues": "write"}


@pytest.mark.req("REQ-YG-637")
def test_workflow_outer_timeout_thirty_minutes():
    assert _job(_load_workflow())["timeout-minutes"] == 30


@pytest.mark.req("REQ-YG-637")
def test_workflow_single_flight_concurrency():
    wf = _load_workflow()
    conc = wf["concurrency"]
    assert conc["cancel-in-progress"] is False
    assert conc["group"]


@pytest.mark.req("REQ-YG-637")
def test_workflow_runs_on_windows_service_labels():
    labels = _job(_load_workflow())["runs-on"]
    assert "self-hosted" in labels
    assert "Windows" in labels
    assert "delegate" in labels


@pytest.mark.req("REQ-YG-637")
def test_workflow_authorization_gate_before_any_mutation():
    """Job-level if: label + committed allowlist, recursion identities excluded."""
    gate = _job(_load_workflow())["if"]
    assert "github.event.label.name == 'delegate'" in gate
    assert "sheikkinen" in gate  # committed allowlist
    assert "github-actions" in gate  # excluded identity
    assert "huutokauppakone-svc" in gate  # worker service identity excluded


@pytest.mark.req("REQ-YG-637")
def test_workflow_target_checkout_credential_isolation():
    steps = _job(_load_workflow())["steps"]
    checkout = next(s for s in steps if s.get("id") == "checkout-target")
    with_ = checkout["with"]
    assert with_["persist-credentials"] is False
    assert "DELEGATE_CHECKOUT_PAT" in str(with_["token"])
    assert with_["path"] == "target"


@pytest.mark.req("REQ-YG-637")
def test_workflow_payload_env_marks_delegated():
    steps = _job(_load_workflow())["steps"]
    payload = next(s for s in steps if s.get("id") == "payload")
    assert str(payload["env"]["YAMLGRAPH_DELEGATED"]) == "1"


@pytest.mark.req("REQ-YG-637")
def test_workflow_step_ordering_matches_lifecycle():
    """claim → validate → checkout → preflight → payload → resolve → comments → terminal."""
    ids = [s.get("id") for s in _job(_load_workflow())["steps"] if s.get("id")]
    expected = [
        "claim",
        "validate",
        "checkout-target",
        "credential-preflight",
        "payload",
        "resolve",
        "publish-comments",
        "terminal-mutation",
    ]
    positions = [ids.index(e) for e in expected]
    assert positions == sorted(positions), f"lifecycle order violated: {ids}"


@pytest.mark.req("REQ-YG-637")
def test_workflow_resolve_runs_unconditionally():
    steps = _job(_load_workflow())["steps"]
    resolve = next(s for s in steps if s.get("id") == "resolve")
    assert "always()" in str(resolve["if"])


# ---------------------------------------------------------------------------
# windows_job.ps1 — static contract (live witness: AC-17)
# ---------------------------------------------------------------------------


def _ps1() -> str:
    return (BUNDLE / "windows_job.ps1").read_text()


@pytest.mark.req("REQ-YG-637")
def test_windows_job_inner_deadline_default_1500():
    assert re.search(r"\$DeadlineSeconds\s*=\s*1500", _ps1())


@pytest.mark.req("REQ-YG-637")
def test_windows_job_object_markers():
    text = _ps1()
    for marker in [
        "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
        "CREATE_SUSPENDED",
        "AssignProcessToJobObject",
        "ResumeThread",
        "TerminateJobObject",
    ]:
        assert marker in text, f"missing Job Object marker: {marker}"


@pytest.mark.req("REQ-YG-637")
def test_windows_job_records_pids_and_cleans_up_unconditionally():
    text = _ps1()
    assert "finally" in text
    assert "descendant" in text.lower()
    assert "surviving_pids" in text
    assert "inner_deadline_fired" in text


# ---------------------------------------------------------------------------
# worker.py CLI — the same entrypoints the workflow steps call
# ---------------------------------------------------------------------------


def _run_worker(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BUNDLE / "worker.py"), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


@pytest.mark.req("REQ-YG-637")
def test_worker_cli_validate_payload_ok():
    res = _run_worker("validate-payload", "judge", "feature-requests/FR-1-x.md")
    assert res.returncode == 0, res.stderr


@pytest.mark.req("REQ-YG-637")
def test_worker_cli_validate_payload_refused():
    res = _run_worker("validate-payload", "judge", "../etc/passwd")
    assert res.returncode == 1
    assert "refused" in res.stderr or "payload" in res.stderr


@pytest.mark.req("REQ-YG-637")
def test_worker_cli_parse_issue_emits_request_fields(tmp_path):
    body = (
        "please judge\n\n```yaml\n"
        "schema_version: 1\n"
        "task: judge\n"
        "sha: " + "a" * 40 + "\n"
        "payload: feature-requests/FR-1-x.md\n"
        "```\n"
    )
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"issue": {"body": body}}))
    res = _run_worker("parse-issue", str(event))
    assert res.returncode == 0, res.stderr
    fields = dict(line.split("=", 1) for line in res.stdout.splitlines() if "=" in line)
    assert fields["task"] == "judge"
    assert fields["repo"] == "sheikkinen/yamlgraph"
    assert fields["sha"] == "a" * 40
    assert fields["payload"] == "feature-requests/FR-1-x.md"
    assert fields["max_reported_credits"] == "60"


@pytest.mark.req("REQ-YG-637")
def test_worker_cli_parse_issue_invalid_body_fails_typed(tmp_path):
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"issue": {"body": "no yaml block here"}}))
    res = _run_worker("parse-issue", str(event))
    assert res.returncode == 1
    assert "INVALID_REQUEST" in res.stderr


# ---------------------------------------------------------------------------
# sync-worker.sh — deterministic deployment to frozen comms paths (AC-03)
# ---------------------------------------------------------------------------


def _run_sync(dest: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(BUNDLE / "sync-worker.sh"), str(dest)],
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.req("REQ-YG-637")
def test_sync_deploys_frozen_paths_byte_identical(tmp_path):
    dest = tmp_path / "comms"
    dest.mkdir()
    res = _run_sync(dest)
    assert res.returncode == 0, res.stderr
    for src_name, deployed in DEPLOY_MAP.items():
        src_bytes = (BUNDLE / src_name).read_bytes()
        assert (dest / deployed).read_bytes() == src_bytes, deployed


@pytest.mark.req("REQ-YG-637")
def test_sync_copies_only_enumerated_worker_files(tmp_path):
    """Control-side files (submit.sh, SKILL.md) and credentials never deploy."""
    dest = tmp_path / "comms"
    dest.mkdir()
    _run_sync(dest)
    deployed = sorted(str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file())
    assert deployed == sorted(DEPLOY_MAP.values())


@pytest.mark.req("REQ-YG-637")
def test_sync_refuses_missing_dest(tmp_path):
    res = _run_sync(tmp_path / "does-not-exist")
    assert res.returncode != 0


# ---------------------------------------------------------------------------
# submit.sh — control-side refusals + exact submission argv (AC-06)
# ---------------------------------------------------------------------------

FAKE_GH = """#!/usr/bin/env bash
{
  for a in gh "$@"; do printf '%s\\x00' "$a"; done
  printf '\\x1e'
} >> "$GH_LOG"
cmd="${1:-}"
if [ "$cmd" = api ]; then
  path="$2"
  case "$path" in
    */actions/runners) cat "$GH_RUNNERS_JSON" ;;
    */contents/*)
      rel="${path#*contents/}"
      key="${rel//\\//__}"
      cat "$GH_CONTENTS_DIR/$key.json"
      ;;
  esac
elif [ "$cmd" = issue ]; then
  echo "https://github.com/sheikkinen/yamlgraph-delegation/issues/99"
fi
"""

RUNNERS_ONLINE = {
    "runners": [
        {
            "name": "huutokauppakone",
            "status": "online",
            "labels": [
                {"name": "self-hosted"},
                {"name": "Windows"},
                {"name": "delegate"},
            ],
        }
    ]
}

RUNNERS_OFFLINE = {
    "runners": [
        {
            "name": "huutokauppakone",
            "status": "offline",
            "labels": [{"name": "delegate"}],
        }
    ]
}


class SubmitFixture:
    def __init__(self, tmp_path: Path):
        self.tmp = tmp_path
        self.origin = tmp_path / "origin.git"
        self.work = tmp_path / "work"
        self.bin = tmp_path / "bin"
        self.gh_log = tmp_path / "gh.log"
        self.contents_dir = tmp_path / "contents"
        self.runners_json = tmp_path / "runners.json"
        self._build()

    def _git(self, *args: str, cwd: Path | None = None) -> None:
        subprocess.run(
            ["git", *args],
            cwd=cwd or self.work,
            check=True,
            capture_output=True,
            env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null"},
        )

    def _build(self) -> None:
        subprocess.run(
            ["git", "init", "--bare", str(self.origin)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.origin), "symbolic-ref", "HEAD", "refs/heads/main"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "clone", str(self.origin), str(self.work)],
            check=True,
            capture_output=True,
        )
        self._git("symbolic-ref", "HEAD", "refs/heads/main")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "test")
        bundle_dst = self.work / ".github" / "skills" / "issue-delegate"
        bundle_dst.mkdir(parents=True)
        for name in BUNDLE_FILES:
            bundle_dst.joinpath(name).write_bytes((BUNDLE / name).read_bytes())
        fr_dir = self.work / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-000-sample.md").write_text("# FR-000 sample\n")
        self._git("add", "-A")
        self._git("commit", "-m", "fixture")
        self._git("push", "-u", "origin", "main")
        # fake gh
        self.bin.mkdir()
        gh = self.bin / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        # runner + no-drift contents responses
        self.runners_json.write_text(json.dumps(RUNNERS_ONLINE))
        self.contents_dir.mkdir()
        self.write_contents(drift=False)

    def write_contents(self, *, drift: bool) -> None:
        for src_name, deployed in DEPLOY_MAP.items():
            data = (BUNDLE / src_name).read_bytes()
            sha = _git_blob_sha(data)
            if drift and src_name == "worker.py":
                sha = "0" * 40
            key = deployed.replace("/", "__")
            (self.contents_dir / f"{key}.json").write_text(json.dumps({"sha": sha}))

    @property
    def head(self) -> str:
        res = subprocess.run(
            ["git", "-C", str(self.work), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    def run_submit(self, *args: str, env_extra: dict | None = None):
        env = os.environ.copy()
        env.pop("YAMLGRAPH_DELEGATED", None)
        venv_bin = str(Path(sys.executable).parent)
        env["PATH"] = f"{self.bin}:{venv_bin}:{env['PATH']}"
        env["GH_LOG"] = str(self.gh_log)
        env["GH_RUNNERS_JSON"] = str(self.runners_json)
        env["GH_CONTENTS_DIR"] = str(self.contents_dir)
        env["GIT_CONFIG_GLOBAL"] = "/dev/null"
        if env_extra:
            env.update(env_extra)
        submit = self.work / ".github" / "skills" / "issue-delegate" / "submit.sh"
        return subprocess.run(
            ["bash", str(submit), *args],
            cwd=self.work,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def gh_invocations(self) -> list[list[str]]:
        if not self.gh_log.exists():
            return []
        raw = self.gh_log.read_text()
        return [record.split("\x00")[:-1] for record in raw.split("\x1e") if record]


@pytest.fixture(scope="module")
def submit_fix(tmp_path_factory):
    return SubmitFixture(tmp_path_factory.mktemp("submit"))


JUDGE_ARGS = ("--task", "judge", "--payload", "feature-requests/FR-000-sample.md")


@pytest.mark.req("REQ-YG-637")
def test_submit_refuses_recursion_env(submit_fix):
    res = submit_fix.run_submit(*JUDGE_ARGS, env_extra={"YAMLGRAPH_DELEGATED": "1"})
    assert res.returncode == 3
    assert "delegat" in res.stderr.lower()


@pytest.mark.req("REQ-YG-637")
def test_submit_refuses_unknown_task(submit_fix):
    res = submit_fix.run_submit("--task", "deploy", "--payload", "x.md")
    assert res.returncode == 2
    assert res.stderr


@pytest.mark.req("REQ-YG-637")
def test_submit_refuses_invalid_payload_same_normalizer(submit_fix):
    res = submit_fix.run_submit("--task", "judge", "--payload", "../evil.md")
    assert res.returncode == 6
    assert res.stderr


@pytest.mark.req("REQ-YG-637")
def test_submit_refuses_uncommitted_payload(submit_fix):
    res = submit_fix.run_submit(
        "--task", "judge", "--payload", "feature-requests/FR-999-ghost.md"
    )
    assert res.returncode == 6


@pytest.mark.req("REQ-YG-637")
def test_submit_refuses_dirty_tree(submit_fix):
    marker = submit_fix.work / "feature-requests" / "FR-000-sample.md"
    original = marker.read_text()
    marker.write_text(original + "dirty\n")
    try:
        res = submit_fix.run_submit(*JUDGE_ARGS)
        assert res.returncode == 4
        assert "dirty" in res.stderr.lower() or "clean" in res.stderr.lower()
    finally:
        marker.write_text(original)


@pytest.mark.req("REQ-YG-637")
def test_submit_refuses_unpushed_head(submit_fix):
    (submit_fix.work / "unpushed.md").write_text("x\n")
    submit_fix._git("add", "unpushed.md")
    submit_fix._git("commit", "-m", "unpushed")
    try:
        res = submit_fix.run_submit(*JUDGE_ARGS)
        assert res.returncode == 5
        assert "push" in res.stderr.lower()
    finally:
        submit_fix._git("reset", "--hard", "origin/main")


@pytest.mark.req("REQ-YG-637")
def test_submit_refuses_runner_offline(submit_fix):
    submit_fix.runners_json.write_text(json.dumps(RUNNERS_OFFLINE))
    try:
        res = submit_fix.run_submit(*JUDGE_ARGS)
        assert res.returncode == 7
        assert "runner" in res.stderr.lower()
    finally:
        submit_fix.runners_json.write_text(json.dumps(RUNNERS_ONLINE))


@pytest.mark.req("REQ-YG-637")
def test_submit_refuses_bundle_drift(submit_fix):
    submit_fix.write_contents(drift=True)
    try:
        res = submit_fix.run_submit(*JUDGE_ARGS)
        assert res.returncode == 8
        assert "drift" in res.stderr.lower()
    finally:
        submit_fix.write_contents(drift=False)


@pytest.mark.req("REQ-YG-637")
def test_check_worker_reports_and_never_submits(submit_fix):
    submit_fix.gh_log.unlink(missing_ok=True)
    res = submit_fix.run_submit("--check-worker")
    assert res.returncode == 0, res.stderr
    for invocation in submit_fix.gh_invocations():
        assert invocation[1:3] != ["issue", "create"]


@pytest.mark.req("REQ-YG-637")
def test_submit_happy_path_exact_argv(submit_fix):
    submit_fix.gh_log.unlink(missing_ok=True)
    res = submit_fix.run_submit(*JUDGE_ARGS)
    assert res.returncode == 0, res.stderr
    assert "issues/99" in res.stdout
    creates = [
        inv for inv in submit_fix.gh_invocations() if inv[1:3] == ["issue", "create"]
    ]
    assert len(creates) == 1
    body = (
        "Delegation request (FR-949).\n"
        "\n"
        "```yaml\n"
        "schema_version: 1\n"
        "task: judge\n"
        "repo: sheikkinen/yamlgraph\n"
        f"sha: {submit_fix.head}\n"
        "payload: feature-requests/FR-000-sample.md\n"
        "max_reported_credits: 60\n"
        "```\n"
    )
    assert creates[0] == [
        "gh",
        "issue",
        "create",
        "--repo",
        COMMS_REPO,
        "--title",
        "delegate: judge feature-requests/FR-000-sample.md",
        "--label",
        "delegate",
        "--body",
        body,
    ]


@pytest.mark.req("REQ-YG-637")
def test_submit_repo_override_lands_in_body(submit_fix):
    submit_fix.gh_log.unlink(missing_ok=True)
    res = submit_fix.run_submit(*JUDGE_ARGS, "--repo", "sheikkinen/other-repo")
    assert res.returncode == 0, res.stderr
    creates = [
        inv for inv in submit_fix.gh_invocations() if inv[1:3] == ["issue", "create"]
    ]
    assert "repo: sheikkinen/other-repo\n" in creates[0][-1]
