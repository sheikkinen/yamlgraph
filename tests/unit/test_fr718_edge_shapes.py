"""FR-718 witnesses: edge-shape classification and dispatch decomposition.

The C(20)/C(18) pair in edge_compiler was the fossil record of shape
accretion — every routing feature added a branch to the same boolean-probe
chain. The cure (Judgement F1): `classify_edge` names the shape, a
dispatch table compiles it, and an unnameable shape RAISES with the edge
named (F2: PLAIN is an explicit member, not a fall-through claim).
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

MAP_NODES = {"mapper": (lambda s: [], "mapper__item")}


def _classify(frm, to, condition=None, edge_type=None, maps=None):
    from yamlgraph.compile.edge_compiler import classify_edge

    return classify_edge(frm, to, condition, edge_type, set((maps or MAP_NODES).keys()))


class TestClassification:
    """AC-01: every edge form names its shape; the enum is closed."""

    @pytest.mark.req("REQ-YG-568")
    def test_enum_is_exhaustive_and_counted(self):
        """A new shape must register itself here — count asserted."""
        from yamlgraph.compile.edge_compiler import EdgeShape

        assert {m.name for m in EdgeShape} == {
            "START",
            "PARALLEL_FANOUT",
            "MAP_TO_MAP",
            "TO_MAP",
            "FROM_MAP",
            "ROUTER_CONDITIONAL",
            "EXPRESSION",
            "PLAIN",
        }

    @pytest.mark.req("REQ-YG-568")
    @pytest.mark.parametrize(
        ("frm", "to", "condition", "edge_type", "expected"),
        [
            ("START", "a", None, None, "START"),
            ("START", ["a", "b"], None, None, "START"),
            ("a", ["b", "c"], None, None, "PARALLEL_FANOUT"),
            ("mapper", "mapper", None, None, "MAP_TO_MAP"),
            ("a", "mapper", None, None, "TO_MAP"),
            # FR-467: conditional edge to a map node is EXPRESSION, not TO_MAP
            ("a", "mapper", "x > 1", None, "EXPRESSION"),
            ("mapper", "b", None, None, "FROM_MAP"),
            ("a", ["b", "c"], None, "conditional", "ROUTER_CONDITIONAL"),
            ("a", "b", "score >= 0.5", None, "EXPRESSION"),
            ("a", "b", None, None, "PLAIN"),
            ("a", "END", None, None, "PLAIN"),
        ],
    )
    def test_shapes(self, frm, to, condition, edge_type, expected):
        assert _classify(frm, to, condition, edge_type).name == expected

    @pytest.mark.req("REQ-YG-568")
    def test_unnameable_shape_raises_with_edge_named(self):
        """`to: [a, b]` WITH a condition and no type: conditional was
        silently compiled as fan-out with the condition DROPPED — a
        plausible_wrong_answer at compile time. Now it raises (F2)."""
        with pytest.raises(ValueError, match="cond_fan.*condition"):
            _classify("cond_fan", ["a", "b"], "x > 1", None)


class TestComplexityRelieved:
    """AC-02: the probe chain is gone; nothing new above CC 10."""

    @pytest.mark.req("REQ-YG-568")
    def test_edge_compiler_cc_bounded(self):
        from radon.complexity import cc_visit

        src = (REPO_ROOT / "yamlgraph/compile/edge_compiler.py").read_text()
        offenders = [
            (b.name, b.complexity) for b in cc_visit(src) if b.complexity >= 10
        ]
        assert not offenders, f"CC >= 10 survived decomposition: {offenders}"


class TestRouteMappingPure:
    """The condition-map assembly is a pure function (F1 second half)."""

    @pytest.mark.req("REQ-YG-568")
    def test_expression_route_mapping(self):
        from langgraph.graph import END

        from yamlgraph.compile.edge_compiler import build_expression_route_mapping

        mapping = build_expression_route_mapping(
            [("score >= 0.5", "publish"), ("score < 0.5", "mapper")],
            loop_exit_target=None,
            map_nodes=MAP_NODES,
        )
        assert mapping["publish"] == "publish"
        assert mapping[END] == END
        assert mapping["mapper__item"] == "mapper__item"  # FR-467 sub-node

    @pytest.mark.req("REQ-YG-568")
    def test_router_route_mapping_redirects(self):
        from yamlgraph.compile.edge_compiler import build_router_route_mapping

        mapping = build_router_route_mapping(
            ["approve", "pause", "sub"],
            interrupt_nodes={"pause"},
            subgraph_interrupt_nodes={"sub"},
        )
        assert mapping == {
            "approve": "approve",
            "pause": "pause_prepare",
            "sub": "sub__run",
        }
