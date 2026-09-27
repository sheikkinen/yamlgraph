"""FR-1119: E007 knows every state field a map node creates."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from yamlgraph.linter.checks_semantic import (
    _build_known_state_fields,
    check_expression_syntax,
)
from yamlgraph.models.state_builder import extract_node_fields

pytestmark = pytest.mark.req("REQ-YG-069")

MAP_SHARED = ("_map_accounting", "_map_open", "_map_verdict")


def _map_node(collect: str | None = "results", failures: str | None = None) -> dict:
    node: dict = {
        "type": "map",
        "over": "{state.items}",
        "as": "item",
        "node": {"type": "llm", "prompt": "p", "state_key": "one"},
    }
    if collect is not None:
        node["collect"] = collect
    if failures is not None:
        node["failures"] = failures
    return node


def _reader(ref: str) -> dict:
    return {"type": "llm", "prompt": "p", "variables": {"x": f"{{state.{ref}}}"}}


def _e007(tmp_path: Path, nodes: dict) -> list[str]:
    graph = {"version": "1.0", "name": "g", "state": {"items": "list"}, "nodes": nodes}
    path = tmp_path / "graph.yaml"
    path.write_text(yaml.safe_dump(graph))
    return [i.message for i in check_expression_syntax(path) if i.code == "E007"]


def test_map_verdict_read_is_known(tmp_path: Path) -> None:
    nodes = {"m": _map_node(), "r": _reader("_map_verdict.m.dispatch")}
    assert _e007(tmp_path, nodes) == []


@pytest.mark.parametrize(
    ("failures", "ref"),
    [(None, "results_failures"), ("my_failures", "my_failures")],
)
def test_failures_key_is_known(tmp_path: Path, failures: str | None, ref: str) -> None:
    nodes = {"m": _map_node(failures=failures), "r": _reader(ref)}
    assert _e007(tmp_path, nodes) == []


@pytest.mark.parametrize("ref", ["_map_accounting", "_map_open"])
def test_accounting_and_open_are_known(tmp_path: Path, ref: str) -> None:
    nodes = {"m": _map_node(), "r": _reader(ref)}
    assert _e007(tmp_path, nodes) == []


@pytest.mark.parametrize("ref", MAP_SHARED)
def test_map_channels_unknown_without_map_node(tmp_path: Path, ref: str) -> None:
    messages = _e007(tmp_path, {"r": _reader(ref)})
    assert len(messages) == 1
    assert ref in messages[0]


def test_parity_with_state_builder() -> None:
    nodes = {
        "a": _map_node(collect="alpha"),
        "b": _map_node(collect="beta", failures="beta_errs"),
    }
    builder = set(extract_node_fields(nodes))
    known = _build_known_state_fields({"nodes": nodes})
    assert builder <= known
    assert {"alpha_failures", "beta_errs", *MAP_SHARED} <= builder


def test_map_without_collect_does_not_raise() -> None:
    known = _build_known_state_fields({"nodes": {"m": _map_node(collect=None)}})
    assert set(MAP_SHARED) <= known
    assert not any(f.endswith("_failures") for f in known)
