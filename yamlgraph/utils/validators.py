"""Graph configuration validators.

Validation functions for YAML graph configuration structures.
"""

from typing import Any

from yamlgraph.constants import ErrorHandler, NodeType


def validate_required_sections(config: dict[str, Any]) -> None:
    """Validate required top-level sections exist.

    Args:
        config: Parsed YAML configuration dictionary

    Raises:
        ValueError: If required sections are missing
    """
    if not config.get("nodes"):
        raise ValueError("Graph config missing required 'nodes' section")
    if not config.get("edges"):
        raise ValueError("Graph config missing required 'edges' section")


def validate_node_prompt(node_name: str, node_config: dict[str, Any]) -> None:
    """Validate node has required prompt if applicable.

    Args:
        node_name: Name of the node
        node_config: Node configuration dictionary

    Raises:
        ValueError: If prompt is required but missing
    """
    node_type = node_config.get("type", NodeType.LLM)
    # Only llm and router nodes require prompts
    # tool, python, agent, and map nodes don't require prompts
    if NodeType.requires_prompt(node_type) and not node_config.get("prompt"):
        raise ValueError(f"Node '{node_name}' missing required 'prompt' field")


def validate_router_node(
    node_name: str, node_config: dict[str, Any], all_nodes: dict[str, Any]
) -> None:
    """Validate router node has routes pointing to valid nodes.

    Args:
        node_name: Name of the node
        node_config: Node configuration dictionary
        all_nodes: All nodes in the graph for target validation

    Raises:
        ValueError: If router configuration is invalid
    """
    if node_config.get("type") != NodeType.ROUTER:
        return

    if not node_config.get("routes"):
        raise ValueError(f"Router node '{node_name}' missing required 'routes' field")

    for route_key, target_node in node_config["routes"].items():
        if target_node not in all_nodes:
            raise ValueError(
                f"Router node '{node_name}' route '{route_key}' points to "
                f"nonexistent node '{target_node}'"
            )

    # FR-272: candidates + provider is mutually exclusive
    if node_config.get("candidates") and node_config.get("provider"):
        raise ValueError(
            f"Router node '{node_name}' cannot have both 'provider' and 'candidates' — "
            "use 'candidates' for race-based routing (FR-272)"
        )

    # FR-272: on_error: skip is invalid for router nodes with candidates
    if node_config.get("candidates") and node_config.get("on_error") == "skip":
        raise ValueError(
            f"Router node '{node_name}' with 'candidates' cannot use "
            "on_error: skip — a router must always produce a route; "
            "use on_error: fallback to route via default_route instead"
        )


def validate_edges(edges: list[dict[str, Any]]) -> None:
    """Validate each edge has required from/to fields.

    Args:
        edges: List of edge configurations

    Raises:
        ValueError: If edge is missing required fields
    """
    for i, edge in enumerate(edges):
        if "from" not in edge:
            raise ValueError(f"Edge {i} missing required 'from' field")
        if "to" not in edge:
            raise ValueError(f"Edge {i} missing required 'to' field")

        # Validate condition expressions at load time
        if "condition" in edge:
            validate_condition_expression(edge["condition"], i)


def validate_condition_expression(condition: str, edge_index: int) -> None:
    """Validate a condition expression has valid syntax.

    Performs compile-time validation of condition expressions to catch
    syntax errors early rather than at runtime.

    Supports expression conditions like "score < 0.8", "a.b >= 1 and c == 'done'"

    Args:
        condition: Condition expression like "score < 0.8"
        edge_index: Edge index for error messages

    Raises:
        ValueError: If condition has invalid syntax
    """
    import re

    # Expression syntax check - must match comparison pattern
    # Valid: "score < 0.8", "a.b >= 1", "x == 'done'"
    # Also valid: compound expressions "a > 1 and b < 2"
    comparison_pattern = r"[a-zA-Z_][\w.]*\s*(<=|>=|==|!=|<|>)\s*.+"
    compound_pattern = r"\s+(and|or)\s+"

    # Split by and/or and validate each part
    parts = re.split(compound_pattern, condition, flags=re.IGNORECASE)
    # parts includes the 'and'/'or' tokens, so filter to just comparisons
    comparisons = [p.strip() for p in parts if p.strip().lower() not in ("and", "or")]

    for part in comparisons:
        if not re.match(comparison_pattern, part.strip()):
            raise ValueError(
                f"Edge {edge_index} has invalid condition syntax: '{condition}'. "
                f"Expected format: 'field <op> value' (e.g., 'score < 0.8')"
            )


def validate_on_error(node_name: str, node_config: dict[str, Any]) -> None:
    """Validate on_error value is valid.

    Args:
        node_name: Name of the node
        node_config: Node configuration dictionary

    Raises:
        ValueError: If on_error value is invalid
    """
    on_error = node_config.get("on_error")
    # FR-778: tool_call supports only skip/fail; the retrying and
    # substituting handlers are LLM-node semantics the envelope contract
    # cannot honor.
    if node_config.get("type") == "tool_call":
        if on_error and on_error not in ("skip", "fail"):
            raise ValueError(
                f"Node '{node_name}' (tool_call) has invalid on_error value "
                f"'{on_error}'. Valid values: skip, fail"
            )
        return
    if on_error and on_error not in ErrorHandler.all_values():
        raise ValueError(
            f"Node '{node_name}' has invalid on_error value '{on_error}'. "
            f"Valid values: {', '.join(ErrorHandler.all_values())}"
        )


