"""Unified prompt loading and path resolution.

This module consolidates prompt loading logic used by executor.py
and node_factory.py into a single, testable module.

Search order for prompts:
1. If prompts_relative + prompts_dir + graph_path: graph_path.parent/prompts_dir/{prompt_name}.yaml
2. If prompts_dir specified: prompts_dir/{prompt_name}.yaml
3. If prompts_relative + graph_path: graph_path.parent/{prompt_name}.yaml
4. Default: PROMPTS_DIR/{prompt_name}.yaml
5. Fallback: {parent}/prompts/{basename}.yaml (external examples)
"""

import logging
from pathlib import Path

import yaml

from yamlgraph.config import PROMPTS_DIR

logger = logging.getLogger(__name__)


def check_messages_contract(content: object, prompt_name: str) -> None:
    """FR-747: raise the contract when a prompt uses a `messages:` role list.

    F3 (binding): detection keys on a top-level `messages:` key in the
    PARSED YAML combined with ABSENT `system:`/`user:` — both conditions,
    parsed-structure level, never text grep. A `messages` variable inside
    a valid prompt never fires.
    """
    if (
        isinstance(content, dict)
        and "messages" in content
        and "system" not in content
        and "user" not in content
    ):
        raise ValueError(
            f"Prompt '{prompt_name}' uses 'messages:' role list — YAMLGraph "
            "prompts use top-level 'system:' and 'user:' keys "
            "(see reference/prompt-yaml.md)."
        )


def _resolve_graph_relative_with_dir(
    prompt_name: str, graph_path: Path, prompts_dir: Path
) -> Path | None:
    """Strategy 1: graph_path.parent / prompts_dir / {prompt_name}.yaml"""
    yaml_path = graph_path.parent / prompts_dir / f"{prompt_name}.yaml"
    return yaml_path if yaml_path.exists() else None


def _resolve_explicit_dir(prompt_name: str, prompts_dir: Path) -> Path | None:
    """Strategy 2: prompts_dir / {prompt_name}.yaml"""
    yaml_path = prompts_dir / f"{prompt_name}.yaml"
    return yaml_path if yaml_path.exists() else None


def _resolve_graph_relative(prompt_name: str, graph_path: Path) -> Path | None:
    """Strategy 3: graph_path.parent / {prompt_name}.yaml"""
    yaml_path = graph_path.parent / f"{prompt_name}.yaml"
    return yaml_path if yaml_path.exists() else None


def _resolve_default(prompt_name: str) -> Path | None:
    """Strategy 4: PROMPTS_DIR / {prompt_name}.yaml"""
    yaml_path = PROMPTS_DIR / f"{prompt_name}.yaml"
    return yaml_path if yaml_path.exists() else None


def _resolve_external_fallback(prompt_name: str) -> Path | None:
    """Strategy 5: {parent}/prompts/{basename}.yaml for external examples"""
    parts = prompt_name.rsplit("/", 1)
    if len(parts) == 2:
        parent_dir, basename = parts
        yaml_path = Path(parent_dir) / "prompts" / f"{basename}.yaml"
        return yaml_path if yaml_path.exists() else None
    return None


def resolve_prompt_path(
    prompt_name: str,
    prompts_dir: Path | None = None,
    graph_path: Path | None = None,
    prompts_relative: bool = False,
) -> Path:
    """Resolve a prompt name to its full YAML file path.

    Resolution order:
    1. If prompts_relative + prompts_dir + graph_path: graph_path.parent/prompts_dir/{prompt_name}.yaml
    2. If prompts_dir specified: prompts_dir/{prompt_name}.yaml
    3. If prompts_relative + graph_path: graph_path.parent/{prompt_name}.yaml
    4. Default: PROMPTS_DIR/{prompt_name}.yaml
    5. Fallback: {parent}/prompts/{basename}.yaml (external examples)

    Args:
        prompt_name: Prompt name like "greet" or "prompts/opening"
        prompts_dir: Explicit prompts directory (combined with graph_path if prompts_relative=True)
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

        >>> resolve_prompt_path("opening", prompts_dir="prompts", graph_path=Path("graphs/demo.yaml"), prompts_relative=True)
        PosixPath('/path/to/graphs/prompts/opening.yaml')
    """
    # Validation
    if prompts_relative and graph_path is None and prompts_dir is None:
        raise ValueError("graph_path required when prompts_relative=True")

    if prompts_relative and graph_path is None and prompts_dir is not None:
        logger.warning(
            f"prompts_relative=True but graph_path is None — "
            f"falling back to prompts_dir '{prompts_dir}' without graph-relative resolution"
        )

    # Build strategy list based on config
    strategies: list[tuple[str, Path | None]] = []

    if prompts_relative and prompts_dir is not None and graph_path is not None:
        strategies.append(
            (
                "graph-relative+dir",
                _resolve_graph_relative_with_dir(
                    prompt_name, Path(graph_path), Path(prompts_dir)
                ),
            )
        )

    if prompts_dir is not None:
        strategies.append(
            (
                "explicit-dir",
                _resolve_explicit_dir(prompt_name, Path(prompts_dir)),
            )
        )

    if prompts_relative and graph_path is not None:
        strategies.append(
            (
                "graph-relative",
                _resolve_graph_relative(prompt_name, Path(graph_path)),
            )
        )

    strategies.append(("default", _resolve_default(prompt_name)))
    strategies.append(("external-fallback", _resolve_external_fallback(prompt_name)))

    # Return first match
    for name, path in strategies:
        if path:
            logger.debug(f"Prompt resolved via {name}: {path}")
            return path

    raise FileNotFoundError(f"Prompt not found: {prompt_name}")


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
        ValueError: If the prompt uses a 'messages:' role list (FR-747)
    """
    path = resolve_prompt_path(
        prompt_name,
        prompts_dir=prompts_dir,
        graph_path=graph_path,
        prompts_relative=prompts_relative,
    )

    with open(path, encoding="utf-8") as f:
        content = yaml.safe_load(f)

    check_messages_contract(content, prompt_name)
    return content


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

    with open(path, encoding="utf-8") as f:
        content = yaml.safe_load(f)

    check_messages_contract(content, prompt_name)
    return path, content


__all__ = [
    "check_messages_contract",
    "load_prompt",
    "load_prompt_path",
    "resolve_prompt_path",
]
