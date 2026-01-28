"""YamlGraph - YAML-first LLM pipeline framework.

Framework for building LLM pipelines with YAML configuration.
State is generated dynamically from graph config.
"""

from pathlib import Path

from yamlgraph.builder import build_graph, build_resume_graph, run_pipeline
from yamlgraph.executor import execute_prompt, get_executor
from yamlgraph.models import (
    ErrorType,
    GenericReport,
    PipelineError,
    build_state_class,
    create_initial_state,
)
from yamlgraph.storage import YamlGraphDB


def get_schema_path() -> Path:
    """Get path to the bundled JSON Schema for graph YAML files.

    Returns:
        Path to the bundled graph-v1.json schema file.
    """
    return Path(__file__).parent / "schemas" / "graph-v1.json"


__all__ = [
    # Builder
    "build_graph",
    "build_resume_graph",
    "run_pipeline",
    # Executor
    "execute_prompt",
    "get_executor",
    # Framework models
    "ErrorType",
    "PipelineError",
    "GenericReport",
    # Dynamic state
    "build_state_class",
    "create_initial_state",
    # Storage
    "YamlGraphDB",
    # Schema
    "get_schema_path",
]
