"""Unified prompt loading and path resolution.

This module consolidates prompt loading logic used by executor.py
and node_factory.py into a single, testable module.

Search order for prompts:
1. If prompts_dir specified: prompts_dir/{prompt_name}.yaml
2. If prompts_relative + graph_path: graph_path.parent/{prompt_name}.yaml
3. Default: PROMPTS_DIR/{prompt_name}.yaml
4. Fallback: {parent}/prompts/{basename}.yaml (external examples)
"""

from pathlib import Path

import yaml

from yamlgraph.config import PROMPTS_DIR


def resolve_prompt_path(
    prompt_name: str,
    prompts_dir: Path | None = None,
    graph_path: Path | None = None,
    prompts_relative: bool = False,
) -> Path:
    """Resolve a prompt name to its full YAML file path.

    Resolution order:
    1. If prompts_dir specified: prompts_dir/{prompt_name}.yaml
    2. If prompts_relative and graph_path: graph_path.parent/{prompt_name}.yaml
    3. Default: PROMPTS_DIR/{prompt_name}.yaml
    4. Fallback: {parent}/prompts/{basename}.yaml (external examples)

    Args:
        prompt_name: Prompt name like "greet" or "prompts/opening"
        prompts_dir: Explicit prompts directory override (takes precedence)
        graph_path: Path to the graph YAML file (for relative resolution)
        prompts_relative: If True, resolve relative to graph_path.parent

    Returns:
        Path to the YAML file

    Raises:
        FileNotFoundError: If prompt file doesn't exist
        ValueError: If prompts_relative=True but graph_path not provided

    Examples:
        >>> resolve_prompt_path("greet")
        PosixPath('/path/to/prompts/greet.yaml')

        >>> resolve_prompt_path("prompts/opening", graph_path=Path("graphs/demo.yaml"), prompts_relative=True)
        PosixPath('/path/to/graphs/prompts/opening.yaml')
    """
    # Validate prompts_relative requires graph_path
    if prompts_relative and graph_path is None and prompts_dir is None:
        raise ValueError("graph_path required when prompts_relative=True")

    # 1. Explicit prompts_dir takes precedence
    if prompts_dir is not None:
        prompts_dir = Path(prompts_dir)
        yaml_path = prompts_dir / f"{prompt_name}.yaml"
        if yaml_path.exists():
            return yaml_path
        # Fall through to other resolution methods

    # 2. Graph-relative resolution
    if prompts_relative and graph_path is not None:
        graph_dir = Path(graph_path).parent
        yaml_path = graph_dir / f"{prompt_name}.yaml"
        if yaml_path.exists():
            return yaml_path
        # Fall through to default

    # 3. Default: use global PROMPTS_DIR
    default_dir = PROMPTS_DIR if prompts_dir is None else prompts_dir
    yaml_path = Path(default_dir) / f"{prompt_name}.yaml"
    if yaml_path.exists():
        return yaml_path

    # 4. Fallback: external example location {parent}/prompts/{basename}.yaml
    parts = prompt_name.rsplit("/", 1)
    if len(parts) == 2:
        parent_dir, basename = parts
        alt_path = Path(parent_dir) / "prompts" / f"{basename}.yaml"
        if alt_path.exists():
            return alt_path

    raise FileNotFoundError(f"Prompt not found: {yaml_path}")


def load_prompt(
    prompt_name: str,
    prompts_dir: Path | None = None,
    graph_path: Path | None = None,
    prompts_relative: bool = False,
) -> dict:
    """Load a YAML prompt template.

    Args:
        prompt_name: Name of the prompt file (without .yaml extension)
        prompts_dir: Optional prompts directory override
        graph_path: Path to the graph YAML file (for relative resolution)
        prompts_relative: If True, resolve relative to graph_path.parent

    Returns:
        Dictionary with prompt content (typically 'system' and 'user' keys)

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    path = resolve_prompt_path(
        prompt_name,
        prompts_dir=prompts_dir,
        graph_path=graph_path,
        prompts_relative=prompts_relative,
    )

    with open(path) as f:
        return yaml.safe_load(f)


def load_prompt_path(
    prompt_name: str,
    prompts_dir: Path | None = None,
    graph_path: Path | None = None,
    prompts_relative: bool = False,
) -> tuple[Path, dict]:
    """Load a prompt and return both path and content.

    Useful when you need both the file path (for schema loading)
    and the content (for prompt execution).

    Args:
        prompt_name: Name of the prompt file (without .yaml extension)
        prompts_dir: Optional prompts directory override
        graph_path: Path to the graph YAML file (for relative resolution)
        prompts_relative: If True, resolve relative to graph_path.parent

    Returns:
        Tuple of (path, content_dict)

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    path = resolve_prompt_path(
        prompt_name,
        prompts_dir=prompts_dir,
        graph_path=graph_path,
        prompts_relative=prompts_relative,
    )

    with open(path) as f:
        content = yaml.safe_load(f)

    return path, content


__all__ = ["resolve_prompt_path", "load_prompt", "load_prompt_path"]
