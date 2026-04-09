"""Tests for scripts/dependency_rationale.py — dependency rationale audit.

FR-219: Dependency Rationale Audit — verify every pyproject.toml dependency
has a documented rationale in docs/dependency-rationale.yaml.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import dependency_rationale

# ---------------------------------------------------------------------------
# parse_pyproject_dependencies
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-219")
class TestParsePyprojectDependencies:
    """Tests for parse_pyproject_dependencies() function."""

    def test_extracts_core_dependencies(self, tmp_path: Path) -> None:
        """Core dependencies should be extracted with version specifiers stripped."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("""\
[project]
dependencies = [
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
]
""")

        result = dependency_rationale.parse_pyproject_dependencies(toml)

        assert "pydantic" in result["core"]
        assert "pyyaml" in result["core"]

    def test_extracts_optional_dependencies(self, tmp_path: Path) -> None:
        """Optional dependency groups should be extracted."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("""\
[project]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
]
redis = [
    "langgraph-checkpoint-redis>=0.3.0",
]
""")

        result = dependency_rationale.parse_pyproject_dependencies(toml)

        assert "pytest" in result["dev"]
        assert "ruff" in result["dev"]
        assert "langgraph-checkpoint-redis" in result["redis"]

    def test_strips_version_specifiers(self, tmp_path: Path) -> None:
        """Version specifiers (>=, <, ==, ~=) should be stripped from names."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("""\
[project]
dependencies = [
    "a2a-sdk[http-server]>=0.3,<1.0",
    "langchain-anthropic>=0.3.0",
]
""")

        result = dependency_rationale.parse_pyproject_dependencies(toml)

        assert "a2a-sdk" in result["core"]
        assert "langchain-anthropic" in result["core"]

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """Missing pyproject.toml should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            dependency_rationale.parse_pyproject_dependencies(
                tmp_path / "nonexistent.toml"
            )


# ---------------------------------------------------------------------------
# parse_rationale_registry
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-219")
class TestParseRationaleRegistry:
    """Tests for parse_rationale_registry() function."""

    def test_extracts_documented_packages(self, tmp_path: Path) -> None:
        """Documented packages should be returned as a set."""
        registry = tmp_path / "dependency-rationale.yaml"
        registry.write_text("""\
dependencies:
  pydantic:
    rationale: "Structured validation"
    modules: ["yamlgraph/models/"]
    added: "0.1.0"
  pyyaml:
    rationale: "YAML parsing"
    modules: ["yamlgraph/data_loader.py"]
    added: "0.1.0"
""")

        result = dependency_rationale.parse_rationale_registry(registry)

        assert "pydantic" in result
        assert "pyyaml" in result

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Missing registry file should return empty dict."""
        result = dependency_rationale.parse_rationale_registry(
            tmp_path / "nonexistent.yaml"
        )
        assert result == {}

    def test_validates_required_fields(self, tmp_path: Path) -> None:
        """Entries missing required fields should be reported."""
        registry = tmp_path / "dependency-rationale.yaml"
        registry.write_text("""\
dependencies:
  pydantic:
    rationale: "Structured validation"
  pyyaml:
    modules: ["yamlgraph/data_loader.py"]
""")

        result = dependency_rationale.parse_rationale_registry(registry)

        # Both should be in the dict but pyyaml missing rationale
        assert "pydantic" in result
        assert "pyyaml" in result
        # Entry without rationale should be flagged as incomplete
        assert result["pydantic"]["rationale"] == "Structured validation"
        assert result["pyyaml"].get("rationale") is None


# ---------------------------------------------------------------------------
# find_undocumented
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-219")
class TestFindUndocumented:
    """Tests for find_undocumented() function."""

    def test_all_documented_returns_empty(self) -> None:
        """When all deps are documented, undocumented list should be empty."""
        deps = {"core": ["pydantic", "pyyaml"]}
        registry = {
            "pydantic": {"rationale": "x", "modules": ["m"]},
            "pyyaml": {"rationale": "x", "modules": ["m"]},
        }

        result = dependency_rationale.find_undocumented(deps, registry)

        assert result == {}

    def test_missing_deps_reported(self) -> None:
        """Undocumented deps should be reported by group."""
        deps = {"core": ["pydantic", "pyyaml", "jinja2"]}
        registry = {
            "pydantic": {"rationale": "x", "modules": ["m"]},
        }

        result = dependency_rationale.find_undocumented(deps, registry)

        assert "pyyaml" in result["core"]
        assert "jinja2" in result["core"]

    def test_optional_groups_checked(self) -> None:
        """Optional dependency groups should also be checked."""
        deps = {
            "core": ["pydantic"],
            "dev": ["pytest", "ruff"],
        }
        registry = {
            "pydantic": {"rationale": "x", "modules": ["m"]},
            "pytest": {"rationale": "x", "modules": ["m"]},
        }

        result = dependency_rationale.find_undocumented(deps, registry)

        assert "core" not in result
        assert "ruff" in result["dev"]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-219")
class TestMain:
    """Tests for main() entry point."""

    def test_no_gaps_returns_zero(self, tmp_path: Path) -> None:
        """All documented → exit 0."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("""\
