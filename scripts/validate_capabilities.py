#!/usr/bin/env python3
"""Validate capability registry YAML files.

Usage:
    python scripts/validate_capabilities.py [--strict]

Validates all capabilities/CAP-*.yaml files against the schema:
- Required fields: id, name, description, modules, requirements, fr
- ID matches filename pattern (CAP-01-foo.yaml → id must be CAP-01)
- Requirement IDs follow REQ-YG-{NNN} format
- No duplicate capability or requirement IDs across files
- No file reuses a retired ID (CAP-27, CAP-29, CAP-58)

FR-178: Append-Only Capability Registry
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CAPABILITIES_DIR = REPO_ROOT / "capabilities"

# Retired capability IDs — gaps in numbering, must not be reused
RETIRED_CAPS = {
    "CAP-27": "Telco Voice Call Demo — relocated to projects/outcaller/",
    "CAP-29": "Incaller Voice Demo — relocated to projects/incaller/",
    "CAP-52": "Architecture Capability Count Guard — removed by FR-177",
    "CAP-58": "Removed (see git history for details)",
    "CAP-63": "Enforce Pipeline Reflexion Loop — superseded by FR-183 simplified pipeline",
}

REQUIRED_FIELDS = {"id", "name", "description", "modules", "requirements", "fr"}
CAP_ID_PATTERN = re.compile(r"^CAP-(\d+)$")
REQ_ID_PATTERN = re.compile(r"^REQ-YG-(\d+)$")
FILENAME_PATTERN = re.compile(r"^CAP-(\d+)-[\w-]+\.yaml$")


def validate_file(filepath: Path) -> list[str]:
    """Validate a single capability YAML file. Returns list of errors."""
    errors: list[str] = []
    filename = filepath.name

    # Check filename pattern
    match = FILENAME_PATTERN.match(filename)
    if not match:
        errors.append(
            f"{filename}: Invalid filename pattern. Expected CAP-XX-kebab-name.yaml"
        )
        return errors

    expected_cap_num = match.group(1)
    expected_cap_id = f"CAP-{expected_cap_num}"

    # Check retired ID reuse
    if expected_cap_id in RETIRED_CAPS:
        errors.append(
            f"{filename}: Uses retired capability ID {expected_cap_id}. "
            f"Reason: {RETIRED_CAPS[expected_cap_id]}"
        )
        return errors

    # Load YAML
    try:
        with open(filepath, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"{filename}: YAML parse error: {e}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"{filename}: Root must be a mapping, got {type(data).__name__}")
        return errors

    # Retired CAPs only need id, name, status
    if data.get("status") == "retired":
        cap_id = data.get("id", "")
        if not CAP_ID_PATTERN.match(str(cap_id)):
            errors.append(f"{filename}: Invalid id format '{cap_id}'. Expected CAP-XX")
        elif cap_id != expected_cap_id:
            errors.append(
                f"{filename}: ID mismatch. File expects {expected_cap_id} but id is {cap_id}"
            )
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{filename}: name must be a non-empty string")
        return errors

    # Check required fields
    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        errors.append(f"{filename}: Missing required fields: {sorted(missing)}")

    # Validate id field
    cap_id = data.get("id", "")
    if not CAP_ID_PATTERN.match(str(cap_id)):
        errors.append(f"{filename}: Invalid id format '{cap_id}'. Expected CAP-XX")
    elif cap_id != expected_cap_id:
        errors.append(
            f"{filename}: ID mismatch. File expects {expected_cap_id} but id is {cap_id}"
        )

    # Validate name
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"{filename}: name must be a non-empty string")

    # Validate description
    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append(f"{filename}: description must be a non-empty string")

    # Validate modules
    modules = data.get("modules")
    if not isinstance(modules, list) or not modules:
        errors.append(f"{filename}: modules must be a non-empty list")
    elif not all(isinstance(m, str) for m in modules):
        errors.append(f"{filename}: modules must be a list of strings")

    # Validate requirements
    requirements = data.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        errors.append(f"{filename}: requirements must be a non-empty list")
    else:
        for i, req in enumerate(requirements):
            if not isinstance(req, dict):
                errors.append(f"{filename}: requirements[{i}] must be a mapping")
                continue

            req_id = req.get("id", "")
            if not REQ_ID_PATTERN.match(str(req_id)):
                errors.append(
                    f"{filename}: requirements[{i}].id '{req_id}' "
                    f"invalid. Expected REQ-YG-XXX"
                )

            req_desc = req.get("description")
            if not isinstance(req_desc, str) or not req_desc.strip():
                errors.append(
                    f"{filename}: requirements[{i}].description must be non-empty string"
                )

            req_modules = req.get("modules")
            if not isinstance(req_modules, list) or not req_modules:
                errors.append(
                    f"{filename}: requirements[{i}].modules must be a non-empty list"
                )

    # Validate fr field
    fr = data.get("fr")
    if not isinstance(fr, str) or not fr.strip():
        errors.append(f"{filename}: fr must be a non-empty string")

    return errors


def validate_registry(strict: bool = False) -> tuple[list[str], dict[str, list[str]]]:
    """Validate all capability files and check for duplicates.

    Returns:
        (errors, capabilities_map) where capabilities_map is {CAP-ID: [req_ids]}
    """
    all_errors: list[str] = []
    cap_ids: dict[str, Path] = {}  # CAP-ID → first file seen
    req_ids: dict[str, str] = {}  # REQ-ID → CAP-ID that owns it
    capabilities_map: dict[str, list[str]] = {}

    if not CAPABILITIES_DIR.exists():
        all_errors.append(f"Capabilities directory not found: {CAPABILITIES_DIR}")
        return all_errors, capabilities_map

    yaml_files = sorted(CAPABILITIES_DIR.glob("CAP-*.yaml"))
    if not yaml_files:
        all_errors.append(f"No capability files found in {CAPABILITIES_DIR}")
        return all_errors, capabilities_map

    for filepath in yaml_files:
        # Per-file validation
        file_errors = validate_file(filepath)
        all_errors.extend(file_errors)

        # Skip duplicate checks if file has parse errors
        if file_errors:
            continue

        # Load for duplicate checking
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        cap_id = data["id"]
        requirements = data.get("requirements", [])

        # Check duplicate capability ID
        if cap_id in cap_ids:
            all_errors.append(
                f"{filepath.name}: Duplicate capability ID {cap_id}. "
                f"First seen in {cap_ids[cap_id].name}"
            )
        else:
            cap_ids[cap_id] = filepath
            capabilities_map[cap_id] = []

        # Check duplicate requirement IDs
        for req in requirements:
            req_id = req.get("id", "")
            if req_id in req_ids:
                all_errors.append(
                    f"{filepath.name}: Duplicate requirement ID {req_id}. "
                    f"First seen in {req_ids[req_id]}"
                )
            else:
                req_ids[req_id] = cap_id
                if cap_id in capabilities_map:
                    capabilities_map[cap_id].append(req_id)

    return all_errors, capabilities_map


def main() -> int:
    """Main entry point."""
    strict = "--strict" in sys.argv

    print("=" * 70)
    print("CAPABILITY REGISTRY VALIDATION")
    print("=" * 70)
    print()

    errors, capabilities_map = validate_registry(strict=strict)

    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"  ❌ {error}")
        print()
        print(f"Found {len(errors)} error(s)")
        return 1

    # Summary
    total_caps = len(capabilities_map)
    total_reqs = sum(len(reqs) for reqs in capabilities_map.values())

    print(f"✅ All {total_caps} capability files valid")
    print(f"   {total_reqs} unique requirements across registry")
    print()

    if strict:
        print("Strict mode: All validations passed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
