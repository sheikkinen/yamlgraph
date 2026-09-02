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
    return path.read_text(encoding="utf-8")


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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

    def test_has_pipeline_nodes(self):
        graph = _load_yaml(GRAPH_FILE)
        nodes = graph["nodes"]
        assert "load_prompts" in nodes
        assert "convert_styles" in nodes
        assert "validate_conversions" in nodes
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

    def test_convert_styles_maps_over_source_prompts(self):
        # collect: prompts must fan out over a DIFFERENT key than it collects
        # into, else the append-reducer doubles the count.
        graph = _load_yaml(GRAPH_FILE)
        over = graph["nodes"]["convert_styles"]["over"]
        assert "source_prompts" in over
        assert graph["nodes"]["load_prompts"]["state_key"] == "source_prompts"

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
        # Fail-fast gate sits between the map and the sink (R-3/C-4).
        assert ("convert_styles", "validate_conversions") in edges
        assert ("validate_conversions", "save_prompts") in edges
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
        # Provider is pinned on the graph map sub-node (the executor resolves
        # provider from node config, not prompt metadata).
        graph = _load_yaml(GRAPH_FILE)
        assert graph["nodes"]["convert_styles"]["node"]["provider"] == "mistral"

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

    def test_returns_source_prompts_key(self, tmp_path):
        # Loader writes source_prompts (not prompts) so the map's collect: prompts
        # target starts empty — reusing 'prompts' would double the count.
        f = tmp_path / "in.txt"
        f.write_text("A cat on a wall\nA dog in a field\n", encoding="utf-8")
        result = self._node()({"input_file": str(f)})
        assert result["source_prompts"] == ["A cat on a wall", "A dog in a field"]
        assert "prompts" not in result

    def test_strips_leading_enumerator(self, tmp_path):
        f = tmp_path / "in.txt"
        f.write_text("1. A cat\n2. A dog\n10. A bird\n", encoding="utf-8")
        result = self._node()({"input_file": str(f)})
        assert result["source_prompts"] == ["A cat", "A dog", "A bird"]

    def test_preserves_internal_enumerator_and_text(self, tmp_path):
        f = tmp_path / "in.txt"
        f.write_text("3. cat, 3.5 ratio, step 2. of 4\n", encoding="utf-8")
        result = self._node()({"input_file": str(f)})
        assert result["source_prompts"] == ["cat, 3.5 ratio, step 2. of 4"]

    def test_skips_blank_lines(self, tmp_path):
        f = tmp_path / "in.txt"
        f.write_text("A cat\n\n   \nA dog\n", encoding="utf-8")
        result = self._node()({"input_file": str(f)})
        assert result["source_prompts"] == ["A cat", "A dog"]

    def test_missing_file_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError):
            self._node()({"input_file": str(tmp_path / "nope.txt")})

    def test_empty_file_raises_value_error(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("   \n\n", encoding="utf-8")
        with pytest.raises(ValueError):
            self._node()({"input_file": str(f)})

    def test_does_not_mutate_source_file(self, tmp_path):
        # AC-06 / C-5: loading never writes the input.
        f = tmp_path / "in.txt"
        original = "1. A cat\n2. A dog\n"
        f.write_text(original, encoding="utf-8")
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
        lines = Path(result["prompt_file"]).read_text(encoding="utf-8").splitlines()
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
        lines = Path(result["prompt_file"]).read_text(encoding="utf-8").splitlines()
        assert len(lines) == len(texts)


# ---------------------------------------------------------------------------
# 7. Failure path: surface error, never silently drop (AC-10)
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-573")
class TestFailurePathSurfacesError:
    def test_failed_branch_surfaces_error_marker(self):
        from yamlgraph.compile.map_compiler import wrap_for_reducer

        def failing_node(state):
            raise RuntimeError("mistral rejected the prompt")

        wrapped = wrap_for_reducer(
            failing_node, "prompts", "converted_one", flatten_output=True
        )
        out = wrapped({"_map_index": 2})

        # Error surfaces on the errors channel (not swallowed).
        assert out.get("errors"), "branch failure must surface on state.errors"
        # The failed branch is collected as an _error marker — which the
        # validate_conversions gate then rejects (see end-to-end test below).
        entries = out["prompts"]
        assert len(entries) == 1
        assert entries[0].get("_error"), "failed entry must carry _error marker"
        assert (
            "prompt_text" not in entries[0]
        ), "a failed branch must not masquerade as a converted prompt"

    def test_validate_node_raises_on_error_marker(self):
        # R-3/C-4 unit: the gate rejects an _error marker before save runs.
        from examples.style_convert.nodes.validate_conversions import (
            validate_conversions_node,
        )

        state = {
            "source_prompts": ["a", "b"],
            "prompts": [
                {"_map_index": 0, "prompt_text": "a in style"},
                {"_map_index": 1, "_error": "boom", "_error_type": "RuntimeError"},
            ],
        }
        with pytest.raises(ValueError, match="conversions failed"):
            validate_conversions_node(state)

    def test_validate_node_raises_on_count_mismatch(self):
        from examples.style_convert.nodes.validate_conversions import (
            validate_conversions_node,
        )

        state = {
            "source_prompts": ["a", "b", "c"],
            "prompts": [{"_map_index": 0, "prompt_text": "a in style"}],
        }
        with pytest.raises(ValueError, match="does not match source"):
            validate_conversions_node(state)

    def test_validate_node_passes_when_all_succeed(self):
        from examples.style_convert.nodes.validate_conversions import (
            validate_conversions_node,
        )

        state = {
            "source_prompts": ["a", "b"],
            "prompts": [
                {"_map_index": 0, "prompt_text": "a in style"},
                {"_map_index": 1, "prompt_text": "b in style"},
            ],
        }
        assert validate_conversions_node(state) == {}


# ---------------------------------------------------------------------------
# 8. End-to-end graph run with mocked LLM (AC-08, AC-09) — catches the
#    count-doubling composition bug that reducer-only tests miss.
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-573")
class TestStyleConvertEndToEnd:
    """Compile and invoke the real graph with a mocked LLM (C-6: no live
    provider). Proves load -> map -> save composes without doubling the count
    and writes converted prompt lines, not stringified dicts."""

    class _FakeConverted:
        def __init__(self, prompt_text: str):
            self.prompt_text = prompt_text

        def model_dump(self) -> dict:
            return {"prompt_text": self.prompt_text}

    def _run(self, tmp_path, prompts_text: str, target_style: str = "waterhouse"):
        from unittest.mock import patch

        from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

        infile = tmp_path / "prompts_in.txt"
        infile.write_text(prompts_text, encoding="utf-8")

        def fake_execute(*args, **kwargs):
            variables = kwargs.get("variables", {})
            original = variables.get("prompt_text", "?")
            style = variables.get("target_style", "?")
            return self._FakeConverted(f"{original} in the style of {style}")

        config = load_graph_config(str(GRAPH_FILE))
        state_graph = compile_graph(config)
        graph = state_graph.compile()

        with (
            patch(
                "yamlgraph.node_factory.llm_nodes.execute_prompt",
                side_effect=fake_execute,
            ),
            patch(
                "examples.image_pipeline.nodes.save_prompts.OUTPUT_BASE",
                tmp_path / "outputs",
            ),
        ):
            result = graph.invoke(
                {"input_file": str(infile), "target_style": target_style}
            )
        saved = Path(result["prompt_file"]).read_text(encoding="utf-8").splitlines()
        return infile, saved

    def test_count_preserved_end_to_end(self, tmp_path):
        # 4 prompts in -> exactly 4 lines out (no originals + converted doubling).
        text = "1. a cat\n2. a dog\n3. a bird\n4. a fish\n"
        _, saved = self._run(tmp_path, text)
        assert len(saved) == 4, f"expected 4 lines, got {len(saved)}: {saved}"

    def test_saved_lines_are_converted_prompts(self, tmp_path):
        text = "a cat\na dog\n"
        _, saved = self._run(tmp_path, text, target_style="waterhouse")
        assert saved == [
            "a cat in the style of waterhouse",
            "a dog in the style of waterhouse",
        ]
        # No stringified dicts / wrapper keys leaked into the file.
        assert not any("prompt_text" in ln or "_map_index" in ln for ln in saved)

    def test_source_file_unchanged_after_run(self, tmp_path):
        text = "1. a cat\n2. a dog\n"
        infile, _ = self._run(tmp_path, text)
        assert infile.read_text(encoding="utf-8") == text

    def test_branch_failure_aborts_before_any_file_written(self, tmp_path):
        # R-3/C-4 end-to-end: one failing conversion aborts the whole run so
        # NO prompt file is ever written — "N in == N out or nothing written".
        from unittest.mock import patch

        from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

        infile = tmp_path / "prompts_in.txt"
        infile.write_text("a cat\na dog\n", encoding="utf-8")
        outputs = tmp_path / "outputs"

        def fake_execute(*args, **kwargs):
            variables = kwargs.get("variables", {})
            original = variables.get("prompt_text", "?")
            if original == "a dog":
                raise RuntimeError("mistral rejected the prompt")
            return self._FakeConverted(f"{original} restyled")

        config = load_graph_config(str(GRAPH_FILE))
        graph = compile_graph(config).compile()

        with (
            patch(
                "yamlgraph.node_factory.llm_nodes.execute_prompt",
                side_effect=fake_execute,
            ),
            patch(
                "examples.image_pipeline.nodes.save_prompts.OUTPUT_BASE",
                outputs,
            ),
            pytest.raises(ValueError, match="conversions failed"),
        ):
            graph.invoke({"input_file": str(infile), "target_style": "waterhouse"})

        # The sink never ran: no output directory / prompts.txt exists.
        assert not outputs.exists(), "no prompt file may be written on failure"
