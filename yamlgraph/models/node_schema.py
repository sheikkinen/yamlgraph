"""Pydantic schemas for per-node YAML configuration (FR-716).

Split from graph_schema.py at the node/graph seam: this module holds the
node-level config models; graph-level models (EdgeConfig,
GraphConfigSchema) stay in graph_schema. Public names are re-exported
unchanged from yamlgraph.models.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from yamlgraph.constants import ErrorHandler, NodeType
from yamlgraph.models.guard_schema import (
    CacheConfig,
    GuardConfig,
    VerificationConfig,
)


class SubgraphNodeConfig(BaseModel):
    """Configuration for a subgraph node."""

    type: Literal["subgraph"]
    graph: str = Field(
        ..., description="Path to subgraph YAML file (relative to parent)"
    )
    mode: Literal["invoke", "direct"] = Field(
        default="invoke",
        description="invoke: explicit state mapping; direct: shared schema",
    )
    input_mapping: dict[str, str] | Literal["auto", "*"] = Field(
        default_factory=dict,
        description="Map parent state fields to child input (mode=invoke only)",
    )
    output_mapping: dict[str, str] | Literal["auto", "*"] = Field(
        default_factory=dict,
        description="Map child output fields to parent state (mode=invoke only)",
    )
    interrupt_output_mapping: dict[str, str] | Literal["auto", "*"] = Field(
        default_factory=dict,
        description="Map child state to parent when subgraph interrupts (FR-006)",
    )
    checkpointer: str | None = Field(
        default=None,
        description="Override parent checkpointer",
    )

    model_config = {"extra": "allow"}

    @model_validator(mode="after")
    def validate_config(self) -> "SubgraphNodeConfig":
        """Validate subgraph configuration."""
        if not self.graph.endswith((".yaml", ".yml")):
            raise ValueError(f"Subgraph must be a YAML file: {self.graph}")
        if self.mode == "direct" and (self.input_mapping or self.output_mapping):
            raise ValueError("mode=direct does not support input/output mappings")
        return self


class NodeConfig(BaseModel):
    """Configuration for a single graph node."""

    type: str = Field(default=NodeType.LLM, description="Node type")
    prompt: str | None = Field(default=None, description="Prompt template name")
    state_key: str | None = Field(default=None, description="State key for output")
    temperature: float = Field(default=0.7, ge=0, le=2)
    provider: str | None = Field(default=None)
    model: str | None = Field(default=None, description="Model name override")
    thinking_budget: int | None = Field(
        default=None,
        description="Anthropic extended thinking budget_tokens (0 or ≥1024)",
    )
    on_error: str | None = Field(default=None)
    fallback: dict[str, Any] | None = Field(default=None)
    variables: dict[str, str] = Field(default_factory=dict)
    requires: list[str] = Field(default_factory=list)
    routes: dict[str, str] | None = Field(default=None, description="Router routes")
    route_field: str | None = Field(
        default=None,
        description="Field name to extract route key from LLM result (router nodes, FR-107)",
    )

    # Map node fields
    over: str | list | None = Field(
        default=None, description="Map over expression or inline list"
    )
    # 'as' is reserved in Python, handled specially
    item_var: str | None = Field(default=None, alias="as")
    node: dict[str, Any] | None = Field(default=None, description="Map sub-node")
    collect: str | None = Field(default=None, description="Map collect key")
    flatten_output: bool = Field(
        default=False, description="Merge _map_xxx_sub contents into items (FR-052)"
    )

    # Tool/Agent fields
    tools: list[str] = Field(default_factory=list)
    max_iterations: int = Field(default=10, ge=1)

    # Per-node timeout (FR-069)
    timeout: float | None = Field(
        default=None,
        description="Timeout in seconds for node execution (any node type)",
    )

    # Copilot node fields (REQ-YG-087)
    backend: Literal["cli", "api", "sampling", "claude"] | None = Field(
        default=None,
        description="Copilot backend: 'cli', 'api', 'sampling', or 'claude' (FR-959)",
    )
    cli_flags: dict[str, Any] | None = Field(
        default=None, description="CLI flags for copilot node (allow_all_paths, etc.)"
    )

    # Race node fields (FR-232)
    candidates: list[dict[str, Any]] | None = Field(
        default=None,
        description="Race candidates: list of {provider, model} dicts",
    )

    # JSON extraction mode (FR-264)
    parse_json: bool = Field(
        default=False,
        description="Extract JSON from LLM response instead of using structured output",
    )

    # Verification gate (FR-164)
    verification: VerificationConfig | None = Field(
        default=None,
        description="Verification gate — falsifiable prediction checked after execution",
    )
    guards: GuardConfig | None = Field(
        default=None,
        description="Deterministic pre/post guard checks with explicit failure policy",
    )

    # Node-level caching (FR-032)
    cache: CacheConfig | None = Field(
        default=None,
        description="Cache policy — true for default, {ttl: N} for time-limited",
    )

    # Structured output model class path (FR-673)
    output_model: str | None = Field(
        default=None, description="Pydantic model class path for structured output"
    )
    max_tokens: int | None = Field(
        default=None, description="Per-node token limit override"
    )
    default_route: str | None = Field(
        default=None, description="Fallback route when routing condition doesn't match"
    )
    loop_limit: int | None = Field(
        default=None, description="Per-node loop protection limit"
    )
    skip_if_exists: bool = Field(
        default=True, description="Skip execution if state_key already has truthy value"
    )
    max_retries: int | None = Field(
        default=None, description="Per-node retry count override"
    )
    description: str | None = Field(
        default=None, description="Human-readable node description"
    )

    # Interrupt node fields
    message: str | dict[str, Any] | None = Field(
        default=None, description="Static interrupt payload sent to user"
    )
    resume_key: str | None = Field(
        default=None, description="State key for storing user response to interrupt"
    )
    idempotent: bool = Field(
        default=True,
        description="Skip prompt if payload already exists (interrupt nodes)",
    )

    # Passthrough node fields
    output: dict[str, Any] | None = Field(
        default=None,
        description=(
            "State key → value mappings for passthrough nodes: template/"
            "expression strings or literal seeds (list, dict, bool, ...) "
            "passed through unchanged by resolve_template (FR-721)"
        ),
    )
    outputs: dict[str, Any] | None = Field(
        default=None, description="Alias for output (passthrough nodes)"
    )

    # Tool call node fields
    tool: str | None = Field(
        default=None, description="Tool name or template expression"
    )
    args: str | dict[str, Any] | None = Field(
        default=None, description="Tool arguments expression"
    )
    tool_results_key: str | None = Field(
        default=None, description="State key for agent tool results"
    )
    parsed_key: str | None = Field(
        default=None,
        description=(
            "FR-810: state key exposing the parsed dict output of a "
            "graph-runtime tool_call, routable by edge conditions"
        ),
    )

    # Map node limits
    max_items: int | None = Field(
        default=None, description="Maximum items to process in map node"
    )

    # Subgraph fields (used when type=subgraph alongside SubgraphNodeConfig)
    graph: str | None = Field(default=None, description="Path to subgraph YAML file")
    mode: str | None = Field(
        default=None, description="Subgraph mode: invoke or direct"
    )
    input_mapping: dict[str, str] | str | None = Field(
        default=None, description="Map parent state fields to child input"
    )
    output_mapping: dict[str, str] | str | None = Field(
        default=None, description="Map child output fields to parent state"
    )
    interrupt_output_mapping: dict[str, str] | str | None = Field(
        default=None, description="Map child state to parent when subgraph interrupts"
    )
    checkpointer: str | None = Field(
        default=None, description="Override parent checkpointer"
    )

    # Python node fields
    module: str | None = Field(
        default=None, description="Python module path for python nodes"
    )
    function: str | None = Field(
        default=None, description="Function name in module for python nodes"
    )
    path: str | None = Field(
        default=None, description="File path to Python module for python nodes"
    )

    # Schema reference
    schema_ref: str | None = Field(
        default=None, alias="schema", description="External YAML schema file reference"
    )
    output_schema: dict[str, Any] | str | None = Field(
        default=None, description="Inline output schema definition"
    )

    model_config = {"extra": "forbid", "populate_by_name": True}

    @field_validator("cache", mode="before")
    @classmethod
    def parse_cache(cls, v: Any) -> Any:
        """Parse cache shorthand: true → CacheConfig(), false → None, dict → CacheConfig."""
        if v is True:
            return CacheConfig()
        if v is False or v is None:
            return None
        if isinstance(v, dict):
            return CacheConfig(**v)
        return v

    @field_validator("verification", mode="before")
    @classmethod
    def parse_verification(cls, v: Any) -> Any:
        """Parse verification from dict (YAML input) to VerificationConfig."""
        if isinstance(v, dict):
            return VerificationConfig(**v)
        return v

    @field_validator("guards", mode="before")
    @classmethod
    def parse_guards(cls, v: Any) -> Any:
        """Parse guards from dict (YAML input) to GuardConfig."""
        if isinstance(v, dict):
            return GuardConfig(**v)
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: float | None) -> float | None:
        """Validate timeout is a positive number."""
        if v is not None and v <= 0:
            raise ValueError(f"timeout must be positive, got {v}")
        return v

    @field_validator("on_error")
    @classmethod
    def validate_on_error(cls, v: str | None) -> str | None:
        """Validate on_error is a known handler."""
        if v is not None and v not in ErrorHandler.all_values():
            valid = ", ".join(ErrorHandler.all_values())
            raise ValueError(f"Invalid on_error '{v}'. Valid: {valid}")
        return v

    @field_validator("thinking_budget")
    @classmethod
    def validate_thinking_budget(cls, v: int | None) -> int | None:
        """Validate thinking_budget is None, -1 (Google auto), 0, or a positive integer."""
        if v is not None and v < -1:
            raise ValueError(
                f"thinking_budget must be None, -1 (Google auto), 0, or a positive integer, got {v}"
            )
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_tool_call_on_error(cls, data: Any) -> Any:
        """FR-778: tool_call supports only skip/fail (envelope vs raise).

        Runs before field validation so every invalid value gets the
        tool_call-specific valid set, not the generic ErrorHandler one.
        """
        if isinstance(data, dict) and data.get("type") == "tool_call":
            on_error = data.get("on_error")
            if on_error not in (None, "skip", "fail"):
                raise ValueError(
                    f"Invalid on_error '{on_error}' for tool_call. "
                    "Valid values: skip, fail"
                )
        return data

    @model_validator(mode="after")
    def validate_claude_cli_flags(self) -> "NodeConfig":
        """FR-959 REQ-YG-640: typed cli_flags when backend is 'claude'."""
        if self.type == NodeType.COPILOT and self.backend == "claude":
            from yamlgraph.models.schemas import ClaudeCliFlags

            ClaudeCliFlags.model_validate(self.cli_flags or {})
        return self

    @model_validator(mode="after")
    def validate_node_requirements(self) -> "NodeConfig":
        """Validate node has required fields based on type."""
        if NodeType.requires_prompt(self.type) and not self.prompt:
            raise ValueError(f"Node type '{self.type}' requires 'prompt' field")

        if self.type == NodeType.ROUTER and not self.routes:
            raise ValueError("Router node requires 'routes' field")

        if self.type == NodeType.ROUTER and not self.route_field:
            raise ValueError(
                "Router node requires 'route_field' — the schema field name "
                "to extract the route key from (e.g. route_field: intent)"
            )

        if self.type == NodeType.MAP:
            if not self.over:
                raise ValueError("Map node requires 'over' field")
            if not self.item_var:
                raise ValueError("Map node requires 'as' field")
            if not self.node:
                raise ValueError("Map node requires 'node' field")
            if not self.collect:
                raise ValueError("Map node requires 'collect' field")

        if self.type == NodeType.RACE:
            if not self.candidates:
                raise ValueError("Race node requires 'candidates' field")
            if len(self.candidates) < 2:
                raise ValueError(
                    "Race node requires at least 2 candidates "
                    "(single candidate = use regular llm node)"
                )
            for i, candidate in enumerate(self.candidates):
                if not candidate.get("provider") and not candidate.get("model"):
                    raise ValueError(
                        f"Race candidate {i} must specify at least provider or model"
                    )

        return self
