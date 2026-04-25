"""Tests for FR-109: Batch Image Prompt Generation Graph.

Validates that the batch image prompt graph exists with decompose → enrich (map)
pipeline, prompts have proper schemas, and the graph passes lint.

TDD: Red-Green-Refactor approach.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GRAPH_DIR = REPO_ROOT / "examples" / "batch_image_prompts"
GRAPH_FILE = GRAPH_DIR / "graph.yaml"
PROMPTS_DIR = GRAPH_DIR / "prompts"
README_FILE = GRAPH_DIR / "README.md"


def _read(path: Path) -> str:
    return path.read_text()


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


# ---------------------------------------------------------------------------
# 1. File existence tests
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-003")
class TestBatchImagePromptsFileStructure:
    """Example directory contains all required files."""

    def test_graph_file_exists(self):
        assert GRAPH_FILE.exists(), "examples/batch_image_prompts/graph.yaml must exist"

    def test_decompose_prompt_exists(self):
        prompt = PROMPTS_DIR / "decompose_concept.yaml"
        assert prompt.exists(), "prompts/decompose_concept.yaml must exist"

    def test_enrich_prompt_exists(self):
        prompt = PROMPTS_DIR / "enrich_prompt.yaml"
        assert prompt.exists(), "prompts/enrich_prompt.yaml must exist"

    def test_readme_exists(self):
        assert README_FILE.exists(), "examples/batch_image_prompts/README.md must exist"


# ---------------------------------------------------------------------------
# 2. Graph structure tests
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-003")
class TestBatchImagePromptsGraphStructure:
    """Graph YAML defines the correct pipeline structure."""

    def test_graph_has_decompose_node(self):
        content = _read(GRAPH_FILE)
        assert "decompose:" in content, "Graph must have a decompose node"

    def test_graph_has_enrich_map_node(self):
        content = _read(GRAPH_FILE)
        assert "enrich:" in content, "Graph must have an enrich node"

    def test_enrich_node_is_map_type(self):
        graph = _load_yaml(GRAPH_FILE)
        enrich = graph["nodes"]["enrich"]
        assert enrich["type"] == "map", "enrich node must be type: map"

    def test_decompose_node_is_llm_type(self):
        graph = _load_yaml(GRAPH_FILE)
        decompose = graph["nodes"]["decompose"]
        assert decompose["type"] == "llm", "decompose node must be type: llm"

    def test_graph_edges_form_pipeline(self):
        """Edges: START → decompose → enrich → END."""
        graph = _load_yaml(GRAPH_FILE)
        edges = graph["edges"]
        edge_pairs = [(e["from"], e["to"]) for e in edges]
        assert ("START", "decompose") in edge_pairs, "Missing START → decompose edge"
        assert ("decompose", "enrich") in edge_pairs, "Missing decompose → enrich edge"
        assert ("enrich", "END") in edge_pairs, "Missing enrich → END edge"

    def test_graph_state_declares_required_fields(self):
        """State must declare concept, style, count, scenes, prompts."""
        graph = _load_yaml(GRAPH_FILE)
        state = graph.get("state", {})
        for field in ("concept", "style", "count", "scenes", "prompts"):
            assert field in state, f"State must declare '{field}' field"

    def test_enrich_map_over_scenes_briefs(self):
        """Map node iterates over decomposed scene briefs."""
        graph = _load_yaml(GRAPH_FILE)
        enrich = graph["nodes"]["enrich"]
        assert "scenes" in enrich.get("over", ""), "enrich.over must reference scenes"
        assert "briefs" in enrich.get("over", ""), "enrich.over must reference briefs"

    def test_enrich_has_flatten_output(self):
        graph = _load_yaml(GRAPH_FILE)
        enrich = graph["nodes"]["enrich"]
        assert enrich.get("flatten_output") is True, (
            "enrich must have flatten_output: true"
        )

    def test_enrich_has_on_error_skip(self):
        graph = _load_yaml(GRAPH_FILE)
        enrich = graph["nodes"]["enrich"]
        assert enrich.get("on_error") == "skip", "enrich must have on_error: skip"

    def test_enrich_collects_to_prompts(self):
        graph = _load_yaml(GRAPH_FILE)
        enrich = graph["nodes"]["enrich"]
        assert enrich.get("collect") == "prompts", "enrich must collect to 'prompts'"


# ---------------------------------------------------------------------------
# 3. Prompt schema tests
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-003")
class TestBatchImagePromptsPromptSchemas:
    """Prompts define proper inline schemas for structured output."""

    def test_decompose_prompt_has_schema(self):
        prompt = _load_yaml(PROMPTS_DIR / "decompose_concept.yaml")
        assert "schema" in prompt, "decompose_concept prompt must have a schema"

    def test_decompose_schema_has_briefs_field(self):
        prompt = _load_yaml(PROMPTS_DIR / "decompose_concept.yaml")
        fields = prompt["schema"]["fields"]
        assert "briefs" in fields, "Schema must have 'briefs' field"
        assert "list" in fields["briefs"]["type"], "briefs must be a list type"

    def test_enrich_prompt_has_schema(self):
        prompt = _load_yaml(PROMPTS_DIR / "enrich_prompt.yaml")
        assert "schema" in prompt, "enrich_prompt prompt must have a schema"

    def test_enrich_schema_has_prompt_text_field(self):
        prompt = _load_yaml(PROMPTS_DIR / "enrich_prompt.yaml")
        fields = prompt["schema"]["fields"]
        assert "prompt_text" in fields, "Schema must have 'prompt_text' field"
        assert fields["prompt_text"]["type"] == "str", "prompt_text must be str type"

    def test_decompose_prompt_uses_jinja2(self):
        """Decompose prompt uses Jinja2 for count default."""
        content = _read(PROMPTS_DIR / "decompose_concept.yaml")
        assert "{{" in content or "{%" in content, (
            "Decompose prompt should use Jinja2 syntax"
        )

    def test_enrich_prompt_references_brief_variable(self):
        """Enrich prompt must use the 'brief' variable from map iteration."""
        content = _read(PROMPTS_DIR / "enrich_prompt.yaml")
        assert "brief" in content, "Enrich prompt must reference 'brief' variable"


# ---------------------------------------------------------------------------
# 4. Lint validation
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-003")
class TestBatchImagePromptsLint:
    """Graph passes yamlgraph lint with no errors."""

    def test_graph_passes_lint(self):
        """examples/batch_image_prompts/graph.yaml passes yamlgraph graph lint."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(GRAPH_FILE)
        errors = [i for i in result.issues if i.severity == "error"]
        assert len(errors) == 0, (
            f"Graph lint errors: {[f'{e.code}: {e.message}' for e in errors]}"
        )
