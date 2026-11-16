"""FR-1167: release.sh prepares a release-branch commit; tagging moves after squash merge.

Witnesses (REQ-YG-190):
  - release.sh executes no tag creation; its printed handoff names the
    branch push -> PR -> squash merge -> squash SHA -> tag -> single-tag push
  - release.sh refuses to run on main, leaving files, HEAD, index and tags unchanged
  - checklist and skill document the same ordered route, with no push --tags
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "release.sh"
CHECKLIST = REPO_ROOT / "reference" / "release-checklist.md"
SKILL = REPO_ROOT / ".github" / "skills" / "release-version" / "SKILL.md"

HANDOFF_ORDER = (
    "git push -u origin",
    "gh pr create",
    "--squash",
    "mergeCommit",
    "git tag v",
    "git push origin v",
)


def _executed_lines(script: str) -> list[str]:
    """Shell lines that run commands: drop comments and echo/printf output text."""
    lines = []
    for raw in script.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("echo ", "printf ", 'echo"', "cat <<")):
            continue
        lines.append(line)
    return lines


def _printed_text(script: str) -> str:
    return "\n".join(
        raw.strip()
        for raw in script.splitlines()
        if raw.strip().startswith(("echo ", "printf "))
    )


def _assert_ordered(text: str, needles: tuple[str, ...], where: str) -> None:
    pos = -1
    for needle in needles:
        found = text.find(needle, pos + 1)
        assert found > pos, f"{where}: '{needle}' missing or out of order"
        pos = found


@pytest.mark.req("REQ-YG-190")
def test_release_script_executes_no_tag_creation() -> None:
    executed = _executed_lines(SCRIPT.read_text(encoding="utf-8"))
    assert not [line for line in executed if "git tag" in line]
    assert any("commit -F" in line for line in executed)


@pytest.mark.req("REQ-YG-190")
def test_release_script_prints_ordered_handoff_with_checklist_pointer() -> None:
    printed = _printed_text(SCRIPT.read_text(encoding="utf-8"))
    _assert_ordered(printed, HANDOFF_ORDER, "release.sh handoff")
    assert "reference/release-checklist.md" in printed


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


def _snapshot(repo: Path) -> tuple[str, str, str, str, str]:
    files = "\n".join(
        f"{p.relative_to(repo)}:{p.read_bytes()!r}"
        for p in sorted(repo.rglob("*"))
        if p.is_file() and ".git" not in p.parts
    )
    return (
        files,
        _git(repo, "rev-parse", "HEAD"),
        _git(repo, "ls-files", "--stage"),
        _git(repo, "tag", "--list"),
        _git(repo, "status", "--porcelain", "--untracked-files=all"),
    )


@pytest.fixture
def main_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "yamlgraph").mkdir()
    (repo / "changelog" / "unreleased").mkdir(parents=True)
    shutil.copy2(SCRIPT, repo / "scripts" / "release.sh")
    (repo / "pyproject.toml").write_text('version = "0.0.1"\n', encoding="utf-8")
    (repo / "yamlgraph" / "__init__.py").write_text(
        '__version__ = "0.0.1"\n', encoding="utf-8"
    )
    (repo / "changelog" / "unreleased" / "fr-1-x.md").write_text(
        "---\ntype: fix\nscope: x\n---\n- **FR-1 X**: x.\n", encoding="utf-8"
    )
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "core.hooksPath", "/dev/null")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


@pytest.mark.req("REQ-YG-190")
def test_release_script_refuses_main_without_mutation(main_repo: Path) -> None:
    before = _snapshot(main_repo)
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null"}
    result = subprocess.run(
        ["bash", "scripts/release.sh", "0.0.2"],
        cwd=main_repo,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "main" in output and "release/v0.0.2" in output, output
    assert _snapshot(main_repo) == before


@pytest.mark.req("REQ-YG-190")
@pytest.mark.parametrize("doc", [CHECKLIST, SKILL], ids=["checklist", "skill"])
def test_release_docs_have_no_tags_push(doc: Path) -> None:
    text = doc.read_text(encoding="utf-8")
    assert "push --tags" not in text
    assert "git push && git push" not in text


ROUTE_ORDER = (
    "release/v",
    "scripts/release.sh",
    "gh pr create",
    "human merge decision",
    "--squash",
    "mergeCommit",
    "merge-base --is-ancestor",
    "git tag v",
    "git push origin v",
)


@pytest.mark.req("REQ-YG-190")
@pytest.mark.parametrize("doc", [CHECKLIST, SKILL], ids=["checklist", "skill"])
def test_release_docs_document_ordered_route(doc: Path) -> None:
    _assert_ordered(doc.read_text(encoding="utf-8"), ROUTE_ORDER, doc.name)


@pytest.mark.req("REQ-YG-190")
def test_checklist_verifies_tag_ci_and_exact_pypi_version() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "Expected CI behavior on direct push to main" not in text
    assert "gh release create" not in text
    _assert_ordered(
        text,
        ("gh run list --branch v", "gh release view v", "pypi.org/pypi/yamlgraph/"),
        "checklist verification",
    )


@pytest.mark.req("REQ-YG-190")
def test_checklist_recovery_stops_on_existing_tag() -> None:
    text = CHECKLIST.read_text(encoding="utf-8").lower()
    assert "recovery" in text
    assert "already exists" in text and "stop" in text
    assert "--force" not in text and "tag -d" not in text and "tag -f" not in text
