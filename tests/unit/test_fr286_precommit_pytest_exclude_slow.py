"""RED acceptance tests for FR-286 pre-commit pytest slow-test exclusion.

These tests define the contract for updating the root pre-commit pytest hook
to exclude slow tests with `-m "not slow"` while preserving failure semantics.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PRECOMMIT_PATH = REPO_ROOT / ".pre-commit-config.yaml"
CLAUDE_PATH = REPO_ROOT / "CLAUDE.md"

EXPECTED_PYTEST_ENTRY = (
    "bash -c '.venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov "
    '-m "not slow" && echo "" && echo "✓ Unit tests passed. Run integration '
    'tests separately:" && echo "  pytest tests/integration/ -v"\''
)


def _load_precommit() -> dict:
    """Load root pre-commit config as YAML."""
    return yaml.safe_load(PRECOMMIT_PATH.read_text())


def _get_root_pytest_hook() -> dict:
    """Return the root local pytest hook from .pre-commit-config.yaml."""
    config = _load_precommit()
    for repo in config.get("repos", []):
        if repo.get("repo") == "local":
            for hook in repo.get("hooks", []):
                if hook.get("id") == "pytest":
                    return hook
    raise AssertionError("Root local pytest hook not found in .pre-commit-config.yaml")


def _get_pytest_entry() -> str:
    """Return the root pytest hook shell entry."""
    return _get_root_pytest_hook().get("entry", "")


@pytest.mark.req("REQ-YG-275")
class TestFR286PrecommitPytestSlowExclusion:
    """Acceptance criteria for FR-286."""

    def test_ac01_root_pytest_hook_includes_not_slow_marker(self) -> None:
        """AC-01: Root pytest hook includes `-m "not slow"`."""
        entry = _get_pytest_entry()
        assert '-m "not slow"' in entry, (
            "Root .pre-commit-config.yaml pytest hook must include " '-m "not slow".'
        )

    def test_ac02_hook_targets_unit_tests_with_slow_filter(self) -> None:
        """AC-02: Hook command targets unit tests and excludes slow tests."""
        entry = _get_pytest_entry()
        assert "pytest tests/unit/" in entry, "Hook must run tests/unit/."
        assert (
            '-m "not slow"' in entry
        ), "Hook must filter out @pytest.mark.slow tests via marker expression."

    def test_ac03_hook_preserves_failure_behavior_for_non_slow_tests(self) -> None:
        """AC-03: Hook remains fail-fast for non-slow test failures."""
        entry = _get_pytest_entry()
        pytest_segment = entry.split("&&", maxsplit=1)[0]

        assert "|| true" not in entry, "Hook must not mask pytest failures."
        assert "; true" not in entry, "Hook must not force success after pytest."
        assert "pytest tests/unit/" in pytest_segment, "Hook must execute pytest."
        assert (
            '-m "not slow"' in pytest_segment
        ), "Fail-fast behavior must apply to non-slow test subset."

    def test_ac04_slow_test_command_remains_available(self) -> None:
        """AC-04: Slow tests remain runnable outside pre-commit."""
        claude_content = CLAUDE_PATH.read_text()
        entry = _get_pytest_entry()

        assert (
            'pytest tests/unit/ -q --no-cov -m "slow"' in claude_content
        ), "CLAUDE.md must document explicit slow-test execution."
        assert (
            '-m "not slow"' in entry
        ), "Pre-commit must run the complementary non-slow subset."

    def test_ac05_hook_command_contract_is_explicit(self) -> None:
        """AC-05: Hook command behavior is asserted by exact contract."""
        entry = _get_pytest_entry()
        assert (
            entry == EXPECTED_PYTEST_ENTRY
        ), "Root pytest hook entry must match the FR-286 command contract."

    def test_ac06_documented_fast_command_and_hook_are_consistent(self) -> None:
        """AC-06: Documentation and hook command stay in sync."""
        claude_content = CLAUDE_PATH.read_text()
        entry = _get_pytest_entry()

        assert (
            'pytest tests/unit/ -q --no-cov -m "not slow"' in claude_content
        ), "CLAUDE.md must document the fast non-slow unit-test command."
        assert (
            '-m "not slow"' in entry
        ), "Root pytest hook must align with documented fast-test command."