[project]
dependencies = ["pydantic>=2.0.0"]
""")

        registry = tmp_path / "docs" / "dependency-rationale.yaml"
        registry.parent.mkdir()
        registry.write_text("""\
dependencies:
  pydantic:
    rationale: "Validation"
    modules: ["yamlgraph/models/"]
    added: "0.1.0"
""")

        with patch.object(dependency_rationale.sys, "argv", ["dep_rationale.py"]):
            original_file = dependency_rationale.__file__
            try:
                dependency_rationale.__file__ = str(
                    tmp_path / "scripts" / "dependency_rationale.py"
                )
                exit_code = dependency_rationale.main()
            finally:
                dependency_rationale.__file__ = original_file

        assert exit_code == 0

    def test_strict_with_gaps_returns_one(self, tmp_path: Path) -> None:
        """Undocumented deps + --strict → exit 1."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("""\
[project]
dependencies = ["pydantic>=2.0.0", "pyyaml>=6.0"]
""")

        registry = tmp_path / "docs" / "dependency-rationale.yaml"
        registry.parent.mkdir()
        registry.write_text("""\
dependencies:
  pydantic:
    rationale: "Validation"
    modules: ["yamlgraph/models/"]
    added: "0.1.0"
""")

        with patch.object(
            dependency_rationale.sys, "argv", ["dep_rationale.py", "--strict"]
        ):
            original_file = dependency_rationale.__file__
            try:
                dependency_rationale.__file__ = str(
                    tmp_path / "scripts" / "dependency_rationale.py"
                )
                exit_code = dependency_rationale.main()
            finally:
                dependency_rationale.__file__ = original_file

        assert exit_code == 1

    def test_non_strict_with_gaps_returns_zero(self, tmp_path: Path) -> None:
        """Undocumented deps without --strict → exit 0 (advisory)."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("""\
[project]
dependencies = ["pydantic>=2.0.0", "pyyaml>=6.0"]
""")

        registry = tmp_path / "docs" / "dependency-rationale.yaml"
        registry.parent.mkdir()
        registry.write_text("""\
dependencies:
  pydantic:
    rationale: "Validation"
    modules: ["yamlgraph/models/"]
    added: "0.1.0"
""")

        with patch.object(dependency_rationale.sys, "argv", ["dep_rationale.py"]):
            original_file = dependency_rationale.__file__
            try:
                dependency_rationale.__file__ = str(
                    tmp_path / "scripts" / "dependency_rationale.py"
                )
                exit_code = dependency_rationale.main()
            finally:
                dependency_rationale.__file__ = original_file

        assert exit_code == 0

    def test_detail_mode(self, tmp_path: Path, capsys) -> None:
        """--detail should print all rationale entries."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("""\
[project]
dependencies = ["pydantic>=2.0.0"]
""")

        registry = tmp_path / "docs" / "dependency-rationale.yaml"
        registry.parent.mkdir()
        registry.write_text("""\
dependencies:
  pydantic:
    rationale: "Structured validation"
    modules: ["yamlgraph/models/"]
    added: "0.1.0"
""")

        with patch.object(
            dependency_rationale.sys, "argv", ["dep_rationale.py", "--detail"]
        ):
            original_file = dependency_rationale.__file__
            try:
                dependency_rationale.__file__ = str(
                    tmp_path / "scripts" / "dependency_rationale.py"
                )
                dependency_rationale.main()
            finally:
                dependency_rationale.__file__ = original_file

        captured = capsys.readouterr()
        assert "pydantic" in captured.out
        assert "Structured validation" in captured.out
