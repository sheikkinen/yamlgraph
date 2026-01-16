"""Showcase package - LangGraph pipeline demonstration.

Framework for building LLM pipelines with YAML configuration.
State is now generated dynamically from graph config.
"""

from showcase.builder import build_resume_graph, build_showcase_graph, run_pipeline
from showcase.executor import execute_prompt, get_executor
from showcase.models import (
    ErrorType,
    GenericReport,
    PipelineError,
    build_state_class,
    create_initial_state,
)
from showcase.storage import ShowcaseDB

__all__ = [
    # Builder
    "build_showcase_graph",
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
    "ShowcaseDB",
]
