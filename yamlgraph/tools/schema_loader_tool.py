"""Built-in schema loader tool (`type: schema_loader`)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SchemaLoaderToolConfig:
    """Configuration for schema loader tools."""

    state_key: str
    path: str | None = None
    paths_from_state: str | None = None
    schema_dir: str | None = None
    suffix: str = ".yaml"
    deduplicate_by: str = "id"
    merge_mode: str = "additive"


def parse_schema_loader_tools(
    tools_config: dict[str, Any],
) -> dict[str, SchemaLoaderToolConfig]:
    """Parse schema_loader tools from YAML tools section."""
    registry: dict[str, SchemaLoaderToolConfig] = {}

    for name, raw_config in tools_config.items():
        if (
            not isinstance(raw_config, dict)
            or raw_config.get("type") != "schema_loader"
        ):
            continue

        path = raw_config.get("path")
        paths_from_state = raw_config.get("paths_from_state")
        if bool(path) == bool(paths_from_state):
            raise ValueError(
                f"schema_loader tool '{name}' must set exactly one of 'path' or "
                "'paths_from_state'"
            )

        state_key = raw_config.get("state_key")
        if not isinstance(state_key, str) or not state_key:
            raise ValueError(
                f"schema_loader tool '{name}' must define non-empty string 'state_key'"
            )

        schema_dir = raw_config.get("schema_dir")
        if paths_from_state and (not isinstance(schema_dir, str) or not schema_dir):
            raise ValueError(
                f"schema_loader tool '{name}' must define non-empty 'schema_dir' when "
                "'paths_from_state' is used"
            )

        suffix = raw_config.get("suffix", ".yaml")
        if not isinstance(suffix, str) or not suffix:
            raise ValueError(
                f"schema_loader tool '{name}' has invalid 'suffix' (must be non-empty str)"
            )

        deduplicate_by = raw_config.get("deduplicate_by", "id")
        if not isinstance(deduplicate_by, str) or not deduplicate_by:
            raise ValueError(
                f"schema_loader tool '{name}' has invalid 'deduplicate_by' "
                "(must be non-empty str)"
            )

        merge_mode = raw_config.get("merge_mode", "additive")
        if merge_mode != "additive":
            raise ValueError(
                f"schema_loader tool '{name}' has unsupported merge_mode '{merge_mode}' "
                "(only 'additive' is supported)"
            )

        registry[name] = SchemaLoaderToolConfig(
            state_key=state_key,
            path=path,
            paths_from_state=paths_from_state,
            schema_dir=schema_dir,
            suffix=suffix,
            deduplicate_by=deduplicate_by,
            merge_mode=merge_mode,
        )

    return registry


def _resolve_schema_path(
    graph_root: Path, relative_path: str, *, tool_name: str
) -> Path:
    resolved = (graph_root / relative_path).resolve()
    try:
        resolved.relative_to(graph_root)
    except ValueError:
        raise ValueError(
            f"schema_loader tool '{tool_name}': path '{relative_path}' escapes graph "
            f"directory '{graph_root}' (resolved: {resolved})"
        ) from None
    return resolved


def _load_yaml_schema(
    graph_root: Path, relative_path: str, *, tool_name: str
) -> dict[str, Any]:
    schema_path = _resolve_schema_path(graph_root, relative_path, tool_name=tool_name)
    if not schema_path.exists():
        raise FileNotFoundError(
            f"schema_loader tool '{tool_name}': schema file not found: {schema_path}"
        )

    with open(schema_path, encoding="utf-8") as f:
        try:
            loaded = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(
                f"schema_loader tool '{tool_name}': invalid YAML at {schema_path}: {exc}"
            ) from exc

    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise TypeError(
            f"schema_loader tool '{tool_name}': schema file {schema_path} must contain "
            f"a mapping, got {type(loaded).__name__}"
        )
    return loaded


def _coerce_state(
    state: dict[str, Any] | None,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(state, dict):
        return state
    return kwargs


def _deduplicate_fields(
    fields: list[Any],
    *,
    deduplicate_by: str,
    tool_name: str,
) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[Any] = set()

    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            raise TypeError(
                f"schema_loader tool '{tool_name}': field at index {index} must be a "
                f"mapping, got {type(field).__name__}"
            )
        if deduplicate_by not in field:
            raise KeyError(
                f"schema_loader tool '{tool_name}': field at index {index} is missing "
                f"deduplicate key '{deduplicate_by}'"
            )

        dedupe_value = field[deduplicate_by]
        if dedupe_value in seen:
            continue
        seen.add(dedupe_value)
        deduped.append(field)

    return deduped


def _build_single_mode(
    name: str,
    config: SchemaLoaderToolConfig,
    *,
    graph_root: Path,
) -> Callable[[dict[str, Any] | None], dict[str, Any]]:
    if config.path is None:
        raise ValueError(
            f"schema_loader tool '{name}' is misconfigured: missing 'path' for single mode"
        )

    def _single_mode(state: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        _ = state
        return {
            config.state_key: _load_yaml_schema(graph_root, config.path, tool_name=name)
        }

    return _single_mode


def _build_merge_mode(
    name: str,
    config: SchemaLoaderToolConfig,
    *,
    graph_root: Path,
) -> Callable[[dict[str, Any] | None], dict[str, Any]]:
    if config.paths_from_state is None or config.schema_dir is None:
        raise ValueError(
            f"schema_loader tool '{name}' is misconfigured: merge mode requires "
            "'paths_from_state' and 'schema_dir'"
        )

    def _merge_mode(
        state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        effective_state = _coerce_state(state, kwargs)
        topics = effective_state.get(config.paths_from_state)
        if not isinstance(topics, list):
            raise TypeError(
                f"schema_loader tool '{name}': expected state['{config.paths_from_state}'] "
                f"to be list, got {type(topics).__name__}"
            )

        existing_schema_raw = effective_state.get(config.state_key, {})
        if existing_schema_raw is None:
            existing_schema_raw = {}
        if not isinstance(existing_schema_raw, dict):
            raise TypeError(
                f"schema_loader tool '{name}': expected state['{config.state_key}'] "
                f"to be dict when present, got {type(existing_schema_raw).__name__}"
            )

        existing_fields_raw = existing_schema_raw.get("fields", [])
        if existing_fields_raw is None:
            existing_fields_raw = []
        if not isinstance(existing_fields_raw, list):
            raise TypeError(
                f"schema_loader tool '{name}': existing schema fields must be list, got "
                f"{type(existing_fields_raw).__name__}"
            )

        merged_fields: list[Any] = list(existing_fields_raw)
        for index, topic in enumerate(topics):
            if not isinstance(topic, str) or not topic:
                raise TypeError(
                    f"schema_loader tool '{name}': topic at index {index} must be "
                    f"non-empty string, got {topic!r}"
                )

            relative_path = str(Path(config.schema_dir) / f"{topic}{config.suffix}")
            topic_schema = _load_yaml_schema(
                graph_root,
                relative_path,
                tool_name=name,
            )
            topic_fields = topic_schema.get("fields", [])
            if topic_fields is None:
                topic_fields = []
            if not isinstance(topic_fields, list):
                raise TypeError(
                    f"schema_loader tool '{name}': schema '{relative_path}' has non-list "
                    f"'fields' ({type(topic_fields).__name__})"
                )
            merged_fields.extend(topic_fields)

        merged_schema = dict(existing_schema_raw)
        merged_schema["fields"] = _deduplicate_fields(
            merged_fields,
            deduplicate_by=config.deduplicate_by,
            tool_name=name,
        )
        return {config.state_key: merged_schema}

    return _merge_mode


def build_schema_loader_tool(
    name: str,
    config: SchemaLoaderToolConfig,
    *,
    graph_root: Path,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Build runtime callable for a schema loader tool."""
    graph_root = graph_root.resolve()

    if config.path:
        return _build_single_mode(name, config, graph_root=graph_root)
    return _build_merge_mode(name, config, graph_root=graph_root)
