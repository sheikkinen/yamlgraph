"""Acceptance tests for FR-441 pre-commit files pattern scoping."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

pytestmark = pytest.mark.process

PRECOMMIT_PATH = Path(".pre-commit-config.yaml")

TARGET_HOOK_FILES_PATTERNS = {
    "req-coverage-strict": (
        r"(^yamlgraph/|^tests/|^ARCHITECTURE\.md$|^capabilities/|^scripts/req_coverage\.py$)"
    ),
    "validate-capabilities": r"(^capabilities/|^scripts/validate_capabilities\.py$)",
    "noqa-confession": r"(\.py$|^docs/confessions\.md$|^scripts/noqa_coverage\.py$)",
    "inline-llm-check": r"(\.py$|^scripts/lint_inline_llm\.py$)",
    "radon-complexity": r"\.py$",
    "file-size-gate": (
        r"\.(py|sh)$|^(CLAUDE\.md|\.github/copilot-instructions\.md)$"
    ),  # FR-889 AC-11 shell; FR-942 instruction byte ceiling
    "forbid-terms": r"\.py$",
    "jscpd-dup": r"\.py$",
    "import-linter": r"(\.py$|^\.importlinter$)",
    "vulture-dead-code": r"(\.py$|^vulture_whitelist\.py$)",
    "hedging-check": r"\.py$",
    "changelog-release-sync": (
        r"(^changelog/|^pyproject\.toml$|^scripts/check_changelog_release_sync\.py$|^scripts/release\.sh$)"
    ),
    "changelog-req-cross-check": (
        r"(^changelog/|^capabilities/|^scripts/check_changelog_req\.py$)"
    ),
    "diary-reflection-check": r"^docs/diary/",
    "diary-filename-check": r"^docs/diary/",
    "pytest": r"(\.py$|\.yaml$|\.yml$|^pyproject\.toml$)",
}


def _load_precommit() -> dict[str, Any]:
    with PRECOMMIT_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_hook(hook_id: str) -> dict[str, Any]:
    config = _load_precommit()
    for repo in config.get("repos", []):
        for hook in repo.get("hooks", []):
            if hook.get("id") == hook_id:
                return hook
    pytest.fail(f"Missing hook in .pre-commit-config.yaml: {hook_id}")


@pytest.mark.req("REQ-YG-002")
def test_ac01_target_hooks_define_files_patterns() -> None:
    for hook_id, expected_pattern in TARGET_HOOK_FILES_PATTERNS.items():
        hook = _get_hook(hook_id)
        assert hook.get("files") == expected_pattern


@pytest.mark.req("REQ-YG-002")
def test_ac02_target_hooks_do_not_use_always_run() -> None:
    for hook_id in TARGET_HOOK_FILES_PATTERNS:
        hook = _get_hook(hook_id)
        assert hook.get("always_run") is not True


@pytest.mark.req("REQ-YG-002")
def test_ac03_cross_cutting_hooks_not_modified_by_fr441() -> None:
    diary_rotate = _get_hook("diary-rotate")
    final_summary = _get_hook("final-summary")
    demo_proof = _get_hook("demo-proof-check")
    gitignore_guard = _get_hook("gitignore-boundary-guard")

    assert diary_rotate.get("always_run") is True
    assert final_summary.get("always_run") is True

    assert demo_proof.get("always_run") is not True
    assert "files" not in demo_proof

    assert gitignore_guard.get("always_run") is not True
    assert "files" not in gitignore_guard


@pytest.mark.req("REQ-YG-002")
def test_ac04_pytest_hook_pattern_covers_code_and_yaml() -> None:
    pytest_hook = _get_hook("pytest")
    files_pattern = str(pytest_hook.get("files", ""))

    assert files_pattern == TARGET_HOOK_FILES_PATTERNS["pytest"]
    assert ".py$" in files_pattern
    assert ".yaml$" in files_pattern
    assert ".yml$" in files_pattern
    assert "pyproject\\.toml$" in files_pattern


@pytest.mark.req("REQ-YG-002")
def test_ac05_dependency_rationale_existing_scope_unchanged() -> None:
    dependency_rationale = _get_hook("dependency-rationale")
    assert dependency_rationale.get("files") == (
        r"(pyproject\.toml|docs/dependency-rationale\.yaml)"
    )
