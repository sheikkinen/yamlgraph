"""Pydantic schemas for YAML graph configuration validation.

Provides structured validation for graph YAML files with clear error
messages. Node-level config models live in node_schema (FR-716 split);
this module holds the graph-level models and validation entry points.
"""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from yamlgraph.constants import NodeType
from yamlgraph.models.guard_schema import GraphVerifyRule
from yamlgraph.models.node_schema import NodeConfig, SubgraphNodeConfig

__all__ = [
    "EdgeConfig",
    "GraphConfigSchema",
    "NodeConfig",
    "SubgraphNodeConfig",
    "validate_graph_schema",
    "export_graph_json_schema",
]


class EdgeConfig(BaseModel):
    """Configuration for a graph edge."""

    from_node: str = Field(..., alias="from", description="Source node")
    to: str | list[str] = Field(..., description="Target node(s)")
    condition: str | None = Field(default=None, description="Condition expression")

    model_config = {"populate_by_name": True}


class GraphConfigSchema(BaseModel):
    """Full YAML graph configuration schema.

    Use this for validating graph YAML files with Pydantic.
    """

    version: str = Field(default="1.0")
    name: str = Field(default="unnamed")
    description: str = Field(default="")
    defaults: dict[str, Any] = Field(default_factory=dict)
    nodes: dict[str, NodeConfig] = Field(...)
    edges: list[EdgeConfig] = Field(...)
    tools: dict[str, Any] = Field(default_factory=dict)
    loop_limits: dict[str, int] = Field(default_factory=dict)
    loop_exits: dict[str, str] = Field(
        default_factory=dict,
        description="Map of node name to target node when loop limit is reached",
    )
    data_files: dict[str, str] = Field(
        default_factory=dict,
        description="External YAML data files to load into state at compile time",
    )
    verify: list[GraphVerifyRule] = Field(
        default_factory=list,
        description="Graph-level terminal verification rules (FR-677)",
    )

    model_config = {"extra": "allow"}

    @model_validator(mode="after")
    def validate_defaults_thinking_budget(self) -> "GraphConfigSchema":
        """Validate thinking_budget in defaults dict."""
        if "thinking_budget" in self.defaults:
            v = self.defaults["thinking_budget"]
            if v is not None and v < -1:
                raise ValueError(
                    f"thinking_budget must be None, -1 (Google auto), 0, or a positive integer, got {v}"
                )
        return self

    @model_validator(mode="after")
    def validate_router_targets(self) -> "GraphConfigSchema":
        """Validate router routes point to existing nodes."""
        for node_name, node in self.nodes.items():
            if node.type == NodeType.ROUTER and node.routes:
                for route_key, target in node.routes.items():
                    if target not in self.nodes:
                        raise ValueError(
                            f"Router '{node_name}' route '{route_key}' "
                            f"targets nonexistent node '{target}'"
                        )
        return self

    @model_validator(mode="after")
    def validate_edge_nodes(self) -> "GraphConfigSchema":
        """Validate edge sources and targets exist."""
        valid_nodes = set(self.nodes.keys()) | {"START", "END"}

        for edge in self.edges:
            if edge.from_node not in valid_nodes:
                raise ValueError(f"Edge 'from' node '{edge.from_node}' not found")

            targets = edge.to if isinstance(edge.to, list) else [edge.to]
            for target in targets:
                if target not in valid_nodes:
                    raise ValueError(f"Edge 'to' node '{target}' not found")

        return self


def validate_graph_schema(config: dict[str, Any]) -> GraphConfigSchema:
    """Validate a graph configuration dict using Pydantic.

    Args:
        config: Raw parsed YAML configuration

    Returns:
        Validated GraphConfigSchema

    Raises:
        pydantic.ValidationError: If validation fails
    """
    return GraphConfigSchema.model_validate(config)


def export_graph_json_schema() -> dict[str, Any]:
    """Export graph configuration as JSON Schema for IDE support.

    Returns a JSON Schema dict compatible with VS Code YAML extension
    and other JSON Schema validators.

    Returns:
        JSON Schema dict with $schema, $id, and full type definitions
    """
    schema = GraphConfigSchema.model_json_schema()

    # Add JSON Schema metadata
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    schema["$id"] = "https://yamlgraph.dev/schemas/graph-v1.json"
    schema["title"] = "YamlGraph Graph Configuration"
    schema["description"] = "Schema for YamlGraph graph.yaml files"

    return schema
