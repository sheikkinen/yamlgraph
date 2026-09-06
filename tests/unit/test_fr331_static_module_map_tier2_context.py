"""RED acceptance tests for FR-331 static module map Tier-2 context."""

import subprocess
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
SCRIPT_PATH = WORKTREE / "scripts" / "generate_module_map.py"
MODULE_MAP_PATH = WORKTREE / "reference" / "module-map.md"
CLAUDE_PATH = WORKTREE / "CLAUDE.md"


def _script_text() -> str:
    assert SCRIPT_PATH.exists(), f"Missing generator script: {SCRIPT_PATH}"
    return SCRIPT_PATH.read_text(encoding="utf-8")


def _module_map_text() -> str:
    assert MODULE_MAP_PATH.exists(), f"Missing generated map: {MODULE_MAP_PATH}"
    return MODULE_MAP_PATH.read_text(encoding="utf-8")


@pytest.mark.req("REQ-YG-667")
class TestFR331StaticModuleMapTier2Context:
    """AC-01..AC-06 contract for static module-map generation."""

    def test_ac01_generator_script_exists_and_uses_ast_parse(self) -> None:
        text = _script_text()
        assert "import ast" in text
        assert "ast.parse(" in text

    def test_ac02_generator_writes_reference_module_map_markdown(
        self, tmp_path: Path
    ) -> None:
        assert SCRIPT_PATH.exists(), f"Missing generator script: {SCRIPT_PATH}"
        out = tmp_path / "module-map.md"
        completed = subprocess.run(
            ["python", str(SCRIPT_PATH), str(out)],
            cwd=WORKTREE,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        content = out.read_text(encoding="utf-8").lower()
        assert "metadata" in content
        assert "module" in content
        assert "test_map" in content

    def test_ac03_module_entries_include_exports_and_import_dependencies(self) -> None:
        content = _module_map_text().lower()
        assert "yamlgraph/" in content
        assert any(token in content for token in ("line count", "lines"))
        assert any(token in content for token in ("exports", "functions", "classes"))
        assert any(token in content for token in ("import", "dependencies"))

    def test_ac04_output_contains_test_map_section_with_deterministic_mapping(
        self,
    ) -> None:
        content = _module_map_text().lower()
        assert "test_map" in content
        assert "tests/" in content
        assert "deterministic" in content

    def test_ac05_claude_references_module_map_artifact(self) -> None:
        assert CLAUDE_PATH.exists(), f"Missing CLAUDE.md: {CLAUDE_PATH}"
        claude = CLAUDE_PATH.read_text(encoding="utf-8")
        assert (
            "@reference/module-map.md" in claude or "reference/module-map.md" in claude
        )

    def test_ac06_generator_has_no_external_parser_dependencies(self) -> None:
        text = _script_text().lower()
        assert "import ast" in text
        assert "ast.parse" in text
        assert "tree_sitter" not in text
        assert "libcst" not in text
