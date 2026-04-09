#!/usr/bin/env python3
"""Verify all pyproject.toml dependencies have documented rationale.

Usage:
    python scripts/dependency_rationale.py           # summary
    python scripts/dependency_rationale.py --detail  # show all entries
    python scripts/dependency_rationale.py --strict  # exit 1 on gaps

FR-219: Dependency Rationale Audit — follows noqa_coverage.py pattern.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# Required fields for each rationale entry
REQUIRED_FIELDS = ("rationale",)


def parse_pyproject_dependencies(toml_path: Path) -> dict[str, list[str]]:
    """Parse pyproject.toml to extract dependency package names.

    Returns dict mapping group name → list of package names.
    Core dependencies use the key "core".
    Version specifiers and extras are stripped.

    Raises:
        FileNotFoundError: If toml_path does not exist.
    """
    if not toml_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found: {toml_path}")

    content = toml_path.read_text()
    result: dict[str, list[str]] = {}

    # Extract core dependencies
    core_deps = _extract_toml_list(content, "dependencies")
    result["core"] = [_strip_version(dep) for dep in core_deps]

    # Extract optional dependency groups
    optional_section = _extract_optional_deps(content)
    for group_name, deps in optional_section.items():
        result[group_name] = [_strip_version(dep) for dep in deps]

    return result


def _strip_version(dep: str) -> str:
    """Strip version specifiers and extras from a dependency string.

    Examples:
        "pydantic>=2.0.0" → "pydantic"
        "a2a-sdk[http-server]>=0.3,<1.0" → "a2a-sdk"
        "langchain-anthropic>=0.3.0" → "langchain-anthropic"
    """
    # Remove extras [...]
    name = re.split(r"[\[>=<~!;]", dep)[0].strip()
    return name


def _extract_toml_list(content: str, key: str) -> list[str]:
    """Extract a TOML list value for a given key using regex.

    Simple parser for pyproject.toml — avoids tomllib dependency for Python 3.11+
    compatibility across environments where tomllib may not be available as a
    standalone import.
    """
    # Find key = [ then track bracket depth to find matching ]
    pattern = rf"(?:^|\n)\s*{re.escape(key)}\s*=\s*\["
    match = re.search(pattern, content)
    if not match:
        return []

    start = match.end()
    depth = 1
    i = start
    while i < len(content) and depth > 0:
        if content[i] == "[":
            depth += 1
        elif content[i] == "]":
            depth -= 1
        i += 1

    items_str = content[start : i - 1]
    return re.findall(r'"([^"]+)"', items_str)


def _extract_optional_deps(content: str) -> dict[str, list[str]]:
    """Extract [project.optional-dependencies] groups from TOML content."""
    result: dict[str, list[str]] = {}

    # Find the optional-dependencies section
    section_match = re.search(
        r"\[project\.optional-dependencies\]\s*\n(.*?)(?=\n\[|\Z)",
        content,
        re.DOTALL,
    )
    if not section_match:
        return result

    section = section_match.group(1)

    # Find each group: name = [...] using bracket-depth tracking
    group_start_pattern = r"(\w[\w-]*)\s*=\s*\["
    for match in re.finditer(group_start_pattern, section):
        group_name = match.group(1)
        start = match.end()
        depth = 1
        i = start
        while i < len(section) and depth > 0:
            if section[i] == "[":
                depth += 1
            elif section[i] == "]":
                depth -= 1
            i += 1
        items_str = section[start : i - 1]
        deps = re.findall(r'"([^"]+)"', items_str)
        result[group_name] = deps

    return result


def parse_rationale_registry(registry_path: Path) -> dict[str, dict]:
    """Parse dependency-rationale.yaml to extract documented entries.

    Returns dict mapping package_name → {rationale, modules, added, ...}.
    Missing file returns empty dict.
    """
    if not registry_path.exists():
        return {}

    content = registry_path.read_text()
    data = yaml.safe_load(content)

    if not data or "dependencies" not in data:
        return {}

    deps = data["dependencies"]
    if not isinstance(deps, dict):
        return {}

    return deps


def find_undocumented(
    deps: dict[str, list[str]],
    registry: dict[str, dict],
) -> dict[str, list[str]]:
    """Find dependencies not documented in the rationale registry.

    Returns dict mapping group → list of undocumented package names.
    Empty groups are omitted.
    """
    documented_names = set(registry.keys())
    undocumented: dict[str, list[str]] = {}

    for group, packages in deps.items():
        missing = [pkg for pkg in packages if pkg not in documented_names]
        if missing:
            undocumented[group] = missing

    return undocumented


def main() -> int:
    """Main entry point."""
    root = Path(__file__).parent.parent
    toml_path = root / "pyproject.toml"
    registry_path = root / "docs" / "dependency-rationale.yaml"

    detail = "--detail" in sys.argv
    strict = "--strict" in sys.argv

    # Parse sources
    deps = parse_pyproject_dependencies(toml_path)
    registry = parse_rationale_registry(registry_path)

    # Find gaps
    undocumented = find_undocumented(deps, registry)

    # Count totals
    total_deps = sum(len(pkgs) for pkgs in deps.values())
    total_documented = len(registry)
    total_undocumented = sum(len(pkgs) for pkgs in undocumented.values())

    # Print summary
    print("=" * 60)
    print("Dependency Rationale Audit")
    print("=" * 60)
    print()
    print(f"Total dependencies:        {total_deps}")
    print(f"Documented rationales:     {total_documented}")
    print(f"Undocumented:              {total_undocumented}")
    print()

    if detail:
        print("-" * 60)
        print("Documented Dependencies:")
        print("-" * 60)
        for pkg_name in sorted(registry.keys()):
            entry = registry[pkg_name]
            rationale = entry.get("rationale", "(no rationale)")
            modules = entry.get("modules", [])
            modules_str = ", ".join(modules) if modules else "(none)"
            print(f"  {pkg_name}")
            print(f"    Rationale: {rationale}")
            print(f"    Modules:   {modules_str}")
        print()

    if undocumented:
        print("-" * 60)
        print("❌ Undocumented dependencies (add to docs/dependency-rationale.yaml):")
        print("-" * 60)
        for group in sorted(undocumented.keys()):
            print(f"  [{group}]")
            for pkg in sorted(undocumented[group]):
                print(f"    - {pkg}")
        print()
        print("Each dependency requires an entry with:")
        print("  - rationale: Why is this dependency needed?")
        print("  - modules: Which modules consume it?")
        print("  - added: Version when it was added")
        print()

    # Check for incomplete entries (missing required fields)
    incomplete = []
    for pkg_name, entry in registry.items():
        if not isinstance(entry, dict):
            incomplete.append((pkg_name, "entry is not a mapping"))
            continue
        for field in REQUIRED_FIELDS:
            if not entry.get(field):
                incomplete.append((pkg_name, f"missing '{field}'"))

    if incomplete:
        print("-" * 60)
        print("⚠ Incomplete rationale entries:")
        print("-" * 60)
        for pkg_name, reason in incomplete:
            print(f"  {pkg_name}: {reason}")
        print()

    if strict and undocumented:
        print("FAIL -- undocumented dependencies detected")
        return 1

    if not undocumented:
        print("✓ All dependencies have documented rationale")

    return 0


if __name__ == "__main__":
    sys.exit(main())
