"""RED acceptance tests for FR-629 data_files glob support."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from yamlgraph.data_loader import DataFileError, load_data_files


class TestDataFilesGlob:
    """Test glob pattern support in data_files."""

    @pytest.mark.req("REQ-YG-478")
    def test_glob_loads_multiple_files_as_dict(self, tmp_path: Path) -> None:
        """Glob pattern loads all matching files keyed by stem."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "javascript.yaml").write_text(
            "language: JavaScript\nparadigm: multi\n", encoding="utf-8"
        )
        (wiki / "typescript.yaml").write_text(
            "language: TypeScript\nparadigm: typed\n", encoding="utf-8"
        )
        (wiki / "react.yaml").write_text(
            "framework: React\ntype: frontend\n", encoding="utf-8"
        )

        graph_path = tmp_path / "graph.yaml"
        graph_path.touch()

        config = {"data_files": {"wiki": "wiki/*.yaml"}}
        result = load_data_files(config, graph_path)

        assert result["wiki"] == {
            "javascript": {"language": "JavaScript", "paradigm": "multi"},
            "react": {"framework": "React", "type": "frontend"},
            "typescript": {"language": "TypeScript", "paradigm": "typed"},
        }

    @pytest.mark.req("REQ-YG-478")
    def test_glob_zero_matches_returns_empty_dict(self, tmp_path: Path) -> None:
        """Glob matching no files returns empty dict, not error."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        graph_path = tmp_path / "graph.yaml"
        graph_path.touch()

        config = {"data_files": {"wiki": "wiki/*.yaml"}}
        result = load_data_files(config, graph_path)

        assert result["wiki"] == {}

    @pytest.mark.req("REQ-YG-478")
    def test_glob_single_match_returns_dict(self, tmp_path: Path) -> None:
        """Glob matching one file still returns dict (not raw content)."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "only.yaml").write_text("key: value\n", encoding="utf-8")

        graph_path = tmp_path / "graph.yaml"
        graph_path.touch()

        config = {"data_files": {"wiki": "wiki/*.yaml"}}
        result = load_data_files(config, graph_path)

        assert result["wiki"] == {"only": {"key": "value"}}

    @pytest.mark.req("REQ-YG-478")
    def test_glob_sorted_alphabetically(self, tmp_path: Path) -> None:
        """Results sorted alphabetically for deterministic ordering."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "zebra.yaml").write_text("z: true\n", encoding="utf-8")
        (wiki / "alpha.yaml").write_text("a: true\n", encoding="utf-8")
        (wiki / "mid.yaml").write_text("m: true\n", encoding="utf-8")

        graph_path = tmp_path / "graph.yaml"
        graph_path.touch()

        config = {"data_files": {"wiki": "wiki/*.yaml"}}
        result = load_data_files(config, graph_path)

        # Dict preserves insertion order (Python 3.7+)
        assert list(result["wiki"].keys()) == ["alpha", "mid", "zebra"]

    @pytest.mark.req("REQ-YG-479")
    def test_glob_rejects_recursive_pattern(self, tmp_path: Path) -> None:
        """** (recursive glob) is explicitly rejected."""
        graph_path = tmp_path / "graph.yaml"
        graph_path.touch()

        config = {"data_files": {"wiki": "wiki/**/*.yaml"}}

        with pytest.raises(DataFileError, match="(?i)recursive"):
            load_data_files(config, graph_path)

    @pytest.mark.req("REQ-YG-479")
    def test_glob_path_traversal_blocked(self, tmp_path: Path) -> None:
        """Glob pattern escaping graph dir raises DataFileError."""
        graph_path = tmp_path / "graph.yaml"
        graph_path.touch()

        config = {"data_files": {"wiki": "../../../etc/*.yaml"}}

        with pytest.raises(DataFileError, match="escapes"):
            load_data_files(config, graph_path)

    @pytest.mark.req("REQ-YG-479")
    def test_glob_symlink_escaping_boundary_skipped(self, tmp_path: Path) -> None:
        """Symlinks resolving outside graph dir are silently skipped."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "safe.yaml").write_text("safe: true\n", encoding="utf-8")

        # Create a symlink pointing outside
        external = tmp_path.parent / "external_secret.yaml"
        external.write_text("secret: true\n", encoding="utf-8")
        try:
            os.symlink(external, wiki / "escape.yaml")
        except OSError:
            pytest.skip("Cannot create symlinks on this platform")

        graph_path = tmp_path / "graph.yaml"
        graph_path.touch()

        config = {"data_files": {"wiki": "wiki/*.yaml"}}
        result = load_data_files(config, graph_path)

        # Only the safe file is loaded; symlink is skipped
        assert "safe" in result["wiki"]
        assert "escape" not in result["wiki"]

    @pytest.mark.req("REQ-YG-478")
    def test_glob_empty_file_returns_empty_dict(self, tmp_path: Path) -> None:
        """Empty YAML files within glob return {} as value."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "empty.yaml").write_text("", encoding="utf-8")

        graph_path = tmp_path / "graph.yaml"
        graph_path.touch()

        config = {"data_files": {"wiki": "wiki/*.yaml"}}
        result = load_data_files(config, graph_path)

        assert result["wiki"] == {"empty": {}}

    @pytest.mark.req("REQ-YG-478")
    def test_single_file_path_unchanged(self, tmp_path: Path) -> None:
        """Single file path (no glob chars) works exactly as before."""
        (tmp_path / "schema.yaml").write_text(
            "fields:\n  - name: x\n", encoding="utf-8"
        )
        graph_path = tmp_path / "graph.yaml"
        graph_path.touch()

        config = {"data_files": {"schema": "schema.yaml"}}
        result = load_data_files(config, graph_path)

        assert result["schema"] == {"fields": [{"name": "x"}]}
