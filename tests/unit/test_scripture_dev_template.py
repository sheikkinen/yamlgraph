"""Tests for FR-207: Standalone Scripture Methodology Repository.

Validates:
  - scripture.yaml parameterizes all project-specific values
  - render.sh reads scripture.yaml and applies sed substitutions from _templates/
  - Rendered Scripture contains zero YAMLGraph-specific references
  - aggregate_changelog.sh generates CHANGELOG.md from fragments without Python
  - req_coverage.py works with --prefix flag
  - Knowledge graph template is valid YAML with governance structure
  - Re-rendering from _templates/ after config change works correctly
"""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTURE_DEV = REPO_ROOT / "projects" / "scripture-dev"

# YAMLGraph-specific terms that must NOT appear in rendered output
FORBIDDEN_TERMS = [
    "yamlgraph",
    "YAMLGraph",
    "LangGraph",
    "LangSmith",
    "Pydantic",
    "REQ-YG",
    "langchain",
    "LangChain",
]


# ---------------------------------------------------------------------------
# Tier 1 — Core: Template Structure
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-201")
class TestScriptureYaml:
    """scripture.yaml parameterizes all project-specific values."""

    def test_scripture_yaml_exists(self) -> None:
        """scripture.yaml must exist in scripture-dev root."""
        assert (SCRIPTURE_DEV / "scripture.yaml").is_file()

    def test_scripture_yaml_valid(self) -> None:
        """scripture.yaml must be valid YAML."""
        data = yaml.safe_load((SCRIPTURE_DEV / "scripture.yaml").read_text())
        assert isinstance(data, dict)

    def test_scripture_yaml_required_keys(self) -> None:
        """scripture.yaml must contain all required configuration keys."""
        data = yaml.safe_load((SCRIPTURE_DEV / "scripture.yaml").read_text())
        required_keys = [
            "project_name",
            "req_prefix",
            "fr_prefix",
            "max_file_lines",
            "max_complexity",
            "coverage_threshold",
        ]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

    def test_scripture_yaml_default_values(self) -> None:
        """scripture.yaml defaults match FR specification."""
        data = yaml.safe_load((SCRIPTURE_DEV / "scripture.yaml").read_text())
        assert data["req_prefix"] == "REQ"
        assert data["fr_prefix"] == "FR"
        assert data["max_file_lines"] == 450
        assert data["max_complexity"] == 21
        assert data["coverage_threshold"] == 80


@pytest.mark.req("REQ-YG-201")
class TestRenderScript:
    """render.sh reads scripture.yaml and applies sed substitutions."""

    def test_render_sh_exists(self) -> None:
        """render.sh must exist and be executable."""
        render_sh = SCRIPTURE_DEV / "render.sh"
        assert render_sh.is_file()
        assert os.access(render_sh, os.X_OK)

    def test_templates_directory_exists(self) -> None:
        """_templates/ directory must exist as source for rendering."""
        assert (SCRIPTURE_DEV / "_templates").is_dir()

    def test_templates_contain_placeholders(self) -> None:
        """Template files in _templates/ must contain __PLACEHOLDER__ markers."""
        templates_dir = SCRIPTURE_DEV / "_templates"
        template_files = list(templates_dir.rglob("*"))
        template_files = [f for f in template_files if f.is_file()]
        assert len(template_files) > 0, "No template files found"

        placeholder_found = False
        for f in template_files:
            content = f.read_text()
            if "__REQ_PREFIX__" in content or "__PROJECT_NAME__" in content:
                placeholder_found = True
                break
        assert placeholder_found, "No __PLACEHOLDER__ markers found in templates"

    def test_render_produces_output(self, tmp_path: Path) -> None:
        """Running render.sh produces rendered files without placeholders."""
        _copy_scripture_dev(tmp_path)
        _run_render(tmp_path)

        # Check that copilot-instructions.md has been rendered
        rendered = (tmp_path / ".github" / "copilot-instructions.md").read_text()
        assert "__REQ_PREFIX__" not in rendered
        assert "__FR_PREFIX__" not in rendered
        assert "__PROJECT_NAME__" not in rendered
        assert "__MAX_FILE_LINES__" not in rendered
        assert "__MAX_COMPLEXITY__" not in rendered
        assert "__COVERAGE_THRESHOLD__" not in rendered

    def test_render_substitutes_values(self, tmp_path: Path) -> None:
        """Rendered output contains actual values from scripture.yaml."""
        _copy_scripture_dev(tmp_path)
        _run_render(tmp_path)

        rendered = (tmp_path / ".github" / "copilot-instructions.md").read_text()
        # Default values from scripture.yaml
        assert "REQ-" in rendered, "req_prefix substitution missing"
        assert "FR-" in rendered, "fr_prefix substitution missing"

    def test_re_render_with_changed_config(self, tmp_path: Path) -> None:
        """Changing config and re-running render.sh updates output."""
        _copy_scripture_dev(tmp_path)
        _run_render(tmp_path)

        # Change scripture.yaml
        config_path = tmp_path / "scripture.yaml"
        config = yaml.safe_load(config_path.read_text())
        config["req_prefix"] = "REQ-FOO"
        config["project_name"] = "changed-project"
        config_path.write_text(yaml.dump(config, default_flow_style=False))

        # Re-render
        _run_render(tmp_path)

        rendered = (tmp_path / ".github" / "copilot-instructions.md").read_text()
        assert "REQ-FOO-" in rendered, "New req_prefix not applied"
        assert "REQ-" not in rendered.replace(
            "REQ-FOO", ""
        ), "Old REQ- prefix still present after re-render"


