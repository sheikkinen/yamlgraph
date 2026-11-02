"""Pydantic schema for `type: subgraph` node configuration.

Moved out of node_schema.py when the FR-1155 decision-node fields pushed
that module over the 400-line split gate (FR-716 discipline: split at a
cohesive seam, never shim). SubgraphNodeConfig remains the single owner
of the mode Literal and the direct-mode mapping prohibition (FR-1060).
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


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
        if self.mode == "direct":
            # Presence, not truthiness: `input_mapping: {}` is a declaration
            # that direct mode has no boundary to map across, and accepting
            # it would contradict the reference and the diagnostic.
            present = [
                name
                for name in ("input_mapping", "output_mapping")
                if name in self.model_fields_set
            ]
            if present:
                raise ValueError(
                    f"mode=direct shares the parent state schema and does not "
                    f"support {', '.join(present)}"
                )
        return self
