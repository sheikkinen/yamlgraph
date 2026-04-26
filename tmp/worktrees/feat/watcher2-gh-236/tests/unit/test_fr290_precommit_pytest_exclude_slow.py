"""Acceptance tests for FR-290: pre-commit pytest hook excludes slow tests.

These tests define the RED contract for updating the local pre-commit pytest
hook to run fast unit checks via marker filtering.
"""

from pathlib import Path

import pytest
import yaml


def _discover_repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / ".pre-commit-config.yaml").exists() and (
            candidate / "pyproject.toml"
        ).exists():
            return candidate
    raise AssertionError(
        "Could not locate repository root with pre-commit and pyproject"
    )


REPO_ROOT = _discover_repo_root()
PRECOMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
PYPROJECT_TOML = REPO_ROOT / "pyproject.toml"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load_precommit_config() -> dict:
    with open(PRECOMMIT_CONFIG) as f:
        data = yaml.safe_load(f)
    _require(
        isinstance(data, dict),
        "Expected .pre-commit-config.yaml to parse to mapping",
    )
    return data


def _find_local_hook(hook_id: str) -> dict:
    config = _load_precommit_config()
    repos = config.get("repos", [])
    for repo in repos:
        if repo.get("repo") != "local":
            continue
        for hook in repo.get("hooks", []):
            if hook.get("id") == hook_id:
                return hook
    raise AssertionError(f"Missing local hook '{hook_id}' in .pre-commit-config.yaml")


@pytest.mark.req("REQ-YG-002")
class TestFR290PrecommitPytestExcludesSlow:
    """Acceptance criteria for FR-290."""

    def test_ac01_pytest_hook_includes_not_slow_marker(self) -> None:
        """AC-01: local pytest hook includes -m "not slow"."""
        hook = _find_local_hook("pytest")
        entry = hook.get("entry", "")
        _require(
            '-m "not slow"' in entry,
            'pytest hook entry must include marker filter: -m "not slow"',
        )

    def test_ac02_pytest_hook_keeps_unit_and_core_flags(self) -> None:
        """AC-02: hook keeps tests/unit + -q --tb=short --no-cov while filtering slow."""
        hook = _find_local_hook("pytest")
        entry = hook.get("entry", "")

        for expected in ("tests/unit/", "-q", "--tb=short", "--no-cov"):
            _require(
                expected in entry,
                f"Expected '{expected}' in pytest hook entry",
            )

        _require(
            '-m "not slow"' in entry,
            "Core flags must be preserved with marker filter enabled",
        )

    def test_ac03_pytest_hook_contract_remains_precommit_local(self) -> None:
        """AC-03: hook remains local pre-commit hook with always_run/pass_filenames contract."""
        hook = _find_local_hook("pytest")

        _require(
            hook.get("pass_filenames") is False,
            "pytest hook must keep pass_filenames: false",
        )
        _require(
            hook.get("always_run") is True,
            "pytest hook must keep always_run: true",
        )
        _require(
            hook.get("stages") == ["pre-commit"],
            "pytest hook must stay at pre-commit stage",
        )
        _require(
            '-m "not slow"' in hook.get("entry", ""),
            "pytest pre-commit hook must filter slow tests",
        )

    def test_ac04_slow_tests_stay_explicitly_runnable(self) -> None:
        """AC-04: slow marker contract remains available via explicit pytest command."""
        pyproject = PYPROJECT_TOML.read_text()
        claude_md = CLAUDE_MD.read_text()
        hook = _find_local_hook("pytest")

        _require(
            "slow: marks tests that take >1 second to complete" in pyproject,
            "pyproject.toml must keep the slow marker definition",
        )
        _require(
            'pytest tests/unit/ -q --no-cov -m "slow"' in claude_md,
            "Developer docs must keep explicit slow-test command",
        )
        _require(
            '-m "not slow"' in hook.get("entry", ""),
            "pre-commit hook must explicitly run the fast counterpart (not slow)",
        )

    def test_ac05_and_ac06_exact_pytest_hook_entry_contract(self) -> None:
        """AC-05/AC-06: enforce exact hook contract and minimal behavior-preserving delta."""
        hook = _find_local_hook("pytest")
        expected_entry = (
            "bash -c '.venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov "
            '-m "not slow" && echo "" && echo "✓ Unit tests passed. Run integration tests '
            'separately:" && echo "  pytest tests/integration/ -v"\''
        )
        _require(
            hook.get("entry", "") == expected_entry,
            "pytest hook entry must match FR-290 contract exactly (only marker-filter delta)",
        )
