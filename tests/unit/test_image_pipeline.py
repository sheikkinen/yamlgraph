"""Tests for FR-202: End-to-End Image Generation Pipeline.

Validates the image_pipeline example: graph structure, prompts, Python nodes
(save_prompts, generate_images), sidecar files, EXIF best-effort, and lint.

TDD: Red-Green-Refactor approach.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GRAPH_DIR = REPO_ROOT / "examples" / "image_pipeline"
GRAPH_FILE = GRAPH_DIR / "graph.yaml"
PROMPTS_DIR = GRAPH_DIR / "prompts"
NODES_DIR = GRAPH_DIR / "nodes"
README_FILE = GRAPH_DIR / "README.md"


def _read(path: Path) -> str:
    return path.read_text()


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


# ---------------------------------------------------------------------------
# 1. File existence tests
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-198")
class TestImagePipelineFileStructure:
    """Example directory contains all required files."""

    def test_graph_file_exists(self):
        assert GRAPH_FILE.exists(), "examples/image_pipeline/graph.yaml must exist"

    def test_generate_concepts_prompt_exists(self):
        prompt = PROMPTS_DIR / "generate_concepts.yaml"
        assert prompt.exists(), "prompts/generate_concepts.yaml must exist"

    def test_save_prompts_node_exists(self):
        node = NODES_DIR / "save_prompts.py"
        assert node.exists(), "nodes/save_prompts.py must exist"

    def test_generate_images_node_exists(self):
        node = NODES_DIR / "generate_images.py"
        assert node.exists(), "nodes/generate_images.py must exist"

    def test_readme_exists(self):
        assert README_FILE.exists(), "examples/image_pipeline/README.md must exist"

    def test_nodes_init_exists(self):
        init = NODES_DIR / "__init__.py"
        assert init.exists(), "nodes/__init__.py must exist"


# ---------------------------------------------------------------------------
# 2. Graph structure tests
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-198")
class TestImagePipelineGraphStructure:
    """Graph YAML defines the correct pipeline structure."""

    def test_graph_has_generate_concepts_node(self):
        graph = _load_yaml(GRAPH_FILE)
        assert "generate_concepts" in graph["nodes"]

    def test_generate_concepts_is_llm_type(self):
        graph = _load_yaml(GRAPH_FILE)
        node = graph["nodes"]["generate_concepts"]
        assert node["type"] == "llm"

    def test_graph_has_generate_prompts_map_node(self):
        """generate_prompts is a map node that iterates over concepts."""
        graph = _load_yaml(GRAPH_FILE)
        node = graph["nodes"]["generate_prompts"]
        assert node["type"] == "map"

    def test_map_node_iterates_over_concepts(self):
        """Map node iterates over concepts list from generate_concepts."""
        graph = _load_yaml(GRAPH_FILE)
        node = graph["nodes"]["generate_prompts"]
        assert "concepts" in node.get("over", "")

    def test_map_node_has_subgraph_inner_node(self):
        """Map node's inner node is a subgraph referencing batch_image_prompts."""
        graph = _load_yaml(GRAPH_FILE)
        node = graph["nodes"]["generate_prompts"]
        inner_node = node.get("node", {})
        assert inner_node.get("type") == "subgraph"
        assert "batch_image_prompts" in inner_node.get("graph", "")

    def test_graph_has_save_prompts_node(self):
        graph = _load_yaml(GRAPH_FILE)
        node = graph["nodes"]["save_prompts"]
        assert node["type"] == "python"

    def test_graph_has_generate_images_node(self):
        graph = _load_yaml(GRAPH_FILE)
        node = graph["nodes"]["generate_images"]
        assert node["type"] == "python"

    def test_graph_edges_form_pipeline(self):
        """Edges: START → generate_concepts → generate_prompts → save_prompts → generate_images → END."""
        graph = _load_yaml(GRAPH_FILE)
        edges = graph["edges"]
        edge_pairs = [(e["from"], e["to"]) for e in edges]
        assert ("START", "generate_concepts") in edge_pairs
        assert ("generate_concepts", "generate_prompts") in edge_pairs
        assert ("generate_prompts", "save_prompts") in edge_pairs
        assert ("save_prompts", "generate_images") in edge_pairs
        assert ("generate_images", "END") in edge_pairs

    def test_graph_state_declares_required_fields(self):
        """State must declare style, count, concepts_count, concepts, prompts, etc."""
        graph = _load_yaml(GRAPH_FILE)
        state = graph.get("state", {})
        for field in (
            "style",
            "count",
            "concepts_count",
            "concepts",
            "prompts",
            "prompt_file",
            "output_dir",
            "images",
        ):
            assert field in state, f"State must declare '{field}' field"

    def test_graph_tools_section_declares_python_tools(self):
        graph = _load_yaml(GRAPH_FILE)
        tools = graph.get("tools", {})
        assert "save_prompts" in tools
        assert tools["save_prompts"]["type"] == "python"
        assert "generate_images" in tools
        assert tools["generate_images"]["type"] == "python"


