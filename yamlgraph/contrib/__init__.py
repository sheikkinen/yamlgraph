"""Contrib utilities for YAMLGraph pipelines.

Shared utilities extracted from common pipeline patterns. These functions
eliminate copy-paste duplication across projects.

Modules:
- utils: Core utilities (get_map_result, to_serializable)
- progress: Skip/error reporting (SkipReport)
"""

from yamlgraph.contrib.progress import SkipReport
from yamlgraph.contrib.utils import get_map_result, to_serializable

__all__ = ["get_map_result", "to_serializable", "SkipReport"]