# ---------------------------------------------------------------------------
# Tier 1 — Core: Framework-Agnostic Scripture
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-202")
class TestFrameworkAgnostic:
    """Rendered Scripture contains zero YAMLGraph-specific references."""

    def test_copilot_instructions_no_yamlgraph_refs(self, tmp_path: Path) -> None:
        """Rendered copilot-instructions.md has no framework-specific terms."""
        _copy_scripture_dev(tmp_path)
        _run_render(tmp_path)

        rendered = (tmp_path / ".github" / "copilot-instructions.md").read_text()
        for term in FORBIDDEN_TERMS:
            assert (
                term not in rendered
            ), f"Forbidden term '{term}' found in rendered copilot-instructions.md"

    def test_precommit_config_no_yamlgraph_refs(self, tmp_path: Path) -> None:
        """Rendered .pre-commit-config.yaml has no framework-specific terms."""
        _copy_scripture_dev(tmp_path)
        _run_render(tmp_path)

        rendered = (tmp_path / ".pre-commit-config.yaml").read_text()
        for term in FORBIDDEN_TERMS:
            assert (
                term not in rendered
            ), f"Forbidden term '{term}' found in rendered .pre-commit-config.yaml"

    def test_hooks_no_yamlgraph_refs(self, tmp_path: Path) -> None:
        """Hook scripts have no framework-specific terms."""
        _copy_scripture_dev(tmp_path)
        _run_render(tmp_path)

        hooks_dir = tmp_path / "hooks"
        if hooks_dir.is_dir():
            for hook in hooks_dir.glob("*.sh"):
                content = hook.read_text()
                for term in FORBIDDEN_TERMS:
                    assert (
                        term not in content
                    ), f"Forbidden term '{term}' found in {hook.name}"

    def test_no_yamlgraph_specific_hooks(self, tmp_path: Path) -> None:
        """Pre-commit config must not include YAMLGraph-specific hooks."""
        _copy_scripture_dev(tmp_path)
        _run_render(tmp_path)

        yamlgraph_hooks = [
            "inline-llm-check",
            "validate-capabilities",
            "validate-id-registry",
            "hedging-check",
            "noqa-confession",
            "demo-proof-check",
            "absolution",
            "inquisitor-background",
        ]
        rendered = (tmp_path / ".pre-commit-config.yaml").read_text()
        for hook in yamlgraph_hooks:
            assert (
                hook not in rendered
            ), f"YAMLGraph-specific hook '{hook}' must not be in template"


