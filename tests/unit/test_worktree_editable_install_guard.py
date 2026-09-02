"""Condemning tests for FR-236: worktree teardown editable install guard.

Bug: clean_stale_pth_entries() removes .pth and .egg-link files referencing a
deleted worktree, but does NOT clean direct_url.json inside *.dist-info/
directories.  Modern pip (21.3+) editable installs create these files with the
worktree path, leaving stale metadata after teardown.

After cleanup:
  - pip show <package> still reports the deleted worktree as Location
  - pip install -e . from the main repo may skip reinstall because dist-info
    metadata already exists

These tests MUST FAIL on the unmodified codebase (proving the bug), then PASS
after the fix.
"""

import json
from pathlib import Path

import pytest


def _make_venv_with_site_packages(tmp_path: Path) -> tuple[Path, Path]:
    """Create a minimal .venv with lib/python3.XX/site-packages."""
    venv = tmp_path / ".venv"
    site_packages = venv / "lib" / "python3.11" / "site-packages"
    site_packages.mkdir(parents=True)
    return venv, site_packages


@pytest.mark.req("REQ-YG-156")
class TestCleanStaleDistInfoDirectUrl:
    """clean_stale_pth_entries must also clean direct_url.json in dist-info."""

    def test_direct_url_json_referencing_worktree_is_cleaned(
        self, tmp_path: Path
    ) -> None:
        """direct_url.json inside dist-info referencing the worktree must be
        removed (or the entire dist-info directory purged) after cleanup."""
        from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries

        venv, site_packages = _make_venv_with_site_packages(tmp_path)
        worktree_dir = "/tmp/worktrees/feat/fr-236-test"

        # Modern pip editable install creates __editable__.pth AND dist-info
        pth = site_packages / "__editable__.yamlgraph-0.4.68.pth"
        pth.write_text(f"{worktree_dir}/src\n", encoding="utf-8")

        dist_info = site_packages / "yamlgraph-0.4.68.dist-info"
        dist_info.mkdir()
        direct_url = dist_info / "direct_url.json"
        direct_url.write_text(
            json.dumps(
                {
                    "url": f"file://{worktree_dir}",
                    "dir_info": {"editable": True},
                }
            )
        , encoding="utf-8")

        removed = clean_stale_pth_entries(venv, worktree_dir)

        # .pth should be cleaned (existing behavior)
        assert not pth.exists(), ".pth file should have been removed"
        assert any(p.name.endswith(".pth") for p in removed)

        # BUG: direct_url.json is NOT cleaned by the current implementation
        # This assertion MUST FAIL on the unmodified codebase.
        assert not direct_url.exists(), (
            "direct_url.json still references deleted worktree — "
            "stale dist-info metadata survives cleanup"
        )

    def test_dist_info_with_worktree_url_reported_in_removed_list(
        self, tmp_path: Path
    ) -> None:
        """The returned list must include dist-info artifacts that were cleaned."""
        from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries

        venv, site_packages = _make_venv_with_site_packages(tmp_path)
        worktree_dir = "/tmp/worktrees/feat/fr-236-test"

        dist_info = site_packages / "yamlgraph-0.4.68.dist-info"
        dist_info.mkdir()
        direct_url = dist_info / "direct_url.json"
        direct_url.write_text(
            json.dumps(
                {
                    "url": f"file://{worktree_dir}",
                    "dir_info": {"editable": True},
                }
            )
        , encoding="utf-8")

        removed = clean_stale_pth_entries(venv, worktree_dir)

        # BUG: current implementation returns empty list — it doesn't touch
        # dist-info at all. This MUST FAIL on unmodified code.
        assert len(removed) > 0, (
            "clean_stale_pth_entries returned empty list despite stale "
            "direct_url.json referencing the worktree"
        )

    def test_unrelated_dist_info_preserved(self, tmp_path: Path) -> None:
        """dist-info directories for packages NOT pointing at the worktree
        must be left untouched."""
        from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries

        venv, site_packages = _make_venv_with_site_packages(tmp_path)
        worktree_dir = "/tmp/worktrees/feat/fr-236-test"

        # Unrelated package dist-info
        other_dist = site_packages / "requests-2.31.0.dist-info"
        other_dist.mkdir()
        other_url = other_dist / "direct_url.json"
        other_url.write_text(
            json.dumps({"url": "https://pypi.org/packages/requests-2.31.0.tar.gz"})
        , encoding="utf-8")

        # Stale worktree dist-info
        stale_dist = site_packages / "yamlgraph-0.4.68.dist-info"
        stale_dist.mkdir()
        stale_url = stale_dist / "direct_url.json"
        stale_url.write_text(
            json.dumps(
                {
                    "url": f"file://{worktree_dir}",
                    "dir_info": {"editable": True},
                }
            )
        , encoding="utf-8")

        clean_stale_pth_entries(venv, worktree_dir)

        # Unrelated package MUST survive
        assert other_url.exists(), "Unrelated dist-info must not be touched"
        # Stale package MUST be cleaned — this MUST FAIL on unmodified code
        assert (
            not stale_url.exists()
        ), "Stale direct_url.json referencing worktree survives cleanup"
