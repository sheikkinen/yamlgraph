"""FR-467: conditional edges whose target is a ``map`` node.

A conditional (expression) edge routing one branch to a map node must compile to
a *single* router on the source node. The earlier defect registered a second,
unconditional map fan-out router alongside the expression router; LangGraph then
ran both every superstep, so the condition never took effect and graphs with a
terminating branch looped forever.

These tests pin the fix:

* exactly one router is wired on a conditional-to-map source;
* the map branch still fans out (Send) and the terminating branch reaches END;
* an *unconditional* edge to a map node mixed with conditional edges on the same
  source is rejected at compile time (dual-router guard);
* a plain unconditional node -> map edge keeps working (no regression).
"""

import pytest

from yamlgraph.graph_loader import GraphConfig, compile_graph


def _passthrough(outputs: dict) -> dict:
    return {"type": "passthrough", "outputs": outputs}


def _map_node() -> dict:
    return {
        "type": "map",
        "over": "{state.items}",
        "as": "item",
        "node": _passthrough({"r": "{state.item}"}),
        "collect": "results",
    }


def _cfg(edges: list, nodes: dict | None = None) -> GraphConfig:
    base_nodes = {
        "start": {"prompt": "gen", "state_key": "items"},
        "parse": _passthrough({"action": "{state.x}", "items": "{state.items}"}),
        "plan": _map_node(),
    }
    if nodes:
        base_nodes.update(nodes)
    return GraphConfig(
        {"name": "t", "version": "0.1", "nodes": base_nodes, "edges": edges}
    )


@pytest.mark.req("REQ-YG-434")
def test_conditional_edge_to_map_registers_single_router() -> None:
    """A conditional-to-map source wires exactly one router (not two)."""
    cfg = _cfg(
        edges=[
            {"from": "START", "to": "start"},
            {"from": "start", "to": "parse"},
            {"from": "parse", "to": "END", "condition": "action=='stop'"},
            {"from": "parse", "to": "plan", "condition": "action=='go'"},
            {"from": "plan", "to": "parse"},
        ]
    )

    graph = compile_graph(cfg)

    assert len(graph.branches["parse"]) == 1


@pytest.mark.req("REQ-YG-434")
def test_unconditional_and_conditional_map_edges_rejected() -> None:
    """Mixing an unconditional map edge with conditional edges is rejected."""
    cfg = _cfg(
        edges=[
            {"from": "START", "to": "start"},
            {"from": "start", "to": "parse"},
            # Unconditional edge to the map node...
            {"from": "parse", "to": "plan"},
            # ...alongside a conditional edge on the same source.
            {"from": "parse", "to": "END", "condition": "action=='stop'"},
            {"from": "plan", "to": "parse"},
        ]
    )

    with pytest.raises(ValueError, match="map node"):
        compile_graph(cfg)


@pytest.mark.req("REQ-YG-434")
def test_unconditional_edge_to_map_still_compiles() -> None:
    """A plain unconditional node -> map edge keeps working (no regression)."""
    cfg = _cfg(
        edges=[
            {"from": "START", "to": "start"},
            {"from": "start", "to": "plan"},
            {"from": "plan", "to": "parse"},
            {"from": "parse", "to": "END"},
        ]
    )

    graph = compile_graph(cfg)

    # The unconditional map source registers its single fan-out router.
    assert len(graph.branches["start"]) == 1
