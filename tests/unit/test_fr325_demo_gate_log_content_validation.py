"""Acceptance tests for FR-325 demo-gate log content semantics."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = Path(".github/workflows/commitlint.yml")
PRECOMMIT_SCRIPT_PATH = Path("scripts/check_demo_proof.sh")
SEMANTICS_SCRIPT_PATH = Path("scripts/demo_log_semantics.sh")


def _load_workflow() -> dict:
    with WORKFLOW_PATH.open() as f:
        return yaml.safe_load(f)


def _demo_gate_run_script() -> str:
    workflow = _load_workflow()
    steps = workflow["jobs"]["demo-gate"]["steps"]
    verify_steps = [
        step
        for step in steps
        if "run" in step and "demo" in step.get("name", "").lower()
    ]
    assert verify_steps, "demo-gate must include a verification step"
    return str(verify_steps[0]["run"])


def _setup_git_repo(tmpdir: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)


def _run_precommit_demo_gate(
    staged_files: dict[str, str],
) -> subprocess.CompletedProcess:
    script_abs = str(PRECOMMIT_SCRIPT_PATH.resolve())

    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)
        tmppath = Path(tmpdir)

        (tmppath / "README.md").write_text("init\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmpdir, check=True)

        for relpath, content in staged_files.items():
            fpath = tmppath / relpath
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content)

        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        return subprocess.run(
            ["bash", script_abs],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )


def _run_ci_demo_gate_check(
    changed_files: dict[str, str],
) -> subprocess.CompletedProcess:
    run_script = _demo_gate_run_script()

    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)
        tmppath = Path(tmpdir)

        semantics_dest = tmppath / "scripts" / "demo_log_semantics.sh"
        semantics_dest.parent.mkdir(parents=True, exist_ok=True)
        semantics_dest.write_text(SEMANTICS_SCRIPT_PATH.read_text())
        semantics_dest.chmod(0o755)

        (tmppath / "README.md").write_text("base\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=tmpdir, check=True)
        base_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tmpdir,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        for relpath, content in changed_files.items():
            fpath = tmppath / relpath
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content)
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "head"], cwd=tmpdir, check=True)
        head_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tmpdir,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        env = os.environ.copy()
        env["BASE_SHA"] = base_sha
        env["HEAD_SHA"] = head_sha
        return subprocess.run(
            ["bash", "-lc", run_script],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env=env,
        )


@pytest.mark.req("REQ-YG-200")
class TestFR325DemoGateLogContentValidation:
    def test_ac02_ci_gate_script_contains_fatal_log_markers_check(self) -> None:
        run_script = _demo_gate_run_script()
        semantics = SEMANTICS_SCRIPT_PATH.read_text()

        assert (
            "source scripts/demo_log_semantics.sh" in run_script
        ), "CI demo-gate must source shared semantic validation rules"
        assert (
            "validate_demo_output_log_file" in run_script
        ), "CI demo-gate must validate demo-output.log contents"
        assert "Node .+ failed" in semantics
        assert "\\[ERROR\\]" in semantics
        assert "❌ Error:" in semantics
        assert "exit code [1-9]" in semantics

    def test_ac03_ci_gate_script_rejects_empty_or_no_success_log(self) -> None:
        empty_result = _run_ci_demo_gate_check(
            {
                "examples/demos/hello/graph.yaml": "nodes: {}\n",
                "examples/demos/hello/demo-output.log": " \n\t\n",
            }
        )
        assert empty_result.returncode == 1
        assert "empty" in (empty_result.stdout + empty_result.stderr).lower()

        no_success_result = _run_ci_demo_gate_check(
            {
                "examples/demos/hello/graph.yaml": "nodes: {}\n",
                "examples/demos/hello/demo-output.log": "started run\nstill running\n",
            }
        )
        assert no_success_result.returncode == 1
        assert (
            "success evidence"
            in (no_success_result.stdout + no_success_result.stderr).lower()
        )

    def test_ac04_precommit_script_rejects_failed_demo_log(self) -> None:
        result = _run_precommit_demo_gate(
            {
                "examples/demos/hello/graph.yaml": "nodes: {}\n",
                "examples/demos/hello/demo-output.log": "[ERROR] yamlgraph.error_handlers: Node greet failed: boom\n",
            }
        )
        assert result.returncode == 1
        assert "fatal execution marker" in (result.stdout + result.stderr).lower()

    def test_ac04_precommit_script_rejects_empty_demo_log(self) -> None:
        result = _run_precommit_demo_gate(
            {
                "examples/demos/hello/graph.yaml": "nodes: {}\n",
                "examples/demos/hello/demo-output.log": "\n  \t\n",
            }
        )
        assert result.returncode == 1
        assert "empty" in (result.stdout + result.stderr).lower()

    def test_ac04_precommit_script_accepts_successful_demo_log(self) -> None:
        result = _run_precommit_demo_gate(
            {
                "examples/demos/hello/graph.yaml": "nodes: {}\n",
                "examples/demos/hello/demo-output.log": (
                    "2026-01-01 00:00:00 [INFO] yamlgraph.node_factory.llm_nodes: "
                    "Node greet completed successfully\n"
                    "✓ Graph execution completed successfully\n"
                ),
            }
        )
        assert result.returncode == 0, result.stdout

    def test_ac04_precommit_and_ci_share_same_semantic_rules(self) -> None:
        run_script = _demo_gate_run_script()
        precommit_script = PRECOMMIT_SCRIPT_PATH.read_text()
        semantics = SEMANTICS_SCRIPT_PATH.read_text()

        assert "source scripts/demo_log_semantics.sh" in run_script
        assert "demo_log_semantics.sh" in precommit_script
        assert "DEMO_LOG_FATAL_MARKERS=" in semantics
        assert "DEMO_LOG_SUCCESS_MARKERS=" in semantics
