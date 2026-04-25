"""Tests for FR-249: Guardrails Pattern Documentation.

Verifies that reference/patterns.md includes Pattern 11 (Input Guardrails)
documenting the echo → validate → respond pipeline, and that
examples/README.md lists guardrails in the "By Feature" section.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PATTERNS_MD = REPO_ROOT / "reference" / "patterns.md"
EXAMPLES_README = REPO_ROOT / "examples" / "README.md"


# ---------------------------------------------------------------------------
# AC-1: Pattern 11 heading exists in patterns.md
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-254")
class TestGuardrailsPatternExists:
    """Verify Pattern 11 exists with correct heading."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = PATTERNS_MD.read_text()

    def test_pattern_11_heading(self):
        assert "## Pattern 11: Input Guardrails" in self.content, (
            "patterns.md must have '## Pattern 11: Input Guardrails' heading"
        )

    def test_pattern_11_between_10_and_12(self):
        """Pattern 11 must appear between Pattern 10 and Pattern 12."""
        pos_10 = self.content.index("## Pattern 10:")
        pos_11 = self.content.index("## Pattern 11:")
        pos_12 = self.content.index("## Pattern 12:")
        assert pos_10 < pos_11 < pos_12, (
            "Pattern 11 must be between Pattern 10 and Pattern 12"
        )


# ---------------------------------------------------------------------------
# AC-2: Pattern has required sections
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-254")
class TestGuardrailsPatternSections:
    """Verify Pattern 11 contains all required sections."""

    @pytest.fixture(autouse=True)
    def _load(self):
        content = PATTERNS_MD.read_text()
        # Extract Pattern 11 section (between Pattern 11 heading and Pattern 12)
        start = content.index("## Pattern 11:")
        end = content.index("## Pattern 12:")
        self.section = content[start:end]

    def test_has_problem_section(self):
        assert "### Problem" in self.section, "Pattern 11 must have a Problem section"

    def test_has_solution_section(self):
        assert "### Solution" in self.section, "Pattern 11 must have a Solution section"

    def test_has_graph_structure(self):
        assert "### Graph Structure" in self.section, (
            "Pattern 11 must have a Graph Structure section"
        )

    def test_has_python_tools(self):
        assert "### Python Tools" in self.section, (
            "Pattern 11 must have a Python Tools section"
        )

    def test_has_key_points(self):
        assert "### Key Points" in self.section, (
            "Pattern 11 must have a Key Points section"
        )


# ---------------------------------------------------------------------------
# AC-3: YAML example is valid
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-254")
class TestGuardrailsYamlValid:
    """Verify the YAML example in Pattern 11 is parseable."""

    @pytest.fixture(autouse=True)
    def _load(self):
        content = PATTERNS_MD.read_text()
        start = content.index("## Pattern 11:")
        end = content.index("## Pattern 12:")
        self.section = content[start:end]

    def test_yaml_example_is_valid(self):
        """Extract and parse the first YAML code block in Pattern 11."""
        # Find the first yaml code block
        yaml_start = self.section.index("```yaml") + len("```yaml")
        yaml_end = self.section.index("```", yaml_start)
        yaml_content = self.section[yaml_start:yaml_end]

        parsed = yaml.safe_load(yaml_content)
        assert parsed is not None, "YAML example must be parseable"
        assert "nodes" in parsed, "YAML example must have nodes"
        assert "edges" in parsed, "YAML example must have edges"

    def test_yaml_has_echo_validate_respond_nodes(self):
        """YAML must have echo, validate, and respond nodes."""
        yaml_start = self.section.index("```yaml") + len("```yaml")
        yaml_end = self.section.index("```", yaml_start)
        yaml_content = self.section[yaml_start:yaml_end]

        parsed = yaml.safe_load(yaml_content)
        nodes = parsed["nodes"]
        assert "echo" in nodes, "YAML must have echo node"
        assert "validate" in nodes, "YAML must have validate node"
        assert "respond" in nodes, "YAML must have respond node"

    def test_yaml_has_correct_edge_flow(self):
        """Edges must flow START → echo → validate → respond → END."""
        yaml_start = self.section.index("```yaml") + len("```yaml")
        yaml_end = self.section.index("```", yaml_start)
        yaml_content = self.section[yaml_start:yaml_end]

        parsed = yaml.safe_load(yaml_content)
        edges = parsed["edges"]
        edge_pairs = [(e["from"], e["to"]) for e in edges]

        assert ("START", "echo") in edge_pairs
        assert ("echo", "validate") in edge_pairs
        assert ("validate", "respond") in edge_pairs
        assert ("respond", "END") in edge_pairs


# ---------------------------------------------------------------------------
# AC-4: Pattern references openai_proxy example
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-254")
class TestGuardrailsReferences:
    """Verify Pattern 11 references the production example."""

    @pytest.fixture(autouse=True)
    def _load(self):
        content = PATTERNS_MD.read_text()
        start = content.index("## Pattern 11:")
        end = content.index("## Pattern 12:")
        self.section = content[start:end]

    def test_references_openai_proxy(self):
        assert "openai_proxy" in self.section, (
            "Pattern 11 must reference examples/openai_proxy/"
        )

    def test_references_validation_missing_stamp(self):
        assert "validation missing" in self.section, (
            "Pattern 11 must mention the *validation missing* stamp"
        )


# ---------------------------------------------------------------------------
# AC-5: examples/README.md includes guardrails in By Feature
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-254")
class TestExamplesReadmeGuardrails:
    """Verify examples/README.md lists guardrails in By Feature section."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = EXAMPLES_README.read_text()

    def test_guardrails_category_exists(self):
        assert "Guardrail" in self.content, (
            "examples/README.md must have a Guardrails category in By Feature"
        )

    def test_openai_proxy_in_guardrails(self):
        assert "openai_proxy" in self.content, (
            "examples/README.md must list openai_proxy under guardrails"
        )