# ---------------------------------------------------------------------------
# Tier 1 — Core: Directory Structure
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-201")
class TestDirectoryStructure:
    """Scripture-dev has correct directory layout."""

    def test_diary_directory(self) -> None:
        """docs/diary/.gitkeep must exist."""
        assert (SCRIPTURE_DEV / "docs" / "diary" / ".gitkeep").exists()

    def test_changelog_unreleased_directory(self) -> None:
        """changelog/unreleased/.gitkeep must exist."""
        assert (SCRIPTURE_DEV / "changelog" / "unreleased" / ".gitkeep").exists()

    def test_changelog_readme(self) -> None:
        """changelog/README.md must document fragment format."""
        readme = SCRIPTURE_DEV / "changelog" / "README.md"
        assert readme.is_file()
        content = readme.read_text()
        assert "fragment" in content.lower() or "type:" in content

    def test_hooks_directory(self) -> None:
        """hooks/ directory must exist with shell scripts."""
        hooks_dir = SCRIPTURE_DEV / "hooks"
        assert hooks_dir.is_dir()
        sh_files = list(hooks_dir.glob("*.sh"))
        assert len(sh_files) >= 3, "Expected at least 3 hook scripts"

    def test_templates_directory_with_entries(self) -> None:
        """templates/ directory must contain diary, FR, and knowledge graph templates."""
        templates_dir = SCRIPTURE_DEV / "templates"
        assert templates_dir.is_dir()
        assert (templates_dir / "diary-entry.md").is_file()
        assert (templates_dir / "feature-request.md").is_file()
        assert (templates_dir / "knowledge-graph.yaml").is_file()

    def test_readme_exists(self) -> None:
        """README.md must exist with adoption guide."""
        readme = SCRIPTURE_DEV / "README.md"
        assert readme.is_file()
        content = readme.read_text()
        assert "render.sh" in content
        assert "scripture.yaml" in content

    def test_license_exists(self) -> None:
        """LICENSE must exist."""
        assert (SCRIPTURE_DEV / "LICENSE").is_file()


