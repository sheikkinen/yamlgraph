"""Thin wrapper around the shared FSM bridge action."""

from pathlib import Path

from yamlgraph.utils.fsm import YamlgraphAsyncAction as _SharedYamlgraphAsyncAction


class YamlgraphAsyncAction(_SharedYamlgraphAsyncAction):
    """Example-local adapter preserving relative graph-path resolution."""

    GRAPH_BASE_DIR = Path(__file__).resolve().parent.parent


__all__ = ["YamlgraphAsyncAction"]
