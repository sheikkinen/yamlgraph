"""FR-186: Storyboard image node to_serializable migration tests.

Tests that generate_images_node uses to_serializable() from yamlgraph.contrib
instead of inline hasattr(obj, "model_dump") patterns.
"""

import inspect
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from examples.shared.replicate_tool import ImageResult


class TestGenerateImagesNodeToSerializable:
    """FR-186: generate_images_node uses to_serializable for Pydantic models."""

    @pytest.mark.req("REQ-YG-070")
    def test_pydantic_model_story_is_serialized(self, tmp_path):
        """Category B (line 44): Pydantic model story should be converted
        via to_serializable, not inline hasattr."""

        class Story(BaseModel):
            title: str
            panels: list[str]

        story = Story(title="Test Story", panels=["A dragon appears"])

        mock_result = ImageResult(success=True, path=str(tmp_path / "panel_1.png"))

        with patch(
            "examples.storyboard.nodes.image_node.generate_image",
            return_value=mock_result,
        ):
            from examples.storyboard.nodes.image_node import generate_images_node

            result = generate_images_node({"story": story})

        assert result["images"] == [str(tmp_path / "panel_1.png")]

    @pytest.mark.req("REQ-YG-070")
    def test_string_story_uses_fallback(self, tmp_path):
        """Category B: String story should produce fallback dict with panels."""

        mock_result = ImageResult(success=True, path=str(tmp_path / "panel_1.png"))

        with patch(
            "examples.storyboard.nodes.image_node.generate_image",
            return_value=mock_result,
        ):
            from examples.storyboard.nodes.image_node import generate_images_node

            result = generate_images_node({"story": "Once upon a time..."})

        # The fallback wraps string in {"panels": [str(story)]}
        assert len(result["images"]) == 1

    @pytest.mark.req("REQ-YG-070")
    def test_dict_story_works(self, tmp_path):
        """Dict story should pass through (existing behavior preserved)."""

        mock_result = ImageResult(success=True, path=str(tmp_path / "panel_1.png"))

        with patch(
            "examples.storyboard.nodes.image_node.generate_image",
            return_value=mock_result,
        ):
            from examples.storyboard.nodes.image_node import generate_images_node

            result = generate_images_node(
                {"story": {"title": "Test", "panels": ["A scene"]}}
            )

        assert len(result["images"]) == 1

    @pytest.mark.req("REQ-YG-070")
    def test_uses_to_serializable_import(self):
        """FR-186: image_node.py must import to_serializable from contrib."""
        import examples.storyboard.nodes.image_node as mod

        source = inspect.getsource(mod)
        assert "from yamlgraph.contrib import to_serializable" in source
        assert "to_serializable(" in source
