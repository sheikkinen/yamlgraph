#!/usr/bin/env python3
"""Collect @pytest.mark.req markers and report requirement coverage.

Usage:
    python scripts/req_coverage.py                 # summary
    python scripts/req_coverage.py --detail        # per-req test list
    python scripts/req_coverage.py --implementation  # req → code → test links
    python scripts/req_coverage.py --strict        # exit 1 on gaps

FR-178: Loads capabilities from YAML registry under capabilities/

--implementation requires a healthy .coverage DB with test contexts.
Recording command (FR-850 — sequential, ctrace core; -n auto and the
sysmon core silently poison contexts):
    COVERAGE_CORE=ctrace pytest tests/unit tests/integration -q \\
        --cov=yamlgraph --cov-context=test

Scope contract (FR-436):
- Includes framework test scope only: tests/unit and tests/integration
- Excludes infrastructure hook scope: .github/hooks/tests
"""

from __future__ import annotations

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coverage_contexts import (  # noqa: E402  # CONF-412
    RESOLUTION_CLASSES,
    CoverageContextError,
    derive_resolution,
    load_coverage_contexts,
    reconcile_modules,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CAPABILITIES_DIR = REPO_ROOT / "capabilities"
FRAMEWORK_TEST_DIRS = ("tests/unit", "tests/integration")
EXCLUDED_TEST_DIRS = (".github/hooks/tests",)


def load_capabilities_from_registry() -> (
    tuple[list[str], dict[str, tuple[str, list[str]]]]
):
    """Load capabilities from YAML registry files.

    Returns:
        (all_reqs, capabilities) where:
        - all_reqs: sorted list of all REQ-YG-XXX IDs
        - capabilities: dict mapping CAP-ID → (name, [req_ids])
    """
    capabilities: dict[str, tuple[str, list[str]]] = {}
    all_req_ids: set[str] = set()

    if not CAPABILITIES_DIR.exists():
        raise FileNotFoundError(f"Capabilities directory not found: {CAPABILITIES_DIR}")

    yaml_files = sorted(CAPABILITIES_DIR.glob("CAP-*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"No capability files found in {CAPABILITIES_DIR}")

    for filepath in yaml_files:
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data.get("status") == "retired":
            continue

        cap_id = data["id"]
        cap_name = data["name"]
        req_ids = [req["id"] for req in data.get("requirements", [])]

        capabilities[cap_id] = (cap_name, req_ids)
        all_req_ids.update(req_ids)

    # Sort requirements by numeric part
    def req_sort_key(req_id: str) -> int:
        match = re.search(r"(\d+)$", req_id)
        return int(match.group(1)) if match else 0

    all_reqs = sorted(all_req_ids, key=req_sort_key)

    return all_reqs, capabilities


# Load from YAML registry (FR-178: Append-Only Capability Registry)
ALL_REQS, CAPABILITIES = load_capabilities_from_registry()


def extract_req_markers(filepath: Path) -> dict[str, list[str]]:
    """Extract @pytest.mark.req(...) markers from a test file.

    Returns mapping of requirement ID -> list of test names.
    Uses class-qualified keys (Class::method) to avoid collisions
    when multiple classes share method names.
    """
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    except SyntaxError:
        return {}

    req_map: dict[str, list[str]] = defaultdict(list)
    stem = filepath.stem

    def _process_func(
        node: ast.FunctionDef | ast.AsyncFunctionDef, class_name: str | None
    ) -> None:
        if not node.name.startswith("test"):
            return
        key = (
            f"{stem}::{class_name}::{node.name}"
            if class_name
            else f"{stem}::{node.name}"
        )
        for decorator in node.decorator_list:
            reqs = _extract_req_from_decorator(decorator)
            for req in reqs:
                req_map[req].append(key)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            # Extract class-level @pytest.mark.req decorators
            class_reqs: list[str] = []
            for decorator in node.decorator_list:
                class_reqs.extend(_extract_req_from_decorator(decorator))

            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    _process_func(item, node.name)
                    # Also apply class-level reqs to test methods
                    if item.name.startswith("test") and class_reqs:
                        key = f"{stem}::{node.name}::{item.name}"
                        for req in class_reqs:
                            if key not in req_map[req]:
                                req_map[req].append(key)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            _process_func(node, None)

    return dict(req_map)


def _extract_req_from_decorator(node: ast.expr) -> list[str]:
    """Extract REQ-YG-XXX strings from a decorator node."""
    # @pytest.mark.req("REQ-YG-014")
    # @pytest.mark.req("REQ-YG-014", "REQ-YG-031")
    if isinstance(node, ast.Call):
        func = node.func
        if _is_req_marker(func):
            return [
                arg.value
                for arg in node.args
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
            ]
    return []


def _is_req_marker(node: ast.expr) -> bool:
    """Check if node represents pytest.mark.req."""
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "req"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
    )


# Question-first section headings for --implementation (FR-850 AC-09)
QUESTION_LINKAGE = (
    "Q1: How is each requirement's witness linked to implementation code?"
)
QUESTION_TRUST = "Q2: Can these linkage numbers be trusted?"
QUESTION_MODULES = (
    "Q3: Which declared modules are never exercised by their capability's tagged tests?"
)


def format_resolution_summary(counts: dict[str, int], total: int) -> str:
    """One-line five-class witness split with an honest denominator (AC-06).

    Raises ValueError when the class counts do not sum to *total* —
    a dishonest denominator is a defect, not a formatting choice.
    """
    if sum(counts.values()) != total:
        raise ValueError(
            f"resolution counts sum to {sum(counts.values())}, "
            f"but total test-req pairs is {total}"
        )
    parts = [f"{cls}: {counts.get(cls, 0)}" for cls in RESOLUTION_CLASSES]
    return f"Witness split ({total} test-req pairs): " + " | ".join(parts)


def _load_cap_modules() -> dict[str, list[str]]:
    """CAP-ID → declared modules (cap-level ∪ req-level) from capabilities/."""
    modules: dict[str, list[str]] = {}
    for filepath in sorted(CAPABILITIES_DIR.glob("CAP-*.yaml")):
        data = yaml.safe_load(filepath.read_text(encoding="utf-8"))
        if data.get("status") == "retired":
            continue
        declared = list(data.get("modules") or [])
        for req in data.get("requirements", []):
            for mod in req.get("modules") or []:
                if mod not in declared:
                    declared.append(mod)
        modules[data["id"]] = declared
    return modules


def _load_req_descriptions(root: Path) -> dict[str, str]:
    """Parse requirement descriptions from ARCHITECTURE.md.

    Matches lines like ``| REQ-YG-001 | Load graph configurations... | modules |``
    and returns ``{"REQ-YG-001": "Load graph configurations..."}``.
    """
    arch_path = root / "ARCHITECTURE.md"
    if not arch_path.exists():
        return {}
    descriptions: dict[str, str] = {}
    pattern = re.compile(r"^\|\s*(REQ-YG-\d{3})\s*\|\s*(.+?)\s*\|")
    for line in arch_path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            req_id, desc = m.group(1), m.group(2).strip()
            # First match wins (avoid duplicate REQ-YG-047 rows)
            if req_id not in descriptions:
                descriptions[req_id] = desc
    return descriptions


def main() -> None:
    # FR-951: this gate prints status glyphs; declare the stream's codec so it
    # survives a pipe on a host whose preferred encoding is not UTF-8.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")

    root = Path(__file__).parent.parent
    # ADR-001 Tier 1 scope: framework tests only.
    test_dirs = [root / rel_path for rel_path in FRAMEWORK_TEST_DIRS]

    # Collect all markers
    all_markers: dict[str, list[str]] = defaultdict(list)
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        for filepath in sorted(test_dir.rglob("test_*.py")):
            markers = extract_req_markers(filepath)
            for req, tests in markers.items():
                all_markers[req].extend(tests)

    # Report
    total_pairs = sum(len(tests) for tests in all_markers.values())
    unique_tests = {t for tests in all_markers.values() for t in tests}
    covered = [r for r in ALL_REQS if r in all_markers]
    uncovered = [r for r in ALL_REQS if r not in all_markers]

    print("=" * 70)
    print("REQUIREMENT TRACEABILITY REPORT")
    print("=" * 70)
    print(
        f"\nScope: framework tests only ({', '.join(FRAMEWORK_TEST_DIRS)}); "
        f"excludes infrastructure tests ({', '.join(EXCLUDED_TEST_DIRS)})"
    )
    print(f"\nRequirements: {len(covered)}/{len(ALL_REQS)} covered")
    print(f"Tagged tests: {len(unique_tests)} unique, {total_pairs} test-req pairs")
    print()

    # Per-capability summary
    print("CAPABILITY COVERAGE")
    print("-" * 70)
    for cap_id, (cap_name, reqs) in CAPABILITIES.items():
        cap_covered = sum(1 for r in reqs if r in all_markers)
        cap_tests = sum(len(all_markers.get(r, [])) for r in reqs)
        status = "✅" if cap_covered == len(reqs) else "⚠️ " if cap_covered > 0 else "❌"
        print(
            f"  {status} {cap_id} {cap_name}: {cap_covered}/{len(reqs)} reqs, {cap_tests} tests"
        )

    # Uncovered requirements
    if uncovered:
        print(f"\nUNCOVERED REQUIREMENTS ({len(uncovered)})")
        print("-" * 70)
        for req in uncovered:
            print(f"  ❌ {req}")

    # Detail: per-requirement test list
    if "--detail" in sys.argv:
        print("\nDETAILED MAPPING")
        print("-" * 70)
        for req in ALL_REQS:
            tests = all_markers.get(req, [])
            if tests:
                print(f"\n  {req} ({len(tests)} tests):")
                for t in tests:
                    print(f"    - {t}")
            else:
                print(f"\n  {req}: NO TESTS")

    # Implementation: req → source files (from coverage + AST import resolution) → tests
    if "--implementation" in sys.argv:
        req_descriptions = _load_req_descriptions(root)

        # Build test_key → filepath index for AST import resolution
        test_key_to_file: dict[str, Path] = {}
        for test_dir in test_dirs:
            if not test_dir.exists():
                continue
            for filepath in sorted(test_dir.rglob("test_*.py")):
                markers = extract_req_markers(filepath)
                for tests in markers.values():
                    for test_key in tests:
                        test_key_to_file[test_key] = filepath

        # Hard refusal on a missing/context-free/poisoned instrument (AC-03)
        try:
            coverage_map, recorded = load_coverage_contexts(root, unique_tests)
        except CoverageContextError as exc:
            print(f"\n✗ {exc}")
            sys.exit(1)

        print("\nIMPLEMENTATION TRACEABILITY")
        print("=" * 70)

        counts: dict[str, int] = dict.fromkeys(RESOLUTION_CLASSES, 0)
        total_linked_pairs = 0
        cap_resolved: dict[str, set[str]] = {}

        print(f"\n{QUESTION_LINKAGE}")
        for cap_id, (cap_name, cap_reqs) in CAPABILITIES.items():
            cap_tests_total = sum(len(all_markers.get(r, [])) for r in cap_reqs)
            resolved_for_cap: set[str] = set()
            print(
                f"\n── {cap_id} {cap_name} ({len(cap_reqs)} reqs, "
                f"{cap_tests_total} tests) {'─' * 20}"
            )

            for req in cap_reqs:
                desc = req_descriptions.get(req, "")
                tests = all_markers.get(req, [])
                if not tests:
                    print(f"\n    {req}  {desc}")
                    print("      NO TESTS")
                    continue

                source_files: set[str] = set()
                by_class: dict[str, list[str]] = {c: [] for c in RESOLUTION_CLASSES}
                for test in tests:
                    cls, files = derive_resolution(
                        test, coverage_map, recorded, test_key_to_file.get(test)
                    )
                    by_class[cls].append(test)
                    counts[cls] += 1
                    total_linked_pairs += 1
                    source_files.update(files)
                resolved_for_cap |= source_files

                print(f"\n    {req}  {desc}")
                print(f"      ({len(source_files)} files, {len(tests)} tests)")
                if source_files:
                    print("      Implementation:")
                    for sf in sorted(source_files):
                        print(f"        {sf}")
                for cls in RESOLUTION_CLASSES:
                    if by_class[cls]:
                        print(f"      Tests ({cls}):")
                        for t in by_class[cls]:
                            print(f"        {t}")
            cap_resolved[cap_id] = resolved_for_cap

        print(f"\n{QUESTION_TRUST}")
        print(
            f"  Instrument: {len(recorded)} recorded test contexts for "
            f"{len(unique_tests)} tagged tests (.coverage accepted)"
        )
        print("  " + format_resolution_summary(counts, total_linked_pairs))

        print(f"\n{QUESTION_MODULES}")
        cap_modules = _load_cap_modules()
        any_never_hit = False
        unmeasured_total = 0
        for cap_id, (cap_name, _cap_reqs) in CAPABILITIES.items():
            never_hit, unmeasured = reconcile_modules(
                cap_modules.get(cap_id, []), cap_resolved.get(cap_id, set())
            )
            unmeasured_total += len(unmeasured)
            if never_hit:
                any_never_hit = True
                print(f"  ⚠ {cap_id} {cap_name} — declared but never hit:")
                for mod in never_hit:
                    print(f"      {mod}")
        if not any_never_hit:
            print(
                "  ✓ every measured declared module is exercised by its "
                "capability's tagged tests"
            )
        print(
            f"  ({unmeasured_total} declarations outside yamlgraph/ are "
            f"unmeasured by this coverage run — not flagged)"
        )

    # Reverse check: phantom requirement detection (FR-145)
    all_reqs_set = set(ALL_REQS)
    phantom_ids = sorted(set(all_markers.keys()) - all_reqs_set)

    if phantom_ids:
        print("\n⚠ Phantom requirement IDs (in tests but not in ALL_REQS):")
        for pid in phantom_ids:
            tests = all_markers[pid]
            print(f"  {pid} referenced by {len(tests)} test(s):")
            for t in tests:
                print(f"    - {t}")

    # Architecture cross-check: every req in ALL_REQS must have a row in ARCHITECTURE.md
    arch_descriptions = _load_req_descriptions(root)
    arch_req_ids = set(arch_descriptions.keys())
    all_req_ids = set(ALL_REQS)
    undocumented = sorted(all_req_ids - arch_req_ids)

    if undocumented:
        print(f"\n⚠ {len(undocumented)} requirement(s) missing from ARCHITECTURE.md:")
        for req_id in undocumented:
            print(f"    {req_id}")

    # Exit code: fail if any requirement uncovered, undocumented, or phantom (strict mode)
    if (uncovered or undocumented or phantom_ids) and "--strict" in sys.argv:
        sys.exit(1)


if __name__ == "__main__":
    main()