# ---------------------------------------------------------------------------
# Tier 1 — Core: Shell Changelog Aggregator
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-203")
class TestShellChangelogAggregator:
    """aggregate_changelog.sh generates CHANGELOG.md from fragments."""

    def test_script_exists_and_executable(self) -> None:
        """aggregate_changelog.sh must exist and be executable."""
        script = SCRIPTURE_DEV / "scripts" / "aggregate_changelog.sh"
        assert script.is_file()
        assert os.access(script, os.X_OK)

    def test_generates_changelog_from_fragments(self, tmp_path: Path) -> None:
        """Script reads fragments and produces grouped output."""
        _copy_scripture_dev(tmp_path)

        # Create test fragments
        unreleased = tmp_path / "changelog" / "unreleased"
        unreleased.mkdir(parents=True, exist_ok=True)
        (unreleased / "FR-001-test-feat.md").write_text(
            textwrap.dedent("""\
            ---
            type: feat
            scope: core
            ---
            - **FR-001 Test Feature**: Added a test feature.
        """)
        )
        (unreleased / "FR-002-test-fix.md").write_text(
            textwrap.dedent("""\
            ---
            type: fix
            scope: cli
            ---
            - **FR-002 Test Fix**: Fixed a test bug.
        """)
        )

        result = subprocess.run(
            ["bash", str(tmp_path / "scripts" / "aggregate_changelog.sh")],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        output = result.stdout
        assert "Added" in output
        assert "Fixed" in output
        assert "FR-001" in output
        assert "FR-002" in output

    def test_no_python_dependency(self) -> None:
        """aggregate_changelog.sh must not require Python."""
        script = SCRIPTURE_DEV / "scripts" / "aggregate_changelog.sh"
        content = script.read_text()
        assert "python" not in content.lower(), "Shell script must not invoke Python"


# ---------------------------------------------------------------------------
# Tier 2 — Extended: CI Workflows
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-201")
class TestCIWorkflows:
    """CI workflow templates for commitlint and security."""

    def test_commitlint_workflow_exists(self) -> None:
        """commitlint.yml must exist in _templates/.github/workflows/."""
        assert (
            SCRIPTURE_DEV / "_templates" / ".github" / "workflows" / "commitlint.yml"
        ).is_file()

    def test_security_workflow_exists(self) -> None:
        """security.yml must exist in _templates/.github/workflows/."""
        assert (
            SCRIPTURE_DEV / "_templates" / ".github" / "workflows" / "security.yml"
        ).is_file()

    def test_rendered_commitlint_has_gates(self, tmp_path: Path) -> None:
        """Rendered commitlint.yml includes changelog-gate and diary-gate."""
        _copy_scripture_dev(tmp_path)
        _run_render(tmp_path)

        workflow = (tmp_path / ".github" / "workflows" / "commitlint.yml").read_text()
        assert "changelog" in workflow.lower()
        assert "diary" in workflow.lower()


# ---------------------------------------------------------------------------
# Tier 2 — Extended: Configurable Req Coverage
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-204")
class TestReqCoveragePrefix:
    """req_coverage.py supports --prefix flag for configurable traceability."""

    def test_req_coverage_script_exists(self) -> None:
        """scripts/req_coverage.py must exist in scripture-dev."""
        assert (SCRIPTURE_DEV / "scripts" / "req_coverage.py").is_file()

    def test_no_yamlgraph_imports(self) -> None:
        """req_coverage.py must not import YAMLGraph modules."""
        content = (SCRIPTURE_DEV / "scripts" / "req_coverage.py").read_text()
        assert "import yamlgraph" not in content
        assert "from yamlgraph" not in content

    def test_supports_prefix_flag(self) -> None:
        """Script must accept --prefix argument."""
        content = (SCRIPTURE_DEV / "scripts" / "req_coverage.py").read_text()
        assert "--prefix" in content

    def test_default_prefix_is_req(self) -> None:
        """Default prefix must be REQ (not REQ-YG)."""
        content = (SCRIPTURE_DEV / "scripts" / "req_coverage.py").read_text()
        # Should have REQ as default, not REQ-YG
        assert "REQ-YG" not in content, "Script must not hardcode REQ-YG prefix"


# ---------------------------------------------------------------------------
# Tier 2 — Extended: Knowledge Graph Template
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-205")
class TestKnowledgeGraphTemplate:
    """Knowledge graph template provides empty governance structure."""

    def test_knowledge_graph_valid_yaml(self) -> None:
        """templates/knowledge-graph.yaml must be valid YAML."""
        kg_path = SCRIPTURE_DEV / "templates" / "knowledge-graph.yaml"
        data = yaml.safe_load(kg_path.read_text())
        assert isinstance(data, dict)

    def test_knowledge_graph_has_sections(self) -> None:
        """Knowledge graph must have boundaries, traps, cures, process, seeds."""
        kg_path = SCRIPTURE_DEV / "templates" / "knowledge-graph.yaml"
        data = yaml.safe_load(kg_path.read_text())
        required_sections = ["boundaries", "traps", "cures", "process", "seeds"]
        for section in required_sections:
            assert section in data, f"Missing section: {section}"


# ---------------------------------------------------------------------------
# Tier 2 — Extended: Python Changelog Aggregator
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-203")
class TestPythonChangelogAggregator:
    """aggregate_changelog.py for full Keep a Changelog output."""

    def test_script_exists(self) -> None:
        """scripts/aggregate_changelog.py must exist."""
        assert (SCRIPTURE_DEV / "scripts" / "aggregate_changelog.py").is_file()

    def test_no_yamlgraph_imports(self) -> None:
        """aggregate_changelog.py must not import YAMLGraph modules."""
        content = (SCRIPTURE_DEV / "scripts" / "aggregate_changelog.py").read_text()
        assert "import yamlgraph" not in content
        assert "from yamlgraph" not in content


# ---------------------------------------------------------------------------
# Tier 1 — Smoke Test: End-to-End
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-201")
class TestSmokeTest:
    """End-to-end: fresh copy → render → verify structure."""

    def test_full_render_pipeline(self, tmp_path: Path) -> None:
        """Smoke: copy template → render.sh → all files valid, no placeholders."""
        _copy_scripture_dev(tmp_path)
        _run_render(tmp_path)

        # All rendered files should have no leftover placeholders
        placeholders = [
            "__REQ_PREFIX__",
            "__FR_PREFIX__",
            "__PROJECT_NAME__",
            "__MAX_FILE_LINES__",
            "__MAX_COMPLEXITY__",
            "__COVERAGE_THRESHOLD__",
        ]

        for f in tmp_path.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix in (".pyc", ".so", ".whl"):
                continue
            if ".git" in str(f):
                continue
            try:
                content = f.read_text()
            except UnicodeDecodeError:
                continue
            # _templates/ dir should retain placeholders (source truth)
            if "_templates" in str(f):
                continue
            # render.sh itself contains placeholder strings as sed operands
            if f.name == "render.sh":
                continue
            for ph in placeholders:
                assert (
                    ph not in content
                ), f"Leftover placeholder {ph} in {f.relative_to(tmp_path)}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _copy_scripture_dev(dest: Path) -> None:
    """Copy scripture-dev project to a temp directory for isolated testing."""
    import shutil

    src = SCRIPTURE_DEV
    # Copy everything except .git
    for item in src.iterdir():
        if item.name == ".git":
            continue
        dst = dest / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)


def _run_render(workdir: Path) -> subprocess.CompletedProcess:
    """Run render.sh in the given directory."""
    result = subprocess.run(
        ["bash", str(workdir / "render.sh")],
        capture_output=True,
        text=True,
        cwd=str(workdir),
    )
    assert result.returncode == 0, f"render.sh failed: {result.stderr}"
    return result
