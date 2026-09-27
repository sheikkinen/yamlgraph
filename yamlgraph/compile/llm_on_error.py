"""FR-1124: top-level ``llm`` error policy resolution at the compile seam.

Precedence: node ``on_error`` -> graph ``defaults.on_error`` -> ``fail``.
Router, race and map sub-nodes are compiled elsewhere and keep their own
policies; this module only sees nodes whose type is ``llm``.
"""

from __future__ import annotations

from typing import Any

from yamlgraph.compile.node_otel import node_config_get
from yamlgraph.constants import ErrorHandler, NodeType


def resolve_llm_on_error(node_config: Any, defaults: dict[str, Any]) -> Any:
    """Return ``node_config`` with ``on_error`` resolved for type ``llm``."""
    if node_config_get(node_config, "type", NodeType.LLM) != NodeType.LLM:
        return node_config
    policy = (
        node_config.get("on_error")
        or defaults.get("on_error")
        or ErrorHandler.FAIL.value
    )
    return {**node_config, "on_error": policy}
