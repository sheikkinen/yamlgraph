"""FR-860 RED: contract tests for scripts/req_audit.sh (REQ-YG-609).

The runner is exercised against a skeleton repo with stubbed `pytest` /
`yamlgraph` executables and fake constructor/report scripts, so the
tests assert the script's *contract* (command construction, fail-fast,
provenance manifest, FR-850 refusal propagation) without recording real
coverage or calling a model. The provenance-header test runs the real
scripts/req_audit_report.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "req_audit.sh"

MANIFEST_KEYS = {
    "git_sha",
    "git_dirty",
    "output_dir",
    "skip_record",
    "pytest_command",
    "coverage_core",
    "recorded_context_count",
    "tagged_test_count",
    "skip_count",
    "python_version",
    "coverage_version",
    "provider",
    "model",
    "phases",
}

FAKE_COVERAGE_CONTEXTS = """\
import os


class CoverageContextError(RuntimeError):
    pass


def load_coverage_contexts(root, tagged=None):
    if os.environ.get("FAKE_POISON"):
        raise CoverageContextError(
            "poisoned coverage DB; remedy: record with COVERAGE_CORE=ctrace "
            "pytest --cov-context=test, sequential (no -n)"
        )
    return {}, {"ctx-1", "ctx-2", "ctx-3"}
"""

FAKE_REQ_COVERAGE = """\
FRAMEWORK_TEST_DIRS = []


def extract_req_markers(filepath):
    return {}
"""

FAKE_QUESTIONS = """\
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coverage_contexts import CoverageContextError, load_coverage_contexts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("tmp/req-audit"))
    args = parser.parse_args()
    fail = os.environ.get("FAKE_CONSTRUCT_FAIL")
    if fail:
        print("constructor failure injected", file=sys.stderr)
        sys.exit(int(fail))
    try:
        load_coverage_contexts(Path("."), None)
    except CoverageContextError as exc:
        print(exc, file=sys.stderr)
        sys.exit(2)
    batches = args.out / "batches"
    batches.mkdir(parents=True, exist_ok=True)
    (batches / "batch-000.json").write_text("[]\\n")
    (args.out / "manifest.json").write_text(
        json.dumps({"batch-000": ["REQ-YG-001"]}) + "\\n"
    )
    print("1 questions, 1 batches")


if __name__ == "__main__":
    main()
"""

FAKE_REPORT = """\
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--run-manifest", type=Path, default=None)
    args = parser.parse_args()
    Path("calls-report.txt").write_text(
        f"--model {args.model} --provider {args.provider} "
        f"--run-manifest {args.run_manifest}\\n"
    )
    (args.audit_dir / "report.md").write_text(
        f"# Requirement Witness Audit\\n- Model: {args.model} ({args.provider})\\n"
    )


if __name__ == "__main__":
    main()
"""

STUB_PYTEST = """\
#!/usr/bin/env bash
printf 'COVERAGE_CORE=%s ARGS=%s\\n' "${COVERAGE_CORE:-}" "$*" > calls-pytest.txt
touch .coverage
echo "5 passed, 2 skipped in 0.1s"
"""

STUB_YAMLGRAPH = """\
#!/usr/bin/env bash
printf 'ARGS=%s\\n' "$*" > calls-yamlgraph.txt
"""


@pytest.fixture()
def skeleton(tmp_path: Path) -> Path:
    """Mini repo: git history, fake pipeline scripts, stubbed executables."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "seed",
        ],
        cwd=tmp_path,
        check=True,
    )
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "coverage_contexts.py").write_text(FAKE_COVERAGE_CONTEXTS)
    (scripts / "req_coverage.py").write_text(FAKE_REQ_COVERAGE)
    (scripts / "req_audit_questions.py").write_text(FAKE_QUESTIONS)
    (scripts / "req_audit_report.py").write_text(FAKE_REPORT)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("pytest", STUB_PYTEST), ("yamlgraph", STUB_YAMLGRAPH)):
        stub = bin_dir / name
        stub.write_text(body)
        stub.chmod(0o755)
    return tmp_path


