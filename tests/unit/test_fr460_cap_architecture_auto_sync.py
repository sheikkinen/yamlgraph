"""FR-460 CAP Architecture Auto-Sync — Unit tests.

Tests that the pre-commit hook for automatic ARCHITECTURE.md regeneration
is properly configured and that the aggregate script produces correct output.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
AGGREGATE_SCRIPT = REPO_ROOT / "scripts" / "aggregate_capabilities.py"
ARCHITECTURE_MD = REPO_ROOT / "ARCHITECTURE.md"


def _load_pre_commit_hooks() -> list[dict]:
    """Load all hooks from .pre-commit-config.yaml."""
    raw = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
    hooks = []
    for repo in raw.get("repos", []):
        for hook in repo.get("hooks", []):
            hooks.append(hook)
    return hooks


def _find_hook(hook_id: str) -> dict | None:
    """Find a specific hook by id."""
    for hook in _load_pre_commit_hooks():
        if hook.get("id") == hook_id:
            return hook
    return None


class TestCapArchitectureSyncHook:
    """Test pre-commit hook configuration."""

    @pytest.mark.req("REQ-YG-425")
    def test_hook_exists(self) -> None:
        """cap-architecture-sync hook must be registered."""
        hook = _find_hook("cap-architecture-sync")
        assert (
            hook is not None
        ), "Hook 'cap-architecture-sync' not found in .pre-commit-config.yaml"

    @pytest.mark.req("REQ-YG-425")
    def test_hook_entry_runs_aggregate_script(self) -> None:
        """Hook must run aggregate_capabilities.py."""
        hook = _find_hook("cap-architecture-sync")
        assert "aggregate_capabilities" in hook["entry"]

    @pytest.mark.req("REQ-YG-425")
    def test_hook_triggers_on_cap_files(self) -> None:
        """Hook must trigger on capabilities/*.yaml changes."""
        hook = _find_hook("cap-architecture-sync")
        files_pattern = hook["files"]
        assert "capabilities" in files_pattern
        assert r"\.yaml" in files_pattern

    @pytest.mark.req("REQ-YG-425")
    def test_hook_triggers_on_aggregate_script(self) -> None:
        """Hook must also trigger when aggregate script itself changes."""
        hook = _find_hook("cap-architecture-sync")
        files_pattern = hook["files"]
        assert "aggregate_capabilities" in files_pattern

    @pytest.mark.req("REQ-YG-425")
    def test_hook_does_not_pass_filenames(self) -> None:
        """Hook must not pass filenames (aggregate script processes all)."""
        hook = _find_hook("cap-architecture-sync")
        assert hook.get("pass_filenames") is False

    @pytest.mark.req("REQ-YG-425")
    def test_hook_is_pre_commit_stage(self) -> None:
        """Hook must run at pre-commit stage."""
        hook = _find_hook("cap-architecture-sync")
        assert "pre-commit" in hook.get("stages", [])

    @pytest.mark.req("REQ-YG-425")
    def test_aggregate_script_exists(self) -> None:
        """aggregate_capabilities.py must exist."""
        assert AGGREGATE_SCRIPT.is_file()

    @pytest.mark.req("REQ-YG-425")
    def test_architecture_has_generation_markers(self) -> None:
        """ARCHITECTURE.md must have BEGIN/END generation markers."""
        text = ARCHITECTURE_MD.read_text(encoding="utf-8")
        assert "<!-- BEGIN GENERATED CAPABILITIES -->" in text
        assert "<!-- END GENERATED CAPABILITIES -->" in text

    @pytest.mark.req("REQ-YG-425")
    def test_aggregate_script_exits_zero(self) -> None:
        """aggregate_capabilities.py must exit 0 (ruff-format pattern)."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "aggregate_capabilities", AGGREGATE_SCRIPT
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.main()
        assert result == 0, "aggregate_capabilities.py must exit 0 for auto-fix pattern"
