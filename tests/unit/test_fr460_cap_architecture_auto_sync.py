"""FR-460 CAP Architecture Auto-Sync — Unit tests.

Tests that the pre-commit hook for automatic ARCHITECTURE.md regeneration
is properly configured and that the aggregate script produces correct output.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
import yaml

# FR-756: this module loads scripts/aggregate_capabilities.py as a module.
pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
AGGREGATE_SCRIPT = REPO_ROOT / "scripts" / "aggregate_capabilities.py"
ARCHITECTURE_MD = REPO_ROOT / "ARCHITECTURE.md"


def _load_aggregate_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "aggregate_capabilities", AGGREGATE_SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    def test_aggregate_script_exits_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FR-1044 AC-01: exit 0 without ever reaching the write boundary.

        Byte equality and `git status` cannot witness this: on a synced tree the
        script rewrites identical bytes and both proxies still pass.
        """
        mod = _load_aggregate_module()

        def _forbidden(*args: object, **kwargs: object) -> None:
            raise AssertionError(
                "aggregate_capabilities wrote a file during a unit test "
                "(FR-1044: the test must run --dry-run)"
            )

        monkeypatch.setattr(Path, "write_text", _forbidden)
        monkeypatch.setattr(sys, "argv", ["aggregate_capabilities.py", "--dry-run"])

        assert mod.main() == 0

    @pytest.mark.req("REQ-YG-425")
    def test_generated_section_matches_committed(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """FR-1044 AC-02: the committed section equals what generation produces.

        Drift here is a failing test instead of a hook-side write mid-commit.
        """
        mod = _load_aggregate_module()
        monkeypatch.setattr(sys, "argv", ["aggregate_capabilities.py", "--dry-run"])
        assert mod.main() == 0
        generated = capsys.readouterr().out.strip()

        text = ARCHITECTURE_MD.read_text(encoding="utf-8")
        begin = text.index(mod.BEGIN_MARKER) + len(mod.BEGIN_MARKER)
        committed = text[begin : text.index(mod.END_MARKER)].strip()

        assert generated == committed, (
            "ARCHITECTURE.md generated section is out of sync with capabilities/ "
            "— run: python scripts/aggregate_capabilities.py"
        )