# ---------------------------------------------------------------------------
# 3. Prompt structure tests
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-198")
class TestImagePipelinePrompt:
    """generate_concepts prompt produces a single concept theme as plain string."""

    def test_prompt_has_name(self):
        prompt = _load_yaml(PROMPTS_DIR / "generate_concepts.yaml")
        assert prompt.get("name") == "generate_concepts"

    def test_prompt_has_system_and_user(self):
        prompt = _load_yaml(PROMPTS_DIR / "generate_concepts.yaml")
        assert "system" in prompt, "Prompt must have system message"
        assert "user" in prompt, "Prompt must have user message"

    def test_prompt_uses_jinja2(self):
        """Prompt uses Jinja2 for variable interpolation."""
        content = _read(PROMPTS_DIR / "generate_concepts.yaml")
        assert "{{" in content or "{%" in content

    def test_prompt_references_style_variable(self):
        content = _read(PROMPTS_DIR / "generate_concepts.yaml")
        assert "style" in content

    def test_prompt_has_schema_for_concepts_list(self):
        """FR-202 extended: Prompt has schema for concepts list."""
        prompt = _load_yaml(PROMPTS_DIR / "generate_concepts.yaml")
        assert (
            "schema" in prompt
        ), "generate_concepts must have a schema for ConceptList"
        schema = prompt["schema"]
        assert "concepts" in schema.get("fields", {})


# ---------------------------------------------------------------------------
# 4. save_prompts_node unit tests
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-198")
class TestSavePromptsNode:
    """save_prompts writes prompts.txt to output dir, one per line."""

    def test_saves_prompts_to_file(self, tmp_path):
        from examples.image_pipeline.nodes.save_prompts import save_prompts_node

        prompts = [
            "A dark forest at midnight",
            "An angel of death",
            "A ruined cathedral",
        ]
        state = {"prompts": prompts}

        with patch(
            "examples.image_pipeline.nodes.save_prompts.OUTPUT_BASE",
            tmp_path / "outputs" / "image_pipeline",
        ):
            result = save_prompts_node(state)

        prompt_file = Path(result["prompt_file"])
        assert prompt_file.exists()
        lines = prompt_file.read_text().strip().split("\n")
        assert lines == prompts

    def test_returns_prompt_file_and_output_dir(self, tmp_path):
        from examples.image_pipeline.nodes.save_prompts import save_prompts_node

        state = {"prompts": ["test prompt"]}

        with patch(
            "examples.image_pipeline.nodes.save_prompts.OUTPUT_BASE",
            tmp_path / "outputs" / "image_pipeline",
        ):
            result = save_prompts_node(state)

        assert "prompt_file" in result
        assert "output_dir" in result
        assert Path(result["output_dir"]).is_dir()

    def test_raises_on_empty_prompts(self):
        from examples.image_pipeline.nodes.save_prompts import save_prompts_node

        with pytest.raises(ValueError, match="[Nn]o prompts"):
            save_prompts_node({"prompts": []})

    def test_raises_on_missing_prompts(self):
        from examples.image_pipeline.nodes.save_prompts import save_prompts_node

        with pytest.raises(ValueError, match="[Nn]o prompts"):
            save_prompts_node({})


