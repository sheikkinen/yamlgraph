"""FR-1050: which node types can honor a graph-level ``loop_limits`` entry.

The two classifications are explicit and disjoint, and their union is the
whole ``NodeType`` enum — a new node type must be classified before it can
ship. Deriving support by compilation would be circular: compiling a graph
that carries ``loop_limits`` is itself gated by this classification.
"""

from yamlgraph.constants import NodeType

# Types whose factory calls ``check_loop_limit`` before doing any work.
LOOP_LIMIT_SUPPORTED_TYPES: frozenset[str] = frozenset(
    {
        NodeType.LLM,
        NodeType.ROUTER,
        NodeType.PYTHON,
        NodeType.TOOL,
        NodeType.PASSTHROUGH,
        NodeType.RACE,
    }
)

# Types on which an entry would be inert. ``interactive_tool`` and ``pipeline``
# are expansion-only macros: their authored node is gone before compilation,
# so an entry naming one can never bind.
LOOP_LIMIT_UNSUPPORTED_TYPES: frozenset[str] = frozenset(
    {
        NodeType.AGENT,
        NodeType.MAP,
        NodeType.TOOL_CALL,
        NodeType.INTERRUPT,
        NodeType.SUBGRAPH,
        NodeType.COPILOT,
        NodeType.VERIFY,
        NodeType.INTERACTIVE_TOOL,
        NodeType.PIPELINE,
    }
)


__all__ = [
    "LOOP_LIMIT_SUPPORTED_TYPES",
    "LOOP_LIMIT_UNSUPPORTED_TYPES",
    "validate_loop_limits",
]


def validate_loop_limits(config: dict) -> None:
    """Reject graph-level ``loop_limits`` entries that could never bind.

    Runs on the raw authored config, before ``interactive_tool`` and
    ``pipeline`` expansion delete their source nodes.

    Raises:
        GraphConfigError: on a key naming no node, or a node whose type
            cannot honor a limit.
    """
    from yamlgraph.compile.node_compiler import GraphConfigError

    nodes = config.get("nodes") or {}
    supported = sorted(str(t) for t in LOOP_LIMIT_SUPPORTED_TYPES)

    for node_name in config.get("loop_limits") or {}:
        node = nodes.get(node_name)
        if node is None:
            raise GraphConfigError(
                f"loop_limits entry {node_name!r} names no node in the graph. "
                f"Remove the entry or correct the node name."
            )
        node_type = str((node or {}).get("type", "llm"))
        if node_type not in LOOP_LIMIT_SUPPORTED_TYPES:
            raise GraphConfigError(
                f"Node {node_name!r} of type {node_type!r} has a 'loop_limits' "
                f"entry but loop limits are only enforced on node types "
                f"{supported}. Remove the entry or change the node type."
            )
