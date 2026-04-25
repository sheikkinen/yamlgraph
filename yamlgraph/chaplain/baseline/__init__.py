"""Baseline checkpointing infrastructure for watcher2 (FR-277).

This module provides deterministic hash-based caching for watcher2 daemon
to prevent redundant processing of unchanged source files.
"""

# Export public API for future watcher2 integration
from .builder import BaselineBuilder
from .graph import load_baseline_graph
from .integration import prepare_watcher2_import
from .manifest import validate_manifest_schema
from .retention import cleanup_old_baselines
from .schema import BaselineState, BaselineSummaryMeta
from .state import build_baseline_state
from .summary import SummaryCache

__all__ = [
    "BaselineBuilder",
    "BaselineState",
    "BaselineSummaryMeta",
    "SummaryCache",
    "build_baseline_state",
    "cleanup_old_baselines",
    "load_baseline_graph",
    "prepare_watcher2_import",
    "validate_manifest_schema",
]