def validate_map_node(node_name: str, node_config: dict[str, Any]) -> None:
    """Validate map node has required fields.

    Args:
        node_name: Name of the node
        node_config: Node configuration dictionary

    Raises:
        ValueError: If map node configuration is invalid
    """
    if node_config.get("type") != NodeType.MAP:
        return

    required_fields = ["over", "as", "node", "collect"]
    for field in required_fields:
        if field not in node_config:
            raise ValueError(f"Map node '{node_name}' missing required '{field}' field")

    # FR-1073: min_success is an int count >= 0 or a float fraction in [0, 1]
    if "min_success" in node_config:
        value = node_config["min_success"]
        valid_int = (
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
        )
        valid_float = isinstance(value, float) and 0.0 <= value <= 1.0
        if not (valid_int or valid_float):
            raise ValueError(
                f"Map node '{node_name}': min_success must be an integer >= 0 "
                f"or a float in [0.0, 1.0], got {value!r}"
            )

    # FR-1073: failures must be a distinct, non-reserved state key
    if "failures" in node_config:
        value = node_config["failures"]
        reserved = {"errors", "current_step", "_loop_counts", node_config["collect"]}
        if (
            not isinstance(value, str)
            or not value
            or value in reserved
            or value.startswith("_map_")
        ):
            raise ValueError(
                f"Map node '{node_name}': failures must be a non-empty state key "
                f"distinct from collect and reserved keys, got {value!r}"
            )


def validate_interactive_tool_node(node_name: str, node_config: dict[str, Any]) -> None:
    """Validate interactive_tool node has required fields.

    Args:
        node_name: Name of the node
        node_config: Node configuration dictionary

    Raises:
        ValueError: If interactive_tool node configuration is invalid
    """
    if node_config.get("type") != NodeType.INTERACTIVE_TOOL:
        return

    required_fields = ["start", "step", "resume_key", "response_key", "loop_until"]
    for field in required_fields:
        if field not in node_config:
            raise ValueError(
                f"Interactive tool node '{node_name}' missing required '{field}' field"
            )


def validate_max_concurrency(value: Any) -> int | None:
    """FR-984: `config.max_concurrency` is a positive int or absent.

    `None` means absent (FR-1085: resolution falls through to the
    environment, then the default). Booleans are rejected explicitly because
    Python treats `bool` as `int`.
    """
    return _positive_int_or_none(value, "config.max_concurrency")


def _positive_int_or_none(value: Any, source: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"Invalid {source} {value!r}: expected a positive integer")
    return value


# FR-1085: one resolved width for the managed run boundaries.
DEFAULT_MAX_CONCURRENCY = 8
MAX_CONCURRENCY_ENV = "YAMLGRAPH_MAX_CONCURRENCY"
# Set by load_and_compile_async so run_graph_async recovers the graph value.
GRAPH_WIDTH_ATTR = "_yamlgraph_max_concurrency"


def _env_max_concurrency() -> int | None:
    import os

    raw = os.environ.get(MAX_CONCURRENCY_ENV)
    if raw is None:
        return None
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        raise ValueError(
            f"{MAX_CONCURRENCY_ENV} must be a positive integer, got {raw!r}"
        )
    return value


def resolve_max_concurrency(caller: Any, graph: Any) -> int:
    """FR-1085: caller run value, then graph config, then environment, then 8."""
    resolved = _positive_int_or_none(caller, "run config max_concurrency")
    if resolved is None:
        resolved = validate_max_concurrency(graph)
    if resolved is None:
        resolved = _env_max_concurrency()
    return DEFAULT_MAX_CONCURRENCY if resolved is None else resolved


def with_max_concurrency(config: dict[str, Any] | None, graph: Any) -> dict[str, Any]:
    """Copy ``config`` with the resolved width; the caller's dict is untouched."""
    resolved = dict(config or {})
    resolved["max_concurrency"] = resolve_max_concurrency(
        resolved.get("max_concurrency"), graph
    )
    return resolved


def graph_width_of(app: Any) -> int | None:
    """Graph width recorded on a compiled app by load_and_compile_async."""
    return vars(app).get(GRAPH_WIDTH_ATTR) if hasattr(app, "__dict__") else None


def validate_config(config: dict[str, Any]) -> None:
    """Validate YAML configuration structure.

    Args:
        config: Parsed YAML dictionary

    Raises:
        ValueError: If required fields are missing or invalid
    """
    validate_required_sections(config)

    # FR-673: Pydantic schema validation rejects unknown node keys at load time
    from pydantic import ValidationError

    from yamlgraph.models.graph_schema import validate_graph_schema

    try:
        validate_graph_schema(config)
    except ValidationError as e:
        raise ValueError(str(e)) from e

    nodes = config["nodes"]
    for node_name, node_config in nodes.items():
        validate_node_prompt(node_name, node_config)
        validate_router_node(node_name, node_config, nodes)
        validate_on_error(node_name, node_config)
        validate_map_node(node_name, node_config)
        validate_interactive_tool_node(node_name, node_config)

    validate_edges(config["edges"])
