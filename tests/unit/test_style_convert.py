"""Tests for FR-764: Style-Convert Pipeline (examples/style_convert).

Validates the sibling example to image_pipeline: it loads an existing prompt
file (one prompt per nonblank line), restyles each prompt to a target art style
via a Mistral-pinned map node with a structured prompt_text schema, and reuses
image_pipeline's save_prompts_node unchanged.

Frozen by judgement 2026-07-28 (APPROVED WITH REVISIONS). All test functions are
tagged REQ-YG-573 (CAP-215).

TDD: Red-Green-Refactor.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GRAPH_DIR = REPO_ROOT / "examples" / "style_convert"
GRAPH_FILE = GRAPH_DIR / "graph.yaml"
PROMPTS_DIR = GRAPH_DIR / "prompts"
NODES_DIR = GRAPH_DIR / "nodes"
README_FILE = GRAPH_DIR / "README.md"

IMAGE_PIPELINE_SAVE_MODULE = "examples.image_pipeline.nodes.save_prompts"


def _read(path: Path) -> str:
    return path.read_text()


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


# ---------------------------------------------------------------------------
# 1. File existence (D-3..D-7)
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-573")
class TestStyleConvertFileStructure:
    def test_graph_file_exists(self):
        assert GRAPH_FILE.exists(), "examples/style_convert/graph.yaml must exist"

    def test_convert_style_prompt_exists(self):
        assert (PROMPTS_DIR / "convert_style.yaml").exists()

    def test_load_prompts_node_exists(self):
        assert (NODES_DIR / "load_prompts.py").exists()

    def test_nodes_init_exists(self):
        assert (NODES_DIR / "__init__.py").exists()

    def test_readme_exists(self):
        assert README_FILE.exists()


# ---------------------------------------------------------------------------
# 2. Graph structure (AC-03)
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-573")
class TestStyleConvertGraphStructure:
    def test_prompts_relative_true(self):
        graph = _load_yaml(GRAPH_FILE)
        assert graph.get("prompts_relative") is True

    def test_state_declares_required_keys(self):
        graph = _load_yaml(GRAPH_FILE)
        state = graph["state"]
        for key in (
            "input_file",
            "target_style",
            "prompts",
            "prompt_file",
            "output_dir",
        ):
            assert key in state, f"state must declare '{key}'"

    def test_has_three_pipeline_nodes(self):
        graph = _load_yaml(GRAPH_FILE)
        nodes = graph["nodes"]
        assert "load_prompts" in nodes
        assert "convert_styles" in nodes
        assert "save_prompts" in nodes

    def test_load_prompts_is_python(self):
        graph = _load_yaml(GRAPH_FILE)
        assert graph["nodes"]["load_prompts"]["type"] == "python"

    def test_convert_styles_is_map(self):
        graph = _load_yaml(GRAPH_FILE)
        assert graph["nodes"]["convert_styles"]["type"] == "map"

    def test_convert_styles_collects_prompts(self):
        graph = _load_yaml(GRAPH_FILE)
        assert graph["nodes"]["convert_styles"]["collect"] == "prompts"

    def test_convert_styles_has_no_on_error_skip(self):
        # C-4: no partial-output policy.
        graph = _load_yaml(GRAPH_FILE)
        assert graph["nodes"]["convert_styles"].get("on_error") != "skip"

    def test_save_prompts_reuses_image_pipeline_node(self):
        # AC-03 / C-3: import the existing save_prompts_node unchanged.
        graph = _load_yaml(GRAPH_FILE)
        tool = graph["tools"]["save_prompts"]
        assert tool["module"] == IMAGE_PIPELINE_SAVE_MODULE
        assert tool["function"] == "save_prompts_node"

    def test_pipeline_edges(self):
        graph = _load_yaml(GRAPH_FILE)
        edges = {(e["from"], e["to"]) for e in graph["edges"]}
        assert ("START", "load_prompts") in edges
        assert ("load_prompts", "convert_styles") in edges
        assert ("convert_styles", "save_prompts") in edges
        assert ("save_prompts", "END") in edges


# ---------------------------------------------------------------------------
# 3. Lint (AC-04)
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-573")
class TestStyleConvertLint:
    def test_graph_passes_lint(self):
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(GRAPH_FILE)
        errors = [i for i in result.issues if i.severity == "error"]
        assert len(errors) == 0, f"Lint errors: {[(e.code, e.message) for e in errors]}"


# ---------------------------------------------------------------------------
# 4. Prompt schema / Mistral metadata (AC-07)
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-573")
class TestStyleConvertPrompt:
    def test_provider_is_mistral(self):
        prompt = _load_yaml(PROMPTS_DIR / "convert_style.yaml")
        assert prompt["metadata"]["provider"] == "mistral"

    def test_schema_has_prompt_text_str(self):
        prompt = _load_yaml(PROMPTS_DIR / "convert_style.yaml")
        fields = prompt["schema"]["fields"]
        assert "prompt_text" in fields
        assert fields["prompt_text"]["type"] == "str"

    def test_prompt_references_map_variables(self):
        content = _read(PROMPTS_DIR / "convert_style.yaml")
        assert "prompt_text" in content
        assert "target_style" in content

    def test_prompt_instructs_preservation(self):
        content = _read(PROMPTS_DIR / "convert_style.yaml").lower()
        # Preserve subject/composition/pose/action; replace only style/medium.
        for token in ("subject", "composition", "pose", "action"):
            assert token in content, f"prompt must mention preserving '{token}'"


# ---------------------------------------------------------------------------
# 5. load_prompts_node contract (AC-05, AC-06)
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-573")
class TestLoadPromptsNode:
    def _node(self):
        from examples.style_convert.nodes.load_prompts import load_prompts_node

        return load_prompts_node

    def test_returns_prompts_key(self, tmp_path):
        f = tmp_path / "in.txt"
        f.write_text("A cat on a wall\nA dog in a field\n")
        result = self._node()({"input_file": str(f)})
        assert result["prompts"] == ["A cat on a wall", "A dog in a field"]

    def test_strips_leading_enumerator(self, tmp_path):
        f = tmp_path / "in.txt"
        f.write_text("1. A cat\n2. A dog\n10. A bird\n")
        result = self._node()({"input_file": str(f)})
        assert result["prompts"] == ["A cat", "A dog", "A bird"]

    def test_preserves_internal_enumerator_and_text(self, tmp_path):
        f = tmp_path / "in.txt"
        f.write_text("3. cat, 3.5 ratio, step 2. of 4\n")
        result = self._node()({"input_file": str(f)})
        assert result["prompts"] == ["cat, 3.5 ratio, step 2. of 4"]

    def test_skips_blank_lines(self, tmp_path):
        f = tmp_path / "in.txt"
        f.write_text("A cat\n\n   \nA dog\n")
        result = self._node()({"input_file": str(f)})
        assert result["prompts"] == ["A cat", "A dog"]

    def test_missing_file_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError):
            self._node()({"input_file": str(tmp_path / "nope.txt")})

    def test_empty_file_raises_value_error(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("   \n\n")
        with pytest.raises(ValueError):
            self._node()({"input_file": str(f)})

    def test_does_not_mutate_source_file(self, tmp_path):
        # AC-06 / C-5: loading never writes the input.
        f = tmp_path / "in.txt"
        original = "1. A cat\n2. A dog\n"
        f.write_text(original)
        before = f.read_bytes()
        self._node()({"input_file": str(f)})
        assert f.read_bytes() == before


# ---------------------------------------------------------------------------
# 6. Map-output compatibility with reused save_prompts_node (AC-08, AC-09)
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-573")
class TestMapOutputCompatibility:
    """Exercise the real map reducer machinery (no core changes) and prove the
    collected entries are compatible with the unchanged save_prompts_node."""

    class _FakeConverted:
        """Stands in for the Pydantic model the LLM sub-node returns."""

        def __init__(self, prompt_text: str):
            self._pt = prompt_text

        def model_dump(self) -> dict:
            return {"prompt_text": self._pt}

    def _reduce(self, texts: list[str]) -> list[dict]:
        from yamlgraph.compile.map_compiler import wrap_for_reducer

        collected: list[dict] = []
        for i, t in enumerate(texts):

            def node_fn(state, _t=t):
                return {"converted_one": self._FakeConverted(f"{_t} :: styled")}

            wrapped = wrap_for_reducer(
                node_fn, "prompts", "converted_one", flatten_output=True
            )
            out = wrapped({"_map_index": i})
            collected.extend(out["prompts"])
        return collected

    def test_reducer_yields_prompt_text_dicts(self):
        collected = self._reduce(["a", "b"])
        assert all("prompt_text" in e for e in collected)
        assert [e["prompt_text"] for e in collected] == ["a :: styled", "b :: styled"]

    def test_saved_file_has_prompt_lines_not_dicts(self, tmp_path):
        from examples.image_pipeline.nodes.save_prompts import save_prompts_node

        collected = self._reduce(["cat", "dog", "bird"])
        with patch(
            "examples.image_pipeline.nodes.save_prompts.OUTPUT_BASE",
            tmp_path / "outputs",
        ):
            result = save_prompts_node({"prompts": collected})
        lines = Path(result["prompt_file"]).read_text().splitlines()
        assert lines == ["cat :: styled", "dog :: styled", "bird :: styled"]
        # No stringified dicts leaked into the file.
        assert not any("prompt_text" in ln or "_map_index" in ln for ln in lines)

    def test_count_preserved_n_in_n_out(self, tmp_path):
        from examples.image_pipeline.nodes.save_prompts import save_prompts_node

        texts = [f"prompt {i}" for i in range(7)]
        collected = self._reduce(texts)
        with patch(
            "examples.image_pipeline.nodes.save_prompts.OUTPUT_BASE",
            tmp_path / "outputs",
        ):
            result = save_prompts_node({"prompts": collected})
        lines = Path(result["prompt_file"]).read_text().splitlines()
        assert len(lines) == len(texts)


# ---------------------------------------------------------------------------
# 7. Failure path: surface error, never silently drop (AC-10)
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-573")
class TestFailurePathSurfacesError:
    def test_failed_branch_surfaces_error_and_is_retained(self):
        from yamlgraph.compile.map_compiler import wrap_for_reducer

        def failing_node(state):
            raise RuntimeError("mistral rejected the prompt")

        wrapped = wrap_for_reducer(
            failing_node, "prompts", "converted_one", flatten_output=True
        )
        out = wrapped({"_map_index": 2})

        # Error surfaces on the errors channel (not swallowed).
        assert out.get("errors"), "branch failure must surface on state.errors"
        # The failed branch is retained as an error entry — not silently dropped.
        entries = out["prompts"]
        assert len(entries) == 1
        assert entries[0].get("_error"), "failed entry must carry _error marker"
        assert (
            "prompt_text" not in entries[0]
        ), "a failed branch must not masquerade as a converted prompt"
