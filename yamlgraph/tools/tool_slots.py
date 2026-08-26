"""Invocation-time tool-slot binding (FR-892).

A graph ``tools:`` entry may declare ``slot: true`` with a ``contract:``
block; the caller binds an FR-768 tool manifest at invocation
(``--tool SLOT=manifest.yaml``). Resolution replaces each slot entry with
a ``{"manifest": path}`` entry consumed by the existing FR-768 expansion
— translation and execution reuse the existing runtimes; no new engine.

All contaminated bindings fail closed with ToolSlotBindingError BEFORE
any node executes (judgement R-1/R-6).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from yamlgraph.tools.manifest import ToolManifest, translate_manifest

_SHELL_PLACEHOLDER = re.compile(r"\{(\w+)\}")


class ToolSlotBindingError(ValueError):
    """A tool-slot binding failed preflight validation (FR-892)."""


def parse_tool_bindings(raw: list[str]) -> dict[str, str]:
    """Parse repeatable CLI ``--tool NAME=PATH`` values.

    Raises:
        ToolSlotBindingError: Malformed entry or duplicate slot name.
    """
    bindings: dict[str, str] = {}
    for entry in raw:
        name, sep, path = entry.partition("=")
        if not sep or not name.strip() or not path.strip():
            raise ToolSlotBindingError(f"--tool expects NAME=PATH, got: '{entry}'")
        name = name.strip()
        if name in bindings:
            raise ToolSlotBindingError(f"Duplicate --tool binding for '{name}'")
        bindings[name] = path.strip()
    return bindings


def _check_contract(
    slot_name: str, contract: dict[str, Any], manifest: ToolManifest, path: Path
) -> None:
    """Mechanical contract checks: runtime allowlist + shell arg placeholders."""
    runtimes = contract.get("runtimes")
    if runtimes and manifest.runtime.type not in runtimes:
        raise ToolSlotBindingError(
            f"Slot '{slot_name}': manifest '{path}' has runtime "
            f"'{manifest.runtime.type}', contract allows {runtimes}"
        )
    args = contract.get("args") or []
    if args and manifest.runtime.type == "shell":
        placeholders = set(_SHELL_PLACEHOLDER.findall(manifest.runtime.command))
        missing = [a for a in args if a not in placeholders]
        if missing:
            raise ToolSlotBindingError(
                f"Slot '{slot_name}': contract args {missing} missing from "
                f"shell command placeholders in manifest '{path}'"
            )
    # python/graph runtimes: args are duck-typed at invocation; the
    # runtime-type allowlist above is the mechanical check surface.


def resolve_tool_slots(
    tools: dict[str, Any],
    bindings: dict[str, str] | None,
    base_dir: Path,
) -> dict[str, Any]:
    """Resolve ``slot: true`` tool entries against invocation bindings.

    Args:
        tools: Raw ``tools:`` section from graph YAML.
        bindings: Slot name → manifest path (CWD/base_dir-relative).
        base_dir: Resolution base for relative manifest paths.

    Returns:
        Tools dict with each slot replaced by ``{"manifest": abs_path}``
        for FR-768 expansion; non-slot entries pass through unchanged.

    Raises:
        ToolSlotBindingError: Missing binding for a declared slot, binding
            to an undeclared slot, missing/invalid manifest file, runtime
            type outside the contract, or contract args unsatisfied.
    """
    if not tools:
        if bindings:
            raise ToolSlotBindingError(
                f"--tool bindings given but graph declares no tools: {sorted(bindings)}"
            )
        return tools

    bindings = dict(bindings or {})
    slot_names = {
        name
        for name, entry in tools.items()
        if isinstance(entry, dict) and entry.get("slot") is True
    }

    undeclared = sorted(set(bindings) - slot_names)
    if undeclared:
        raise ToolSlotBindingError(
            f"--tool binding(s) for undeclared slot(s): {undeclared}; "
            f"declared slots: {sorted(slot_names)}"
        )
    unbound = sorted(slot_names - set(bindings))
    if unbound:
        raise ToolSlotBindingError(
            f"Missing --tool binding(s) for declared slot(s): {unbound}"
        )

    resolved: dict[str, Any] = {}
    for name, entry in tools.items():
        if name not in slot_names:
            resolved[name] = entry
            continue

        manifest_path = Path(bindings[name])
        if not manifest_path.is_absolute():
            manifest_path = (base_dir / manifest_path).resolve()
        if not manifest_path.is_file():
            raise ToolSlotBindingError(
                f"Slot '{name}': manifest not found: {manifest_path}"
            )
        try:
            raw = yaml.safe_load(manifest_path.read_text())
            manifest = ToolManifest.model_validate(raw)
        except (yaml.YAMLError, ValidationError, TypeError) as e:
            raise ToolSlotBindingError(
                f"Slot '{name}': invalid manifest '{manifest_path}': {e}"
            ) from e

        contract = entry.get("contract") or {}
        _check_contract(name, contract, manifest, manifest_path)

        # FR-768 translation, single path; key-match check skipped because
        # the binding is explicit (slot name ≠ manifest name is legitimate).
        resolved[name] = translate_manifest(manifest, manifest_path.parent)

    return resolved
