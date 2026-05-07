"""Writers for portable skill package artifacts."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml


def write_skill_package(package_data: dict[str, Any], target_dir: Path) -> None:
    """Write all skill package artifacts into target_dir atomically."""
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".{target_dir.name}-", dir=str(target_dir.parent))
    )
    try:
        _write_skill_md(staging_dir, package_data)
        _write_run_script(staging_dir, package_data)
        _write_references(staging_dir, package_data)
        _write_schema(staging_dir, package_data)

        if target_dir.exists():
            target_dir.rmdir()
        staging_dir.rename(target_dir)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise


def _write_skill_md(package_root: Path, package_data: dict[str, Any]) -> None:
    input_schema = package_data["input_schema"]
    output_schema = package_data["output_schema"]
    input_descriptions = package_data["input_descriptions"]
    run_command = package_data["run_command"]

    input_lines: list[str] = []
    for key in sorted(input_schema["properties"].keys()):
        schema_type = input_schema["properties"][key]["type"]
        description = input_descriptions.get(key, "No description provided.")
        input_lines.append(f"- `{key}` (`{schema_type}`): {description}")

    output_lines: list[str] = []
    for key in sorted(output_schema["properties"].keys()):
        schema_type = output_schema["properties"][key]["type"]
        output_lines.append(f"- `{key}` (`{schema_type}`)")

    content = (
        f"# {package_data['skill_name']}\n\n"
        f"{package_data['description']}\n\n"
        "## Inputs\n\n"
        f"{chr(10).join(input_lines)}\n\n"
        "## Outputs\n\n"
        f"{chr(10).join(output_lines)}\n\n"
        "## Run\n\n"
        "```bash\n"
        f"{run_command}\n"
        "```\n"
    )
    (package_root / "SKILL.md").write_text(content)


def _write_run_script(package_root: Path, package_data: dict[str, Any]) -> None:
    run_command = package_data["run_command"]
    script_path = package_root / "scripts" / "run.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(f"#!/usr/bin/env bash\nset -euo pipefail\n\n{run_command}\n")
    script_path.chmod(script_path.stat().st_mode | 0o111)


def _write_references(package_root: Path, package_data: dict[str, Any]) -> None:
    references_dir = package_root / "references"
    references_dir.mkdir(parents=True, exist_ok=True)
    references: dict[str, str] = package_data["prompt_references"]
    for prompt_name in sorted(references.keys()):
        safe_name = prompt_name.replace("/", "__")
        (references_dir / f"{safe_name}.md").write_text(references[prompt_name])


def _write_schema(package_root: Path, package_data: dict[str, Any]) -> None:
    assets_dir = package_root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "input": package_data["input_schema"],
        "output": package_data["output_schema"],
    }
    (assets_dir / "schema.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True)
    )


def write_agent_md_file(package_data: dict[str, Any], target_file: Path) -> None:
    """Write a single .agent.md artifact for GitHub agent mode."""
    target_file.parent.mkdir(parents=True, exist_ok=True)
    content = _build_agent_md_content(package_data)
    with target_file.open("x") as handle:
        handle.write(content)


def _build_agent_md_content(package_data: dict[str, Any]) -> str:
    input_schema = package_data["input_schema"]
    input_descriptions = package_data["input_descriptions"]
    skill_name = package_data["skill_name"]
    description = package_data["description"]

    frontmatter_payload = {
        "description": description,
        "tools": ["yamlgraph/*"],
        "model": "Claude Sonnet 4",
    }
    frontmatter = yaml.safe_dump(
        frontmatter_payload, sort_keys=False, default_flow_style=False
    ).strip()

    input_lines: list[str] = []
    for key in sorted(input_schema["properties"].keys()):
        schema_type = input_schema["properties"][key]["type"]
        field_description = input_descriptions.get(key, "No description provided.")
        input_lines.append(f"- `{key}` (`{schema_type}`): {field_description}")
    if not input_lines:
        input_lines.append("- None")

    body = (
        f"# {skill_name}\n\n"
        f"{description}\n\n"
        "## Inputs\n\n"
        f"{chr(10).join(input_lines)}\n\n"
        "## Invocation\n\n"
        f"Invoke this agent with `@{skill_name}` and include all required inputs."
    )

    return f"---\n{frontmatter}\n---\n\n{body}\n"
