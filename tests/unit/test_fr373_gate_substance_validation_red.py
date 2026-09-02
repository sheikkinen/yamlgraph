"""Acceptance tests for FR-373 gate substance validation."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

WORKFLOW_PATH = Path(".github/workflows/commitlint.yml")
SEMANTICS_SCRIPT_PATH = Path("scripts/gate_artifact_semantics.sh")
CAP_50_PATH = Path("capabilities/CAP-50-ci-changelog-gate.yaml")
CAP_54_PATH = Path("capabilities/CAP-54-ci-diary-existence-gate.yaml")
ARCHITECTURE_PATH = Path("ARCHITECTURE.md")


def _load_workflow() -> dict:
    with WORKFLOW_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _gate_run_script(job_name: str, step_name_substring: str) -> str:
    steps = _load_workflow()["jobs"][job_name]["steps"]
    verify_steps = [
        step
        for step in steps
        if "run" in step and step_name_substring in step.get("name", "").lower()
    ]
    assert verify_steps, f"{job_name} must include a '{step_name_substring}' step"
    return str(verify_steps[0]["run"])


def _setup_git_repo(tmpdir: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)


def _run_gate(
    *,
    job_name: str,
    step_name_substring: str,
    changed_files: dict[str, str],
    pr_title: str = "feat(ci): FR-373 enforce gate substance checks",
) -> subprocess.CompletedProcess:
    run_script = _gate_run_script(job_name, step_name_substring)

    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)
        tmppath = Path(tmpdir)

        semantics_dest = tmppath / "scripts" / "gate_artifact_semantics.sh"
        semantics_dest.parent.mkdir(parents=True, exist_ok=True)
        semantics_dest.write_text(SEMANTICS_SCRIPT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        semantics_dest.chmod(0o755)

        (tmppath / "README.md").write_text("base\n", encoding="utf-8")
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
            fpath.write_text(content, encoding="utf-8")
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
        env["PR_TITLE"] = pr_title
        env["PATH"] = "/usr/bin:/bin"
        return subprocess.run(
            ["bash", "-lc", run_script],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env=env,
        )


def _valid_diary_body() -> str:
    return (
        "# Reflection FR-373\n\n"
        "## Trap\n"
        "Presence-only checks caused compliance theatre in CI gates.\n\n"
        "## Heuristic\n"
        "Check semantic structure and minimum content before passing a merge gate.\n\n"
        "## Seed\n"
        "Seed: Should gate-semantic checks be standardized across all CI contracts?\n"
    )


@pytest.mark.req("REQ-YG-148")
def test_ac01_changelog_gate_rejects_empty_fragment_content() -> None:
    result = _run_gate(
        job_name="changelog-gate",
        step_name_substring="changelog fragment",
        changed_files={"changelog/unreleased/fr-373-empty.md": " \n\t\n"},
    )
    assert result.returncode == 1
    assert "empty" in (result.stdout + result.stderr).lower()


@pytest.mark.req("REQ-YG-148")
def test_ac02_changelog_gate_rejects_missing_type_or_body_list_item() -> None:
    missing_type = _run_gate(
        job_name="changelog-gate",
        step_name_substring="changelog fragment",
        changed_files={
            "changelog/unreleased/fr-373-no-type.md": (
                "---\nscope: ci\n---\n- body item exists\n"
            )
        },
    )
    assert missing_type.returncode == 1
    assert "type" in (missing_type.stdout + missing_type.stderr).lower()

    missing_body_list = _run_gate(
        job_name="changelog-gate",
        step_name_substring="changelog fragment",
        changed_files={
            "changelog/unreleased/fr-373-no-list.md": (
                "---\ntype: feat\nscope: ci\n---\nbody line without markdown bullet\n"
            )
        },
    )
    assert missing_body_list.returncode == 1
    assert "list item" in (missing_body_list.stdout + missing_body_list.stderr).lower()


@pytest.mark.req("REQ-YG-148")
def test_ac03_changelog_gate_accepts_valid_fragment_structure() -> None:
    result = _run_gate(
        job_name="changelog-gate",
        step_name_substring="changelog fragment",
        changed_files={
            "changelog/unreleased/fr-373-valid.md": (
                "---\ntype: feat\nscope: ci\n---\n"
                "- **FR-373**: Added changelog/diary substance validation.\n"
            )
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.req("REQ-YG-152")
def test_ac04_diary_gate_rejects_missing_header_seed_or_min_size() -> None:
    missing_header = _run_gate(
        job_name="diary-gate",
        step_name_substring="diary reflection",
        changed_files={
            "docs/diary/2026-05-13-reflection-fr-373.md": (
                "No markdown header present. " * 8 + "Seed: present\n"
            )
        },
    )
    assert missing_header.returncode == 1
    assert "## header" in (missing_header.stdout + missing_header.stderr)

    missing_seed = _run_gate(
        job_name="diary-gate",
        step_name_substring="diary reflection",
        changed_files={
            "docs/diary/2026-05-13-reflection-fr-373.md": (
                "## Trap\n" + ("Long enough content line.\n" * 12)
            )
        },
    )
    assert missing_seed.returncode == 1
    assert "seed:" in (missing_seed.stdout + missing_seed.stderr).lower()

    too_small = _run_gate(
        job_name="diary-gate",
        step_name_substring="diary reflection",
        changed_files={
            "docs/diary/2026-05-13-reflection-fr-373.md": "## Trap\nSeed: x\n"
        },
    )
    assert too_small.returncode == 1
    assert ">100 bytes" in (too_small.stdout + too_small.stderr)


@pytest.mark.req("REQ-YG-152")
def test_ac05_diary_gate_accepts_valid_reflection_structure() -> None:
    result = _run_gate(
        job_name="diary-gate",
        step_name_substring="diary reflection",
        changed_files={
            "docs/diary/2026-05-13-reflection-fr-373.md": _valid_diary_body()
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.req("REQ-YG-148", "REQ-YG-152")
def test_ac06_commitlint_gate_scripts_source_shared_semantics_module() -> None:
    changelog_script = _gate_run_script("changelog-gate", "changelog fragment")
    diary_script = _gate_run_script("diary-gate", "diary reflection")
    semantics = SEMANTICS_SCRIPT_PATH.read_text(encoding="utf-8")

    assert "source scripts/gate_artifact_semantics.sh" in changelog_script
    assert "source scripts/gate_artifact_semantics.sh" in diary_script
    assert "validate_changelog_fragment_file" in changelog_script
    assert "validate_diary_reflection_file" in diary_script
    assert "validate_changelog_fragment_file()" in semantics
    assert "validate_diary_reflection_file()" in semantics


@pytest.mark.req("REQ-YG-148", "REQ-YG-152")
def test_ac07_reqyg148_and_reqyg152_text_mentions_substance_validation() -> None:
    cap_50 = CAP_50_PATH.read_text(encoding="utf-8").lower()
    cap_54 = CAP_54_PATH.read_text(encoding="utf-8").lower()
    architecture = ARCHITECTURE_PATH.read_text(encoding="utf-8").lower()

    assert "substance" in cap_50
    assert "front matter" in cap_50
    assert "substance" in cap_54
    assert "seed:" in cap_54
    assert "req-yg-148" in architecture and "substance" in architecture
    assert "req-yg-152" in architecture and "seed:" in architecture
