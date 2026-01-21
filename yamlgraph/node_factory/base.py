"""Base utilities for node factory.

Shared utilities for resolving classes and output models.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Type alias for dynamic state
GraphState = dict[str, Any]


def resolve_class(class_path: str) -> type:
    """Dynamically import and return a class from a module path.

    Args:
        class_path: Full path like "yamlgraph.models.GenericReport" or short name

    Returns:
        The class object
    """
    import importlib

    parts = class_path.rsplit(".", 1)
    if len(parts) != 2:
        # Try to find in yamlgraph.models.schemas
        try:
            from yamlgraph.models import schemas

            if hasattr(schemas, class_path):
                return getattr(schemas, class_path)
        except ImportError:
            pass
        raise ValueError(f"Invalid class path: {class_path}")

    module_path, class_name = parts
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def get_output_model_for_node(
    node_config: dict[str, Any],
    prompts_dir: Path | None = None,
    graph_path: Path | None = None,
    prompts_relative: bool = False,
) -> type | None:
    """Get output model for a node, checking inline schema if no explicit model.

    Priority:
    1. Explicit output_model in node config (class path)
    2. Inline schema in prompt YAML file
    3. None (raw string output)

    Args:
        node_config: Node configuration from YAML
        prompts_dir: Base prompts directory
        graph_path: Path to graph YAML file (for relative prompt resolution)
        prompts_relative: If True, resolve prompts relative to graph_path

    Returns:
        Pydantic model class or None
    """
    from yamlgraph.utils.prompts import resolve_prompt_path

    # 1. Check for explicit output_model
    if model_path := node_config.get("output_model"):
        return resolve_class(model_path)

    # 2. Check for inline schema in prompt YAML
    prompt_name = node_config.get("prompt")
    if prompt_name:
        try:
            from yamlgraph.schema_loader import load_schema_from_yaml

            yaml_path = resolve_prompt_path(
                prompt_name,
                prompts_dir=prompts_dir,
                graph_path=graph_path,
                prompts_relative=prompts_relative,
            )
            return load_schema_from_yaml(yaml_path)
        except FileNotFoundError:
            # Prompt file doesn't exist yet - will fail later
            pass

    # 3. No output model
    return None
