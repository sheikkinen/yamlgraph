"""Integration tests for map-demo graph."""

from unittest.mock import MagicMock, patch

from showcase.graph_loader import compile_graph, load_graph_config


class TestMapDemoGraph:
    """Integration tests for the map-demo graph."""

    def test_map_demo_config_loads(self) -> None:
        """Map demo graph config loads successfully."""
        config = load_graph_config("graphs/map-demo.yaml")
        assert config.name == "map-demo"
        assert "expand_frames" in config.nodes
        assert config.nodes["expand_frames"]["type"] == "map"

    def test_map_demo_graph_compiles(self) -> None:
        """Map demo graph compiles to StateGraph."""
        config = load_graph_config("graphs/map-demo.yaml")

        # Mock compile_map_node to avoid needing prompt execution
        with patch("showcase.graph_loader.compile_map_node") as mock_compile_map:
            mock_map_edge_fn = MagicMock()
            mock_compile_map.return_value = (mock_map_edge_fn, "_map_expand_frames_sub")

            compile_graph(config)

            # Should have called compile_map_node for expand_frames
            mock_compile_map.assert_called_once()
            call_args = mock_compile_map.call_args
            assert call_args[0][0] == "expand_frames"

    def test_map_demo_state_has_reducer(self) -> None:
        """Map demo compiled state has reducer for expanded_frames."""
        import operator
        from typing import Annotated, get_args, get_origin

        from showcase.models.state_builder import build_state_class

        config = load_graph_config("graphs/map-demo.yaml")
        state_class = build_state_class(config.raw_config)

        annotations = state_class.__annotations__
        assert "expanded_frames" in annotations

        field_type = annotations["expanded_frames"]
        assert get_origin(field_type) is Annotated
        args = get_args(field_type)
        assert args[0] is list
        assert args[1] is operator.add
