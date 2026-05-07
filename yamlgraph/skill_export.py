"""Portable skill export for YAMLGraph graphs (FR-348)."""

from __future__ import annotations

import shlex
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from yamlgraph.graph_loader import GraphConfig, load_graph_config
from yamlgraph.skill_export_writer import write_agent_markdown, write_skill_package
from yamlgraph.utils.prompts import resolve_prompt_path

_TYPE_MAP: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
}

_TYPE_EXAMPLES: dict[str, str] = {
    "string": "example",
    "integer": "1",
    "number": "1.0",
    "boolean": "true",
    "array": "[]",
    "object": "{}",
}


class SkillFormat(StrEnum):
    SKILL_MD = "skill-md"
    COPILOT = "copilot"
    CURSOR = "cursor"
    AGENT_MD = "agent-md"


class PackageSkill(BaseModel):
    model_config = ConfigDict(frozen=True)
    graph_path_or_dir: Path
    format: SkillFormat = SkillFormat.SKILL_MD
    output_dir: Path = Path("output")


class SkillPackage(BaseModel):
    model_config = ConfigDict(frozen=True)
    skill_name: str
    graph_path: Path
    target_dir: Path
    target_file: Path | None = None
    format: SkillFormat


class SkillExporter:
    def export(self, request: PackageSkill) -> SkillPackage:
        graph_path = self._resolve_graph_path(request.graph_path_or_dir)
        graph_config = self._load_valid_graph(graph_path)
        package_data = self._build_package_data(graph_path, graph_config)
        target_path = self._resolve_target_dir(
            output_dir=request.output_dir,
            skill_name=package_data["skill_name"],
            format_name=request.format,
        )
        self._assert_target_is_safe(target_path, request.format)
        if request.format == SkillFormat.AGENT_MD:
            write_agent_markdown(package_data, target_path)
        else:
            write_skill_package(package_data, target_path)
        return SkillPackage(
            skill_name=package_data["skill_name"],
            graph_path=graph_path,
            target_dir=target_path,
            format=request.format,
        )

    def _resolve_graph_path(self, graph_path_or_dir: Path) -> Path:
        path = Path(graph_path_or_dir).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"Graph path does not exist: {path}")
        if path.is_file():
            return path
        if path.is_dir():
            graph_yaml = path / "graph.yaml"
            if graph_yaml.exists():
                return graph_yaml.resolve()
            yaml_files = sorted(path.glob("*.yaml"))
            if len(yaml_files) == 1:
                return yaml_files[0].resolve()
            raise ValueError(
                f"Directory does not resolve to a single graph YAML: {path}"
            )
        raise ValueError(f"Unsupported graph path: {path}")

    def _load_valid_graph(self, graph_path: Path) -> GraphConfig:
        try:
            return load_graph_config(graph_path)
        except Exception as exc:
            raise ValueError(f"Invalid graph YAML: {graph_path} ({exc})") from exc

    def _resolve_target_dir(
        self, output_dir: Path, skill_name: str, format_name: SkillFormat
    ) -> Path:
        base = Path(output_dir).expanduser().resolve()
        if format_name == SkillFormat.SKILL_MD:
            return base / skill_name
        if format_name == SkillFormat.COPILOT:
            return base / ".copilot" / "skills" / skill_name
        if format_name == SkillFormat.CURSOR:
            return base / ".cursor" / "skills" / skill_name
        if format_name == SkillFormat.AGENT_MD:
            return base / ".github" / "agents" / f"{skill_name}.agent.md"
        raise ValueError(f"Unsupported format: {format_name}")

    def _assert_target_is_safe(
        self, target_path: Path, format_name: SkillFormat
    ) -> None:
        if not target_path.exists():
            return
        if format_name == SkillFormat.AGENT_MD:
            raise FileExistsError(f"Output target already exists: {target_path}")
        if not target_path.is_dir():
            raise FileExistsError(
                f"Output target exists and is not a directory: {target_path}"
            )
        if any(target_path.iterdir()):
            raise FileExistsError(
                f"Output target already exists and is not empty: {target_path}"
            )

    def _build_package_data(
        self, graph_path: Path, graph_config: GraphConfig
    ) -> dict[str, Any]:
        raw_config = graph_config.raw_config
        nodes = raw_config.get("nodes", {}) if isinstance(raw_config, dict) else {}
        state = raw_config.get("state", {}) if isinstance(raw_config, dict) else {}
        if not isinstance(nodes, dict):
            nodes = {}
        if not isinstance(state, dict):
            state = {}

        output_keys = self._extract_output_keys(nodes)
        input_keys = sorted(k for k in state if k not in output_keys)
        input_properties: dict[str, dict[str, str]] = {}
        input_descriptions: dict[str, str] = {}
        for key in input_keys:
            json_type, description_text = self._state_field_spec(state.get(key))
            input_properties[key] = {"type": json_type, "description": description_text}
            input_descriptions[key] = description_text

        output_properties = {
            key: {"type": self._state_field_spec(state.get(key))[0]}
            for key in sorted(output_keys)
        }
        input_schema = {
            "type": "object",
            "properties": input_properties,
            "required": input_keys,
        }
        output_schema = {
            "type": "object",
            "properties": output_properties,
            "required": sorted(output_keys),
        }

        return {
            "skill_name": str(graph_config.name or graph_path.stem),
            "description": str(graph_config.description or "No description provided."),
            "input_schema": input_schema,
            "output_schema": output_schema,
            "input_descriptions": input_descriptions,
            "prompt_references": self._load_prompt_references(
                graph_path, graph_config, nodes
            ),
            "run_command": self._build_run_command(graph_path, input_schema),
        }

    def _extract_output_keys(self, nodes: dict[str, Any]) -> set[str]:
        return {
            state_key
            for node in nodes.values()
            if isinstance(node, dict)
            for state_key in [node.get("state_key")]
            if isinstance(state_key, str) and state_key
        }

    def _state_field_spec(self, field_value: Any) -> tuple[str, str]:
        if isinstance(field_value, dict):
            raw_type = str(field_value.get("type", "str"))
            description = str(
                field_value.get("description", "No description provided.")
            )
        elif isinstance(field_value, str):
            raw_type = field_value
            description = "No description provided."
        else:
            raw_type = "str"
            description = "No description provided."
        base = raw_type.split("[", 1)[0].strip()
        return _TYPE_MAP.get(base, "string"), description

    def _load_prompt_references(
        self, graph_path: Path, graph_config: GraphConfig, nodes: dict[str, Any]
    ) -> dict[str, str]:
        prompt_names = sorted(
            {
                prompt
                for node in nodes.values()
                if isinstance(node, dict)
                for prompt in [node.get("prompt")]
                if isinstance(prompt, str) and prompt
            }
        )
        if not prompt_names:
            return {}
        prompts_dir = (
            Path(graph_config.prompts_dir)
            if graph_config.prompts_dir is not None
            else None
        )
        references: dict[str, str] = {}
        for prompt_name in prompt_names:
            path = resolve_prompt_path(
                prompt_name=prompt_name,
                prompts_dir=prompts_dir,
                graph_path=graph_path,
                prompts_relative=graph_config.prompts_relative,
            )
            prompt_data = self._load_prompt_yaml(path)
            references[prompt_name] = self._render_prompt_reference(
                prompt_name, prompt_data
            )
        return references

    def _load_prompt_yaml(self, path: Path) -> dict[str, Any]:
        try:
            content = yaml.safe_load(path.read_text())
        except Exception as exc:
            raise ValueError(f"Failed to read prompt YAML: {path} ({exc})") from exc
        if not isinstance(content, dict):
            raise ValueError(f"Prompt YAML must be an object: {path}")
        return content

    def _render_prompt_reference(
        self, prompt_name: str, prompt_data: dict[str, Any]
    ) -> str:
        description = str(prompt_data.get("description", "No description provided."))
        template = prompt_data.get("template")
        if template is None:
            template = prompt_data.get("user", "")
        return (
            f"# {prompt_name}\n\n"
            "## Description\n\n"
            f"{description}\n\n"
            "## Template\n\n"
            "```text\n"
            f"{template}\n"
            "```\n"
        )

    def _build_run_command(self, graph_path: Path, input_schema: dict[str, Any]) -> str:
        properties = input_schema.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        command_parts = ["yamlgraph", "graph", "run", shlex.quote(str(graph_path))]
        for key in sorted(properties):
            field = properties.get(key, {})
            if not isinstance(field, dict):
                field = {}
            example = _TYPE_EXAMPLES.get(str(field.get("type", "string")), "example")
            command_parts.extend(["--var", shlex.quote(f"{key}={example}")])
        return " ".join(command_parts)


def export_skill(
    graph_path_or_dir: str | Path,
    *,
    format: str = "skill-md",
    output_dir: str | Path = "output",
) -> SkillPackage:
    valid_formats = {f.value for f in SkillFormat}
    if format not in valid_formats:
        allowed = ", ".join(sorted(valid_formats))
        raise ValueError(f"Unsupported format: {format}. Expected one of: {allowed}.")
    try:
        request = PackageSkill(
            graph_path_or_dir=Path(graph_path_or_dir),
            format=format,
            output_dir=Path(output_dir),
        )
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    return SkillExporter().export(request)


__all__ = ["export_skill", "PackageSkill", "SkillExporter", "SkillPackage"]
