"""Tests for FR-201: Horoscope Demo — Parallel Daily Horoscope Generator.

TDD tests to verify the horoscope demo:
- Graph config loads with correct name and structure
- Map node fans out over all 12 zodiac signs
- State has sorted_add reducer for collected readings
- Exports section configured for markdown output
- Graph compiles to StateGraph
"""

from typing import Annotated, get_args, get_origin
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.graph_loader import compile_graph, load_graph_config

GRAPH_PATH = "examples/demos/horoscope/graph.yaml"

ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


class TestHoroscopeDemoConfig:
    """Verify horoscope demo graph config loads correctly."""

    @pytest.mark.req("REQ-YG-197")
    def test_config_loads(self) -> None:
        """Horoscope demo graph config loads successfully."""
        config = load_graph_config(GRAPH_PATH)
        assert config.name == "daily-horoscope"

    @pytest.mark.req("REQ-YG-197")
    def test_map_node_exists(self) -> None:
        """Graph has a generate node of type map."""
        config = load_graph_config(GRAPH_PATH)
        assert "generate" in config.nodes
        assert config.nodes["generate"]["type"] == "map"

    @pytest.mark.req("REQ-YG-197")
    def test_map_fans_out_over_all_12_signs(self) -> None:
        """Map node over: list contains all 12 zodiac signs."""
        config = load_graph_config(GRAPH_PATH)
        over_list = config.nodes["generate"]["over"]
        assert over_list == ZODIAC_SIGNS

    @pytest.mark.req("REQ-YG-197")
    def test_map_collects_to_readings(self) -> None:
        """Map node collects results into readings state key."""
        config = load_graph_config(GRAPH_PATH)
        assert config.nodes["generate"]["collect"] == "readings"

    @pytest.mark.req("REQ-YG-197")
    def test_assemble_node_exists(self) -> None:
        """Graph has an assemble node for formatting output."""
        config = load_graph_config(GRAPH_PATH)
        assert "assemble" in config.nodes
        assert config.nodes["assemble"]["state_key"] == "document"

    @pytest.mark.req("REQ-YG-197")
    def test_save_node_exists(self) -> None:
        """Graph has a save node for file output."""
        config = load_graph_config(GRAPH_PATH)
        assert "save" in config.nodes
        assert config.nodes["save"]["type"] == "python"
        assert config.nodes["save"]["tool"] == "save_horoscope"

    @pytest.mark.req("REQ-YG-197")
    def test_date_in_state(self) -> None:
        """State declares date as a str field."""
        config = load_graph_config(GRAPH_PATH)
        state = config.raw_config.get("state", {})
        assert "date" in state
        assert state["date"] == "str"

    @pytest.mark.req("REQ-YG-197")
    def test_prompts_relative(self) -> None:
        """Graph uses prompts_relative: true with local prompts dir."""
        config = load_graph_config(GRAPH_PATH)
        raw = config.raw_config
        assert raw.get("prompts_relative") is True
        assert raw.get("prompts_dir") == "prompts"

    @pytest.mark.req("REQ-YG-197")
    def test_minimal_python_for_file_io(self) -> None:
        """Demo uses minimal Python — only save_horoscope tool for file I/O."""
        config = load_graph_config(GRAPH_PATH)
        raw = config.raw_config
        tools = raw.get("tools", {})
        assert len(tools) == 1
        assert "save_horoscope" in tools


class TestHoroscopeDemoCompilation:
    """Verify horoscope demo graph compiles."""

    @pytest.mark.req("REQ-YG-197")
    def test_state_has_sorted_reducer_for_readings(self) -> None:
        """Compiled state has sorted_add reducer for readings."""
        from yamlgraph.models.state_builder import build_state_class, sorted_add

        config = load_graph_config(GRAPH_PATH)
        state_class = build_state_class(config.raw_config)

        annotations = state_class.__annotations__
        assert "readings" in annotations

        field_type = annotations["readings"]
        assert get_origin(field_type) is Annotated
        args = get_args(field_type)
        assert args[0] is list
        assert args[1] is sorted_add

    @pytest.mark.req("REQ-YG-197")
    def test_graph_compiles(self) -> None:
        """Horoscope demo graph compiles to StateGraph."""
        config = load_graph_config(GRAPH_PATH)

        with patch("yamlgraph.node_compiler.compile_map_node") as mock_compile_map:
            mock_map_edge_fn = MagicMock()
            mock_compile_map.return_value = (mock_map_edge_fn, "_map_generate_sub")

            compile_graph(config)

            mock_compile_map.assert_called_once()
            call_args = mock_compile_map.call_args
            assert call_args[0][0] == "generate"
