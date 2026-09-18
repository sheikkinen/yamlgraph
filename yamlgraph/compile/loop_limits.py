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


__all__ = ["LOOP_LIMIT_SUPPORTED_TYPES", "LOOP_LIMIT_UNSUPPORTED_TYPES"]
