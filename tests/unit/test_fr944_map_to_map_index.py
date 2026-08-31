"""FR-944: map-to-map chaining must deliver true per-branch _map_index.

REQ-YG-568 witnesses for the MAP_TO_MAP barrier-join contract: the
downstream map router must fire once, after upstream fan-in, on merged
state — via a generated pass-through join node — so every downstream
branch receives its true index.

Graphs are built from real YAML via load_and_compile so the actual
edge_compiler MAP_TO_MAP path is exercised, not a mocked builder.
"""

import textwrap
from pathlib import Path

import pytest

from yamlgraph.compile.graph_loader import load_and_compile

TOOLS_SRC = textwrap.dedent(
    '''
    """FR-944 test tools."""

    from typing import Any


    def make_other(state: dict[str, Any]) -> list[str]:
        return ["x", "y"]


    def first(state: dict[str, Any]) -> dict[str, Any]:
        return {"value": state["item"].upper()}


    def second(state: dict[str, Any]) -> dict[str, Any]:
        return {"echo": state["item2"]["value"]}


    def second_fails_on_c(state: dict[str, Any]) -> dict[str, Any]:
        if state["item2"]["value"] == "C":
            raise ValueError("poison row")
        return {"echo": state["item2"]["value"]}


    def second_over_other(state: dict[str, Any]) -> dict[str, Any]:
        return {"echo": state["other_item"]}
    '''
)

GRAPH_TEMPLATE = """
name: fr944-chained-maps
description: Chained map index attribution witness.

state:
  items: list
  other: list
  firsts: list
  seconds: list

tools:
  make_other:
    type: python
    path: tools_fr944.py
    function: make_other
  first:
    type: python
    path: tools_fr944.py
    function: first
  second:
    type: python
    path: tools_fr944.py
    function: {second_fn}

nodes:
  first_map:
    type: map
    over: "{{state.items}}"
    as: item
    node:
      type: python
      tool: first
      state_key: out
    collect: firsts

  second_map:
    type: map
    over: "{{state.{second_over}}}"
    as: {second_as}
    node:
      type: python
      tool: second
      state_key: out2
    collect: seconds

edges:
  - from: START
    to: first_map
  - from: first_map
    to: second_map
  - from: second_map
    to: END
"""


def _write_graph(
    tmp_path: Path,
    second_fn: str = "second",
    second_over: str = "firsts",
    second_as: str = "item2",
) -> Path:
    (tmp_path / "tools_fr944.py").write_text(TOOLS_SRC)
    graph_yaml = GRAPH_TEMPLATE.format(
        second_fn=second_fn, second_over=second_over, second_as=second_as
    )
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text(graph_yaml)
    return graph_path


def _compile_chained(tmp_path: Path, **kwargs):
    return load_and_compile(str(_write_graph(tmp_path, **kwargs))).compile()


class TestCollectedListChain:
    """AC-03: N=3 chain, second map over the first map's collect output."""

    @pytest.mark.req("REQ-YG-568")
    def test_second_map_receives_true_ordered_indexes(self, tmp_path):
        """Second fan-out yields exactly 3 results, indexes [0,1,2],
        each paired to the corresponding input value."""
        app = _compile_chained(tmp_path)
        result = app.invoke({"items": ["a", "b", "c"]})

        seconds = result["seconds"]
        assert len(seconds) == 3
        assert [f["_map_index"] for f in seconds] == [0, 1, 2]
        assert [f["echo"] for f in seconds] == ["A", "B", "C"]

    @pytest.mark.req("REQ-YG-568")
    def test_first_map_indexes_unaffected(self, tmp_path):
        """Regression guard: first map keeps correct indexes."""
        app = _compile_chained(tmp_path)
        result = app.invoke({"items": ["a", "b", "c"]})

        assert [f["_map_index"] for f in result["firsts"]] == [0, 1, 2]


