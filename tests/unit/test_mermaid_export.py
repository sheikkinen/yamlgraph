"""Mermaid export, route overlay, and occurrence-aligned diff tests (FR-723).

AC-02: authored-view render on three representative example graphs
(loopy reflexion, map fan-out, router node).
AC-03: overlay preserves decision ordinals — ordered route reconstructible
from the render alone (condemning test: counts-only render fails).
AC-04: occurrence-aligned diff names the seam and the Nth firing.
"""

import json
import re
from pathlib import Path

import pytest
import yaml

from yamlgraph.mermaid_export import (
    diff_routes,
    parse_route_lines,
    render_mermaid,
    render_overlay,
)

REPO = Path(__file__).resolve().parents[2]
REFLEXION = REPO / "examples/demos/reflexion/graph.yaml"
ROUTER = REPO / "examples/demos/router/graph.yaml"
MAP = REPO / "examples/demos/map/graph.yaml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


# --- light Mermaid grammar (AC-02 syntactic validity) -----------------------

_LINE_PATTERNS = [
    re.compile(r"^flowchart TD$"),
    re.compile(r"^\s*%%.*$"),  # comment
    re.compile(r"^\s*[\w-]+\(\((?:START|END)\)\)$"),  # terminal nodes
    re.compile(r'^\s*[\w-]+\["[^"\[\]]+"\](?::::[\w-]+)?$'),  # node def
    re.compile(r'^\s*[\w-]+ (?:-->|-\.->)(?:\|"[^"|]+"\|)? [\w-]+$'),  # edge
    re.compile(r"^\s*classDef [\w-]+ .+$"),
    re.compile(r"^\s*class [\w,-]+ [\w-]+$"),
    re.compile(r"^\s*linkStyle \d+ .+$"),
]


def assert_valid_mermaid(text: str) -> None:
    lines = [line for line in text.splitlines() if line.strip()]
    assert lines[0] == "flowchart TD"
    for line in lines:
        assert any(p.match(line) for p in _LINE_PATTERNS), f"bad line: {line!r}"


class TestRenderAuthoredView:
    @pytest.mark.req("REQ-YG-553")
    def test_reflexion_every_node_exactly_once(self):
        text = render_mermaid(_load(REFLEXION))
        for node in ("draft", "critique", "refine"):
            defs = re.findall(rf'^\s*{node}\["', text, flags=re.M)
            assert len(defs) == 1, f"{node} defined {len(defs)} times"
        assert "START((START))" in text
        assert "END((END))" in text

    @pytest.mark.req("REQ-YG-553")
    def test_reflexion_condition_labels_exactly_once(self):
        text = render_mermaid(_load(REFLEXION))
        assert text.count("critique.score < 0.8") == 1
        assert text.count("critique.score >= 0.8") == 1

    @pytest.mark.req("REQ-YG-553")
    def test_reflexion_loop_exit_edge_rendered(self):
        """The hole this FR closes is visible on the authored map."""
        text = render_mermaid(_load(REFLEXION))
        assert re.search(r'critique -\.->\|"loop_exit"\| END', text)
        # loop limit annotated on the node
        assert re.search(r'critique\["critique \(llm, loop≤3\)"\]', text)

    @pytest.mark.req("REQ-YG-553")
    def test_router_route_labels_exactly_once(self):
        text = render_mermaid(_load(ROUTER))
        for label, target in (
            ("positive", "respond_positive"),
            ("negative", "respond_negative"),
            ("neutral", "respond_neutral"),
        ):
            edges = re.findall(rf'classify -->\|"{label}"\| {target}', text)
            assert len(edges) == 1

    @pytest.mark.req("REQ-YG-553")
    def test_map_node_type_annotated(self):
        text = render_mermaid(_load(MAP))
        assert re.search(r'expand\["expand \(map\)"\]', text)

    @pytest.mark.req("REQ-YG-553")
    def test_all_three_examples_render_valid_mermaid(self):
        for path in (REFLEXION, ROUTER, MAP):
            assert_valid_mermaid(render_mermaid(_load(path)))


# --- overlay (AC-03) ---------------------------------------------------------

ROUTE = [
    {
        "event": "route",
        "node": "critique",
        "value": "critique.score < 0.8",
        "target": "refine",
        "thread_id": "t-1",
    },
    {
        "event": "route",
        "node": "critique",
        "value": "critique.score < 0.8",
        "target": "refine",
        "thread_id": "t-1",
    },
    {
        "event": "route",
        "node": "critique",
        "value": "loop_exit",
        "target": "END",
        "thread_id": "t-1",
    },
]


