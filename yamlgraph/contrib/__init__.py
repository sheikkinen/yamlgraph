"""Contrib utilities for YAMLGraph pipelines.

Shared utilities extracted from common pipeline patterns. These functions
eliminate copy-paste duplication across projects.

Modules:
- utils: Core utilities (to_serializable)
- progress: Skip/error reporting (SkipReport)
"""

from yamlgraph.contrib.progress import SkipReport
from yamlgraph.contrib.utils import to_serializable

__all__ = ["to_serializable", "SkipReport"]
