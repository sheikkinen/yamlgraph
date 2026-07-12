"""Pydantic models and state definitions.

Framework models for error handling and generic reports.
State is now generated dynamically by state_builder.py.
"""

from yamlgraph.models.graph_schema import (
    EdgeConfig,
    GraphConfigSchema,
    NodeConfig,
    validate_graph_schema,
)
from yamlgraph.models.guard_schema import VerificationConfig
from yamlgraph.models.schemas import (
    ErrorType,
    GenericReport,
    GuardViolation,
    PipelineError,
    VerificationViolation,
)
from yamlgraph.models.state_builder import (
    build_state_class,
    create_initial_state,
)
from yamlgraph.verification import CountRangeClaim

__all__ = [
    # Framework models
    "ErrorType",
    "PipelineError",
    "VerificationViolation",
    "GuardViolation",
    "GenericReport",
    # Graph config schema
    "GraphConfigSchema",
    "NodeConfig",
    "VerificationConfig",
    "EdgeConfig",
    "validate_graph_schema",
    # Dynamic state generation
    "build_state_class",
    "create_initial_state",
    # Verification claims (FR-166)
    "CountRangeClaim",
]
