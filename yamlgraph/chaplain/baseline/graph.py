"""Baseline builder graph configuration."""

from pydantic import BaseModel


class GraphNode(BaseModel):
    """Represents a graph node configuration."""
    type: str
    description: str = ""


class GraphConfig(BaseModel):
    """Represents the baseline builder graph configuration."""
    nodes: dict[str, GraphNode]
    edges: dict[str, str] = {}


def load_baseline_graph() -> GraphConfig:
    """
    Load the baseline builder graph configuration.

    Returns:
        GraphConfig: Configuration for baseline builder graph
    """
    # Define the required nodes as per AC-6
    nodes = {
        "load_manifest": GraphNode(
            type="yaml_loader",
            description="Read and validate manifest schema"
        ),
        "expand_sources": GraphNode(
            type="glob_expander",
            description="Resolve globs + excludes to concrete files"
        ),
        "read_sources": GraphNode(
            type="file_reader",
            description="Load file content and compute per-source hashes"
        ),
        "resolve_summaries": GraphNode(
            type="summary_resolver",
            description="For mode: summarized, reuse by summary_key or generate then persist"
        ),
        "compute_baseline_id": GraphNode(
            type="hash_computer",
            description="Compute deterministic BASELINE_ID"
        ),
        "assemble_baseline_state": GraphNode(
            type="state_assembler",
            description="Build namespaced baseline_* state fields"
        ),
        "emit_artifact": GraphNode(
            type="json_exporter",
            description="Write export state consumed by watcher2"
        )
    }

    # Define the edges for sequential processing
    edges = {
        "load_manifest": "expand_sources",
        "expand_sources": "read_sources",
        "read_sources": "resolve_summaries",
        "resolve_summaries": "compute_baseline_id",
        "compute_baseline_id": "assemble_baseline_state",
        "assemble_baseline_state": "emit_artifact"
    }

    return GraphConfig(nodes=nodes, edges=edges)