class TestIndependentListChain:
    """AC-04: second map over an independent M=2 list from parent state."""

    @pytest.mark.req("REQ-YG-568")
    def test_no_per_branch_nxm_fanout(self, tmp_path):
        """N=3 upstream branches, M=2 independent list: exactly 2 results
        with indexes [0, 1], not N*M=6."""
        (tmp_path / "tools_fr944.py").write_text(TOOLS_SRC)
        graph_yaml = (
            GRAPH_TEMPLATE.format(
                second_fn="second_over_other",
                second_over="other",
                second_as="other_item",
            )
            .replace(
                "edges:",
                (
                    "  seed_other:\n"
                    "    type: python\n"
                    "    tool: make_other\n"
                    "    state_key: other\n"
                    "\nedges:"
                ),
            )
            .replace(
                "  - from: START\n    to: first_map",
                "  - from: START\n    to: seed_other\n"
                "  - from: seed_other\n    to: first_map",
            )
        )
        graph_path = tmp_path / "graph.yaml"
        graph_path.write_text(graph_yaml)
        app = load_and_compile(str(graph_path)).compile()

        result = app.invoke({"items": ["a", "b", "c"]})

        seconds = result["seconds"]
        assert len(seconds) == 2, f"expected 2 sends over other, got {len(seconds)}"
        assert [f["_map_index"] for f in seconds] == [0, 1]
        assert sorted(f["echo"] for f in seconds) == ["x", "y"]


class TestErrorAttribution:
    """AC-05: a failing row is attributed to its true index."""

    @pytest.mark.req("REQ-YG-568")
    def test_error_entry_carries_true_index(self, tmp_path):
        """Poison row at index 2: wrap_for_reducer error envelope carries
        _map_index == 2 with exact error text/type; peers unchanged."""
        app = _compile_chained(tmp_path, second_fn="second_fails_on_c")
        result = app.invoke({"items": ["a", "b", "c"]})

        seconds = result["seconds"]
        error_entries = [f for f in seconds if "_error" in f]
        assert len(error_entries) == 1
        err = error_entries[0]
        assert err["_map_index"] == 2
        assert "poison row" in err["_error"]
        assert err["_error_type"] == "ValueError"
        ok = [f for f in seconds if "_error" not in f]
        assert [(f["_map_index"], f["echo"]) for f in ok] == [(0, "A"), (1, "B")]


class TestCompiledPathWitness:
    """AC-06: upstream sub-node -> generated join -> downstream Send router."""

    @pytest.mark.req("REQ-YG-568")
    def test_join_node_in_compiled_path(self, tmp_path):
        """The generated pass-through join exists; the upstream sub-node has
        a static edge to it; no downstream-map conditional router is
        attached directly to the upstream sub-node."""
        builder = load_and_compile(str(_write_graph(tmp_path)))

        join_name = "_map_join_first_map_second_map"
        assert join_name in builder.nodes

        static_edges = set(builder.edges)
        assert ("_map_first_map_sub", join_name) in static_edges

        branch_sources = set(builder.branches.keys())
        assert join_name in branch_sources
        assert "_map_first_map_sub" not in branch_sources

    @pytest.mark.req("REQ-YG-568")
    def test_join_is_stateless_passthrough(self, tmp_path):
        """The join returns {} without mutating state."""
        builder = load_and_compile(str(_write_graph(tmp_path)))

        join_runnable = builder.nodes["_map_join_first_map_second_map"].runnable
        state = {"items": ["a"], "firsts": [{"_map_index": 0, "value": "A"}]}
        assert join_runnable.invoke(dict(state)) == {}


class TestJoinNameCollision:
    """AC-07: synthetic join-name collision fails compilation explicitly."""

    @pytest.mark.req("REQ-YG-568")
    def test_collision_raises_naming_edge_and_node(self, tmp_path):
        """A user node occupying the generated join name must fail
        compilation naming the map-to-map edge and the synthetic name."""
        (tmp_path / "tools_fr944.py").write_text(TOOLS_SRC)
        graph_yaml = (
            GRAPH_TEMPLATE.format(
                second_fn="second", second_over="firsts", second_as="item2"
            )
            .replace(
                "edges:",
                (
                    "  _map_join_first_map_second_map:\n"
                    "    type: python\n"
                    "    tool: make_other\n"
                    "    state_key: other\n"
                    "\nedges:"
                ),
            )
            .replace(
                "  - from: second_map\n    to: END",
                "  - from: second_map\n    to: _map_join_first_map_second_map\n"
                "  - from: _map_join_first_map_second_map\n    to: END",
            )
        )
        graph_path = tmp_path / "graph.yaml"
        graph_path.write_text(graph_yaml)

        with pytest.raises(
            ValueError,
            match=r"first_map.*second_map.*_map_join_first_map_second_map",
        ):
            load_and_compile(str(graph_path))