def run_script(cwd: Path, *args: str, env_extra: dict | None = None):
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(
        [str(cwd / "bin"), str(Path(sys.executable).parent), env["PATH"]]
    )
    env.pop("COVERAGE_CORE", None)
    env.update(env_extra or {})
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_happy_path_runs_all_phases_and_writes_logs(skeleton):
    """AC-01: four phases in order, one log each, report produced."""
    r = run_script(skeleton, "--out", "out")
    assert r.returncode == 0, r.stdout + r.stderr
    out = skeleton / "out"
    for phase in ("record", "construct", "audit", "report"):
        assert (out / f"{phase}.log").exists(), f"missing {phase}.log"
    assert (out / "report.md").exists()
    assert (skeleton / "calls-yamlgraph.txt").exists()


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_record_command_is_exact_full_suite_instrument(skeleton):
    """AC-03: honest instrument — ctrace, sequential, no mark exclusions."""
    r = run_script(skeleton, "--out", "out")
    assert r.returncode == 0, r.stdout + r.stderr
    calls = (skeleton / "calls-pytest.txt").read_text()
    assert "COVERAGE_CORE=ctrace" in calls
    assert (
        "tests/unit tests/integration -q --no-cov-report "
        "--cov=yamlgraph --cov-context=test" in calls
    )
    assert " -n" not in calls
    assert " -m " not in calls


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_help_documents_cli(skeleton):
    """AC-02: --help names every supported flag."""
    r = run_script(skeleton, "--help")
    assert r.returncode == 0
    for flag in ("--out", "--skip-record", "--model", "--provider"):
        assert flag in r.stdout, f"--help missing {flag}"


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_default_model_provider_recorded_and_passed(skeleton):
    """AC-02/AC-05: frozen defaults reach both manifest and report phase."""
    r = run_script(skeleton, "--out", "out")
    assert r.returncode == 0, r.stdout + r.stderr
    manifest = json.loads((skeleton / "out" / "run-manifest.json").read_text())
    assert manifest["model"] == "claude-haiku-4-5"
    assert manifest["provider"] == "anthropic"
    calls = (skeleton / "calls-report.txt").read_text()
    assert "--model claude-haiku-4-5" in calls
    assert "--provider anthropic" in calls


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_explicit_model_provider_flags(skeleton):
    """AC-02: flags override defaults; the manifest records what ran."""
    r = run_script(skeleton, "--out", "out", "--model", "m-x", "--provider", "p-y")
    assert r.returncode == 0, r.stdout + r.stderr
    manifest = json.loads((skeleton / "out" / "run-manifest.json").read_text())
    assert manifest["model"] == "m-x"
    assert manifest["provider"] == "p-y"
    calls = (skeleton / "calls-report.txt").read_text()
    assert "--model m-x" in calls and "--provider p-y" in calls


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_fail_fast_stops_pipeline_and_blocks_report(skeleton):
    """AC-01: first failed phase ends the run; no report, later phases unrun."""
    r = run_script(skeleton, "--out", "out", env_extra={"FAKE_CONSTRUCT_FAIL": "3"})
    assert r.returncode != 0
    out = skeleton / "out"
    assert not (out / "report.md").exists()
    assert not (skeleton / "calls-yamlgraph.txt").exists()
    manifest = json.loads((out / "run-manifest.json").read_text())
    assert manifest["phases"]["construct"]["exit_code"] == 3


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_skip_record_reuses_coverage_without_pytest(skeleton):
    """AC-04: --skip-record never invokes pytest; manifest records the state."""
    (skeleton / ".coverage").touch()
    r = run_script(skeleton, "--out", "out", "--skip-record")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (skeleton / "calls-pytest.txt").exists()
    manifest = json.loads((skeleton / "out" / "run-manifest.json").read_text())
    assert manifest["skip_record"] is True


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_skip_record_poisoned_coverage_hard_refusal(skeleton):
    """AC-04: FR-850 refusal propagates — non-zero, remedy printed, no report."""
    (skeleton / ".coverage").touch()
    r = run_script(
        skeleton, "--out", "out", "--skip-record", env_extra={"FAKE_POISON": "1"}
    )
    assert r.returncode != 0
    combined = r.stdout + r.stderr
    if not any(
        "ctrace" in text
        for text in (
            combined,
            *(p.read_text() for p in (skeleton / "out").glob("*.log") if p.is_file()),
        )
    ):
        pytest.fail("boundary remedy (ctrace) not surfaced")
    assert not (skeleton / "out" / "report.md").exists()


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_run_manifest_frozen_schema(skeleton):
    """AC-05: run-manifest.json carries exactly the frozen key set."""
    r = run_script(skeleton, "--out", "out")
    assert r.returncode == 0, r.stdout + r.stderr
    manifest = json.loads((skeleton / "out" / "run-manifest.json").read_text())
    assert set(manifest) == MANIFEST_KEYS
    assert len(manifest["git_sha"]) == 40
    assert isinstance(manifest["git_dirty"], bool)
    assert manifest["coverage_core"] == "ctrace"
    assert manifest["pytest_command"].startswith("COVERAGE_CORE=ctrace pytest ")
    assert isinstance(manifest["recorded_context_count"], int)
    assert isinstance(manifest["tagged_test_count"], int)
    assert manifest["skip_count"] == 2  # stub pytest reports "2 skipped"
    for phase in ("record", "construct", "audit", "report"):
        entry = manifest["phases"][phase]
        assert set(entry) == {"command", "exit_code", "log"}
        assert entry["exit_code"] == 0


@pytest.mark.req("REQ-YG-609")
@pytest.mark.process
def test_report_header_embeds_provenance(tmp_path):
    """AC-06: the real report script embeds run-manifest provenance."""
    audit_dir = tmp_path / "out"
    (audit_dir / "raw").mkdir(parents=True)
    (audit_dir / "manifest.json").write_text("{}\n")
    sha = "ab12" * 10
    run_manifest = {
        "git_sha": sha,
        "git_dirty": True,
        "recorded_context_count": 3446,
        "tagged_test_count": 4123,
        "provider": "anthropic",
        "model": "claude-haiku-4-5",
    }
    (audit_dir / "run-manifest.json").write_text(json.dumps(run_manifest))
    r = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "req_audit_report.py"),
            "--audit-dir",
            str(audit_dir),
            "--run-manifest",
            str(audit_dir / "run-manifest.json"),
            "--model",
            "claude-haiku-4-5",
            "--provider",
            "anthropic",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    header = (audit_dir / "report.md").read_text()
    assert sha in header
    assert "DIRTY" in header
    assert "3446" in header and "4123" in header
    assert "claude-haiku-4-5" in header and "anthropic" in header
