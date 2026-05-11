"""Project contract models for watcher2 multi-project routing."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator


def _validate_repo_relative_path(value: str, field_name: str) -> str:
    path_value = value.strip()
    if not path_value:
        raise ValueError(f"{field_name} must be non-empty")

    candidate = Path(path_value)
    if candidate.is_absolute():
        raise ValueError(f"{field_name} must be repo-relative, got absolute path")
    if ".." in candidate.parts:
        raise ValueError(f"{field_name} must not contain '..'")
    return path_value


class NinchatVoiceManifest(BaseModel):
    """Required manifest schema for projects/ninchat_voice/chaplain.yaml."""

    project: str
    branch_prefix: str
    work_dir: str
    test_cmd: str
    precommit_config: str
    fr_template: str
    architecture_doc: str

    @field_validator("project")
    @classmethod
    def _project_literal(cls, value: str) -> str:
        if value != "ninchat_voice":
            raise ValueError("project must be literal 'ninchat_voice'")
        return value

    @field_validator("branch_prefix", "test_cmd")
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        text = value.strip()
        if not text:
            raise ValueError(f"{info.field_name} must be non-empty")
        return text

    @field_validator("work_dir", "precommit_config", "fr_template", "architecture_doc")
    @classmethod
    def _repo_relative_paths(cls, value: str, info: Any) -> str:
        return _validate_repo_relative_path(value, info.field_name)


class ProjectContext(BaseModel):
    """Normalized project routing context propagated through watcher2."""

    project: str
    branch_prefix: str
    work_dir: str
    test_cmd: str
    precommit_config: str
    fr_template: str
    architecture_doc: str

    @field_validator("branch_prefix")
    @classmethod
    def _branch_prefix_non_empty(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("branch_prefix must be non-empty")
        return text

    @field_validator("work_dir", "fr_template", "architecture_doc")
    @classmethod
    def _required_repo_relative_paths(cls, value: str, info: Any) -> str:
        return _validate_repo_relative_path(value, info.field_name)

    @field_validator("precommit_config")
    @classmethod
    def _optional_repo_relative_path(cls, value: str) -> str:
        text = value.strip()
        if not text:
            return ""
        return _validate_repo_relative_path(text, "precommit_config")

    @field_validator("test_cmd")
    @classmethod
    def _optional_test_cmd(cls, value: str) -> str:
        return value.strip()


def yamlgraph_project_context() -> ProjectContext:
    """Return default context for the root yamlgraph intake lane."""
    return ProjectContext(
        project="yamlgraph",
        branch_prefix="feat/watcher2-",
        work_dir=".",
        test_cmd="",
        precommit_config="",
        fr_template="feature-requests/TEMPLATE.md",
        architecture_doc="ARCHITECTURE.md",
    )


def load_ninchat_voice_manifest(manifest_path: Path) -> ProjectContext:
    """Load and validate the ninchat_voice manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    raw = yaml.safe_load(manifest_path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError("Manifest content must be a mapping")

    manifest = NinchatVoiceManifest.model_validate(raw)
    return ProjectContext.model_validate(manifest.model_dump())
