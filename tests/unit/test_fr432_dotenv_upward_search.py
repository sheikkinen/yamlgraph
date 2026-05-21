"""FR-432 tests: upward .env search with .git directory boundary."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

_ENV_KEY = "FR432_ENV_PROBE"
_ORIGINAL_CWD = Path.cwd()


@pytest.fixture(autouse=True)
def _restore_config_module_state() -> None:
    """Prevent config module state from leaking cwd-derived constants across tests."""
    yield
    sys.modules.pop("yamlgraph.config", None)
    os.environ.pop(_ENV_KEY, None)
    os.chdir(_ORIGINAL_CWD)


def _import_config_fresh():
    """Import yamlgraph.config fresh so module-level dotenv loading re-runs."""
    sys.modules.pop("yamlgraph.config", None)
    return importlib.import_module("yamlgraph.config")


@pytest.mark.req("REQ-YG-043")
def test_env_found_in_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When .env is in CWD, config import should load it."""
    (tmp_path / ".env").write_text(f"{_ENV_KEY}=cwd\n", encoding="utf-8")

    monkeypatch.delenv(_ENV_KEY, raising=False)
    monkeypatch.chdir(tmp_path)
    _import_config_fresh()

    assert _ENV_KEY in __import__("os").environ
    assert __import__("os").environ[_ENV_KEY] == "cwd"


@pytest.mark.req("REQ-YG-043")
def test_env_found_in_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When .env exists in parent, upward search should find and load it."""
    parent = tmp_path / "project"
    child = parent / "subdir"
    child.mkdir(parents=True)
    (parent / ".env").write_text(f"{_ENV_KEY}=parent\n", encoding="utf-8")

    monkeypatch.delenv(_ENV_KEY, raising=False)
    monkeypatch.chdir(child)
    _import_config_fresh()

    assert __import__("os").environ[_ENV_KEY] == "parent"


@pytest.mark.req("REQ-YG-043")
def test_cwd_env_takes_precedence_over_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When both exist, .env in CWD should win over parent .env."""
    parent = tmp_path / "project"
    child = parent / "app"
    child.mkdir(parents=True)
    (parent / ".env").write_text(f"{_ENV_KEY}=parent\n", encoding="utf-8")
    (child / ".env").write_text(f"{_ENV_KEY}=cwd\n", encoding="utf-8")

    monkeypatch.delenv(_ENV_KEY, raising=False)
    monkeypatch.chdir(child)
    _import_config_fresh()

    assert __import__("os").environ[_ENV_KEY] == "cwd"


@pytest.mark.req("REQ-YG-043")
def test_git_dir_boundary_blocks_parent_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Search must stop at .git directory boundary and not load outer .env."""
    outer = tmp_path / "outer"
    repo = outer / "repo"
    sub = repo / "subdir"
    sub.mkdir(parents=True)
    (outer / ".env").write_text(f"{_ENV_KEY}=outer\n", encoding="utf-8")
    (repo / ".git").mkdir(parents=True)

    monkeypatch.delenv(_ENV_KEY, raising=False)
    monkeypatch.chdir(sub)
    _import_config_fresh()

    assert _ENV_KEY not in __import__("os").environ


@pytest.mark.req("REQ-YG-043")
def test_worktree_git_file_allows_continued_search(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A worktree .git file should not stop upward search to main repo .env."""
    repo = tmp_path / "repo"
    worktree = repo / "tmp" / "worktrees" / "wt"
    work_sub = worktree / "nested"
    work_sub.mkdir(parents=True)

    (repo / ".git").mkdir(parents=True)
    (repo / ".env").write_text(f"{_ENV_KEY}=repo\n", encoding="utf-8")
    (worktree / ".git").write_text("gitdir: /fake/path\n", encoding="utf-8")

    monkeypatch.delenv(_ENV_KEY, raising=False)
    monkeypatch.chdir(work_sub)
    _import_config_fresh()

    assert __import__("os").environ[_ENV_KEY] == "repo"


@pytest.mark.req("REQ-YG-043")
def test_no_env_anywhere_keeps_env_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No .env in search path should leave env var unset."""
    cwd = tmp_path / "a" / "b"
    cwd.mkdir(parents=True)

    monkeypatch.delenv(_ENV_KEY, raising=False)
    monkeypatch.chdir(cwd)
    _import_config_fresh()

    assert _ENV_KEY not in __import__("os").environ