class TestOverlay:
    @pytest.mark.req("REQ-YG-553")
    def test_overlay_marks_taken_edges_and_nodes(self):
        text = render_overlay(_load(REFLEXION), ROUTE)
        assert "classDef taken" in text
        assert re.search(r"^\s*class .*critique.* taken$", text, flags=re.M)
        assert re.search(r"^\s*linkStyle \d+ ", text, flags=re.M)
        assert_valid_mermaid(text)

    @pytest.mark.req("REQ-YG-553")
    def test_overlay_route_reconstructible_from_render(self):
        """Condemning test: counts alone cannot pass — ordinals must map the
        ordered route back out of the render (assert_path_not_destination)."""
        text = render_overlay(_load(REFLEXION), ROUTE)

        found: dict[int, tuple[str, str]] = {}
        for m in re.finditer(
            r'^\s*(\w+) (?:-->|-\.->)\|"([^"|]+)"\| (\w+)$', text, flags=re.M
        ):
            source, label, target = m.groups()
            for ordinal in re.findall(r"#(\d+)", label):
                found[int(ordinal)] = (source, target)

        reconstructed = [found[i] for i in sorted(found)]
        assert reconstructed == [(e["node"], e["target"]) for e in ROUTE]

    @pytest.mark.req("REQ-YG-553")
    def test_parse_route_lines_tolerates_log_prefixes_and_noise(self):
        lines = [
            "2026-07-14 12:00:01 INFO yamlgraph.route " + json.dumps(ROUTE[0]),
            "some unrelated log line",
            json.dumps({"event": "other", "node": "x"}),
            json.dumps(ROUTE[2]),
        ]
        parsed = parse_route_lines(lines)
        assert parsed == [ROUTE[0], ROUTE[2]]


# --- diff (AC-04) ------------------------------------------------------------


class TestDiff:
    @pytest.mark.req("REQ-YG-553")
    def test_identical_routes_empty_diff(self):
        assert diff_routes(ROUTE, [dict(e) for e in ROUTE]) == []

    @pytest.mark.req("REQ-YG-553")
    def test_altered_decision_names_seam_and_nth_firing(self):
        altered = [dict(e) for e in ROUTE]
        altered[1]["value"] = "critique.score >= 0.8"
        altered[1]["target"] = "END"
        diffs = diff_routes(ROUTE, altered)
        assert len(diffs) == 1
        assert "critique#2" in diffs[0]
        assert "refine" in diffs[0] and "END" in diffs[0]

    @pytest.mark.req("REQ-YG-553")
    def test_occurrence_alignment_survives_length_divergence(self):
        """Naive positional diff misaligns after the first divergence."""
        shorter = [dict(ROUTE[0]), dict(ROUTE[2])]
        diffs = diff_routes(ROUTE, shorter)
        # critique#1 matches; critique#2 differs (refine vs END);
        # critique#3 only in the longer route.
        assert any("critique#2" in d for d in diffs)
        assert any("critique#3" in d and "only in a" in d for d in diffs)
        assert not any("critique#1" in d for d in diffs)


# --- CLI (piece 2/3 wiring) --------------------------------------------------


class TestCliExport:
    @pytest.mark.req("REQ-YG-553")
    def test_cli_export_mermaid_stdout(self, capsys):
        from argparse import Namespace

        from yamlgraph.cli.export_commands import cmd_graph_export

        cmd_graph_export(
            Namespace(
                graph_path=str(REFLEXION),
                mermaid=True,
                overlay=None,
                diff=None,
                output=None,
            )
        )
        out = capsys.readouterr().out
        assert out.startswith("flowchart TD")
        assert "critique" in out

    @pytest.mark.req("REQ-YG-553")
    def test_cli_export_overlay(self, tmp_path, capsys):
        from argparse import Namespace

        from yamlgraph.cli.export_commands import cmd_graph_export

        route_file = tmp_path / "route.jsonl"
        route_file.write_text("\n".join(json.dumps(e) for e in ROUTE) + "\n")
        cmd_graph_export(
            Namespace(
                graph_path=str(REFLEXION),
                mermaid=True,
                overlay=str(route_file),
                diff=None,
                output=None,
            )
        )
        out = capsys.readouterr().out
        assert "classDef taken" in out
        assert "#3" in out

    @pytest.mark.req("REQ-YG-553")
    def test_cli_diff_identical_exit_zero(self, tmp_path, capsys):
        from argparse import Namespace

        from yamlgraph.cli.export_commands import cmd_graph_export

        a = tmp_path / "a.jsonl"
        b = tmp_path / "b.jsonl"
        payload = "\n".join(json.dumps(e) for e in ROUTE) + "\n"
        a.write_text(payload)
        b.write_text(payload)
        cmd_graph_export(
            Namespace(
                graph_path=None,
                mermaid=False,
                overlay=None,
                diff=[str(a), str(b)],
                output=None,
            )
        )
        assert "identical" in capsys.readouterr().out

    @pytest.mark.req("REQ-YG-553")
    def test_cli_diff_divergent_exit_one(self, tmp_path, capsys):
        from argparse import Namespace

        from yamlgraph.cli.export_commands import cmd_graph_export

        a = tmp_path / "a.jsonl"
        b = tmp_path / "b.jsonl"
        a.write_text("\n".join(json.dumps(e) for e in ROUTE) + "\n")
        altered = [dict(e) for e in ROUTE]
        altered[2]["target"] = "refine"
        b.write_text("\n".join(json.dumps(e) for e in altered) + "\n")

        with pytest.raises(SystemExit) as exc:
            cmd_graph_export(
                Namespace(
                    graph_path=None,
                    mermaid=False,
                    overlay=None,
                    diff=[str(a), str(b)],
                    output=None,
                )
            )
        assert exc.value.code == 1
        assert "critique#3" in capsys.readouterr().out