# ---------------------------------------------------------------------------
# 5. generate_images_node unit tests
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-198")
class TestGenerateImagesNode:
    """generate_images calls Replicate via shared/replicate_tool.py, saves PNGs and sidecars."""

    def test_calls_generate_image_for_each_prompt(self, tmp_path):
        from examples.shared.replicate_tool import ImageResult

        prompts = ["prompt one", "prompt two"]
        output_dir = str(tmp_path)
        state = {"prompts": prompts, "output_dir": output_dir}

        mock_results = [
            ImageResult(success=True, path=str(tmp_path / "image_01.png")),
            ImageResult(success=True, path=str(tmp_path / "image_02.png")),
        ]
        # Create fake image files so sidecar writes work
        (tmp_path / "image_01.png").write_bytes(b"fake png 1")
        (tmp_path / "image_02.png").write_bytes(b"fake png 2")

        with patch(
            "examples.image_pipeline.nodes.generate_images.generate_image",
            side_effect=mock_results,
        ) as mock_gen:
            from examples.image_pipeline.nodes.generate_images import (
                generate_images_node,
            )

            result = generate_images_node(state)

        assert mock_gen.call_count == 2
        assert len(result["images"]) == 2

    def test_uses_z_image_model(self, tmp_path):
        from examples.shared.replicate_tool import ImageResult

        state = {"prompts": ["test"], "output_dir": str(tmp_path)}
        mock_result = ImageResult(success=True, path=str(tmp_path / "image_01.png"))
        (tmp_path / "image_01.png").write_bytes(b"fake png")

        with patch(
            "examples.image_pipeline.nodes.generate_images.generate_image",
            return_value=mock_result,
        ) as mock_gen:
            from examples.image_pipeline.nodes.generate_images import (
                generate_images_node,
            )

            generate_images_node(state)

        _, kwargs = mock_gen.call_args
        assert kwargs.get("model_name") == "z-image"

    def test_no_sidecar_when_exif_succeeds(self, tmp_path):
        """No sidecar .txt when EXIF metadata is successfully written."""
        from examples.shared.replicate_tool import ImageResult

        prompt = "A dragon in the sky"
        state = {"prompts": [prompt], "output_dir": str(tmp_path)}
        mock_result = ImageResult(success=True, path=str(tmp_path / "image_01.png"))
        (tmp_path / "image_01.png").write_bytes(b"fake png")

        with (
            patch(
                "examples.image_pipeline.nodes.generate_images.generate_image",
                return_value=mock_result,
            ),
            patch(
                "examples.image_pipeline.nodes.generate_images._embed_exif",
                return_value=True,  # EXIF succeeds
            ),
        ):
            from examples.image_pipeline.nodes.generate_images import (
                generate_images_node,
            )

            generate_images_node(state)

        # Check no sidecar .txt files exist (EXIF succeeded)
        sidecars = list(tmp_path.glob("zimage_*.txt"))
        assert len(sidecars) == 0, "No sidecar when EXIF succeeds"

    def test_writes_sidecar_when_exif_fails(self, tmp_path):
        """Sidecar .txt is fallback when EXIF embedding fails."""
        from examples.shared.replicate_tool import ImageResult

        prompt = "A dragon in the sky"
        state = {"prompts": [prompt], "output_dir": str(tmp_path)}
        mock_result = ImageResult(success=True, path=str(tmp_path / "image_01.png"))
        (tmp_path / "image_01.png").write_bytes(b"fake png")

        with (
            patch(
                "examples.image_pipeline.nodes.generate_images.generate_image",
                return_value=mock_result,
            ),
            patch(
                "examples.image_pipeline.nodes.generate_images._embed_exif",
                return_value=False,  # EXIF fails
            ),
        ):
            from examples.image_pipeline.nodes.generate_images import (
                generate_images_node,
            )

            generate_images_node(state)

        # Check sidecar .txt exists (EXIF failed, fallback written)
        sidecars = list(tmp_path.glob("zimage_*.txt"))
        assert len(sidecars) == 1, "Sidecar must exist when EXIF fails"
        assert sidecars[0].read_text() == prompt

    def test_skips_failed_images(self, tmp_path):
        from examples.shared.replicate_tool import ImageResult

        state = {"prompts": ["good", "bad"], "output_dir": str(tmp_path)}
        results = [
            ImageResult(success=True, path=str(tmp_path / "image_01.png")),
            ImageResult(success=False, error="Rate limited"),
        ]
        (tmp_path / "image_01.png").write_bytes(b"fake png")

        with patch(
            "examples.image_pipeline.nodes.generate_images.generate_image",
            side_effect=results,
        ):
            from examples.image_pipeline.nodes.generate_images import (
                generate_images_node,
            )

            result = generate_images_node(state)

        assert len(result["images"]) == 1

    def test_exif_best_effort_no_exiftool(self, tmp_path):
        """EXIF embedding returns False when exiftool is not available."""
        from examples.image_pipeline.nodes.generate_images import (
            PromptMetadata,
            _embed_exif,
        )

        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake png")
        metadata = PromptMetadata(prompt_text="test prompt")

        with patch(
            "examples.image_pipeline.nodes.generate_images.subprocess.run",
            side_effect=FileNotFoundError("exiftool not found"),
        ):
            result = _embed_exif(image_path, metadata)
            assert result is False, "Should return False when exiftool unavailable"

    def test_exif_calls_exiftool_when_available(self, tmp_path):
        """EXIF embedding calls exiftool with all metadata fields."""
        from examples.image_pipeline.nodes.generate_images import (
            PromptMetadata,
            _embed_exif,
        )

        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake png")
        metadata = PromptMetadata(
            prompt_text="test prompt",
            concept="test concept",
            scene_brief="test brief",
        )

        with patch(
            "examples.image_pipeline.nodes.generate_images.subprocess.run",
        ) as mock_run:
            result = _embed_exif(image_path, metadata)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "exiftool"
        assert "-Description=test prompt" in args
        assert "-Title=test concept" in args
        assert "-Subject=test brief" in args
        assert result is True, "Should return True when exiftool succeeds"

    def test_returns_images_list(self, tmp_path):
        from examples.shared.replicate_tool import ImageResult

        state = {"prompts": ["p1"], "output_dir": str(tmp_path)}
        mock_result = ImageResult(success=True, path=str(tmp_path / "image_01.png"))
        (tmp_path / "image_01.png").write_bytes(b"fake png")

        with patch(
            "examples.image_pipeline.nodes.generate_images.generate_image",
            return_value=mock_result,
        ):
            from examples.image_pipeline.nodes.generate_images import (
                generate_images_node,
            )

            result = generate_images_node(state)

        assert "images" in result
        assert isinstance(result["images"], list)


# ---------------------------------------------------------------------------
# 6. Lint validation
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-198")
class TestImagePipelineLint:
    """Graph passes yamlgraph lint with no errors."""

    def test_graph_passes_lint(self):
        """examples/image_pipeline/graph.yaml passes yamlgraph graph lint."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(GRAPH_FILE)
        errors = [i for i in result.issues if i.severity == "error"]
        assert (
            len(errors) == 0
        ), f"Graph lint errors: {[f'{e.code}: {e.message}' for e in errors]}"
