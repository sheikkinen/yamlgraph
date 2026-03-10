#!/usr/bin/env python3
"""Migrate CAPABILITIES dict to individual YAML files under capabilities/.

Usage:
    python scripts/migrate_capabilities.py

Creates capabilities/ directory with one YAML file per active capability.
Reads requirement descriptions from ARCHITECTURE.md and capability groupings
from the CAPABILITIES dict in req_coverage.py.

FR-178: Append-Only Capability Registry
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE_MD = REPO_ROOT / "ARCHITECTURE.md"
OUTPUT_DIR = REPO_ROOT / "capabilities"

# Retired capabilities — skip these
RETIRED_CAPS = {"CAP-27", "CAP-29", "CAP-52", "CAP-58"}

# FR mapping: extracted from ARCHITECTURE.md section headers + task spec
FR_MAP: dict[str, str] = {
    "CAP-28": "FR-071",
    "CAP-30": "FR-082",
    "CAP-31": "FR-090",
    "CAP-32": "FR-100",
    "CAP-33": "FR-106",
    "CAP-34": "FR-111",
    "CAP-35": "FR-116",
    "CAP-36": "FR-118",
    "CAP-37": "FR-121",
    "CAP-38": "FR-125",
    "CAP-39": "FR-131",
    "CAP-40": "FR-128",
    "CAP-41": "FR-140",
    "CAP-42": "FR-142",
    "CAP-43": "FR-138",
    "CAP-44": "FR-136",
    "CAP-45": "FR-144",
    "CAP-46": "FR-124",
    "CAP-47": "FR-145",
    "CAP-48": "FR-153",
    "CAP-49": "FR-135",
    "CAP-50": "FR-149",
    "CAP-51": "FR-150",
    "CAP-53": "FR-157",
    "CAP-54": "FR-158",
    "CAP-55": "FR-163",
    "CAP-56": "FR-164",
    "CAP-57": "FR-166",
    "CAP-59": "FR-172",
    "CAP-60": "FR-174",
    "CAP-61": "FR-173",
    "CAP-62": "FR-175",
    "CAP-63": "FR-169",
    "CAP-64": "FR-176",
}

# Section descriptions per capability (from ARCHITECTURE.md prose)
SECTION_DESC: dict[str, str] = {
    "CAP-01": (
        "Load YAML graph configs, validate schemas, build state models,"
        " and ensure graph integrity through linting."
    ),
    "CAP-02": (
        "Transform validated configs into executable StateGraphs with node"
        " compilation, edge wiring, and loop detection."
    ),
    "CAP-03": (
        "Create executable node functions for LLM, streaming, tool,"
        " interrupt, and subgraph behavior."
    ),
    "CAP-04": (
        "Load prompt YAML, validate variables, format messages, and run"
        " LLM calls sync and async."
    ),
    "CAP-05": (
        "Integrate shell and Python tools into graphs, enable agent loops"
        " for tool-calling."
    ),
    "CAP-06": (
        "Route across nodes using explicit routes, expression evaluation,"
        " and control nodes."
    ),
    "CAP-07": (
        "Checkpointers and Redis storage for resuming pipelines and"
        " state history."
    ),
    "CAP-08": (
        "Error strategies (retry, fallback, skip), sanitization,"
        " resilience features."
    ),
    "CAP-09": (
        "Command-line commands for graph validation, execution, info"
        " display, schema export."
    ),
    "CAP-10": (
        "Export results/states in JSON/Markdown, handle serialization"
        " for persistence."
    ),
    "CAP-11": "Parallel fan-out and nested subgraph execution.",
    "CAP-12": (
        "Logging, templating, JSON extraction, environment handling,"
        " and shared utilities."
    ),
    "CAP-13": (
        "Observability via LangSmith: trace URL retrieval, public"
        " sharing, and tracer injection."
    ),
    "CAP-14": (
        "Stream LLM tokens through the compiled graph pipeline using"
        " LangGraph astream(stream_mode=\"messages\"), enabling real-time"
        " SSE output."
    ),
    "CAP-15": (
        "Value expressions, condition expressions, literal parsing,"
        " and resolve_node_variables batch resolution."
    ),
    "CAP-16": (
        "Linter cross-reference and semantic checks for edge endpoints,"
        " loop limits, state references, and contract warnings."
    ),
    "CAP-17": (
        "Defense-in-depth guards against infinite loops, unbounded map"
        " fan-out, and runaway execution."
    ),
    "CAP-18": "Requirement traceability enforcement and testing infrastructure.",
    "CAP-19": (
        "Expose YAMLGraph graphs as MCP (Model Context Protocol) tools"
        " for Copilot and other AI assistants."
    ),
    "CAP-20": (
        "Shared utilities extracted from pipeline patterns. Eliminates"
        " copy-paste duplication across projects."
    ),
    "CAP-21": (
        "Scheduled pipeline tools for fetching external developments and"
        " appending context-aware diary entries."
    ),
    "CAP-22": (
        "Custom lint checks enforcing architectural patterns beyond"
        " standard linters."
    ),
    "CAP-23": (
        "skip_if_exists checks truthiness, not existence. Empty"
        " collections, empty strings, None, 0, and False do NOT"
        " trigger skip."
    ),
    "CAP-24": (
        "Declarative multi-turn stateful tool integration via"
        " config-level expansion."
    ),
    "CAP-25": (
        "Domain-scoped RAG using Tavily search API with type:python"
        " tool nodes and map fan-out."
    ),
    "CAP-26": (
        "Error propagation, timeout support, and interrupt detection"
        " for run_graph_streaming_native(). Yields StreamEvent Pydantic"
        " objects for errors and interrupts instead of crashing silently."
    ),
    "CAP-28": (
        "Graph-level and per-node thinking_budget YAML field for"
        " Anthropic extended thinking."
    ),
    "CAP-30": (
        "New copilot node type that delegates graph processing to"
        " Copilot CLI, replacing shell-script orchestration with a"
        " first-class YAML-declarable node."
    ),
    "CAP-31": (
        "Extends the Plan-Judge workflow with automatic diary entry"
        " creation after each run."
    ),
    "CAP-32": (
        "A YAMLGraph pipeline that writes the development pipeline"
        " documentation as an eBook."
    ),
    "CAP-33": (
        "Parallel development pipeline via git worktrees, enabling"
        " multiple features to be enforced simultaneously without"
        " blocking the main working tree."
    ),
    "CAP-34": (
        "Process-global compiled graph cache so load_and_compile_async()"
        " results survive module reloads and are shared across all"
        " callers within the same Python process."
    ),
    "CAP-35": (
        "Post-graph hook in watch.sh that detects new feature request"
        " files via ephemeral find + comm diff, skips rejected FRs, and"
        " spawns enforce_worktree.sh in the background."
    ),
    "CAP-36": (
        "--propose flag on inquisitor.sh detects violations persisting"
        " across consecutive Inquisitor Audit entries and writes targeted"
        " fix proposals to .chaplain/inbox/."
    ),
    "CAP-37": (
        "Cross-check test ensuring the provider count in ARCHITECTURE.md"
        " module table matches the actual ProviderType Literal in"
        " llm_factory.py."
    ),
    "CAP-38": (
        "Automates three post-merge obligations after a PR from the"
        " enforce pipeline is merged: CHANGELOG entry, FR status update,"
        " and diary reflection stub."
    ),
    "CAP-39": (
        "inquisitor.sh commit-delta gate extracts last audit SHA from"
        " docs/diary/, counts feat:/fix: commits since that SHA, and"
        " aborts when none found."
    ),
    "CAP-40": (
        "enforce_worktree.sh delegates all LLM orchestration to"
        " examples/enforce/graph.yaml instead of inline copilot -p"
        " calls, completing the three-layer separation."
    ),
    "CAP-41": (
        "Session-scoped autouse pytest fixture strips GIT_* environment"
        " variables injected by pre-commit, preventing subprocess bleed"
        " into tests that create temporary git repos."
    ),
    "CAP-42": (
        "inquisitor.sh worktree gate detects git worktree context and"
        " exits early, suppressing audit and propose phases during"
        " enforce pipeline."
    ),
    "CAP-43": (
        "Shell script that prunes stale Copilot CLI sessions from"
        " ~/.copilot/session-state/ based on age."
    ),
    "CAP-44": (
        "Add a fourth judge verdict (SPLIT) for multi-concern feature"
        " requests, enabling decomposition before implementation."
    ),
    "CAP-45": (
        "Pre-commit hook diary-reflection-check rejects commits when"
        " tracked docs/diary/ reflection files contain unfilled"
        " placeholder text."
    ),
    "CAP-46": (
        "CLI command to import pending diary entries and git report data"
        " into docs/diary/ with optional dry-run and source selection."
    ),
    "CAP-47": "Detect and reject test markers that reference non-existent requirement IDs.",
    "CAP-48": (
        "CHANGELOG.md [Unreleased] documents significant file removals"
        " per Commandment 8."
    ),
    "CAP-49": (
        "Every on-disk example and demo is accurately indexed in"
        " examples/README.md with categorized sections and enforced"
        " quality bar."
    ),
    "CAP-50": (
        "GitHub Actions job in commitlint.yml that blocks merge of feat"
        " and fix PRs unless CHANGELOG.md is modified in the PR diff."
    ),
    "CAP-51": (
        "GitHub branch protection rules on main enforcing squash-merge"
        " only, required status checks, and no direct pushes."
    ),
    "CAP-53": (
        "CI job that fails when unresolved merge conflict markers are"
        " found in tracked files, complementing the local"
        " check-merge-conflict pre-commit hook."
    ),
    "CAP-54": (
        "CI gate ensuring feat/fix PRs with FR references include a"
        " diary reflection file in the diff."
    ),
    "CAP-55": (
        "Document the .chaplain/inbox/ workflow in CLAUDE.md so Claude"
        " Code sessions can discover and use the autonomous proposal"
        " pipeline."
    ),
    "CAP-56": (
        "Per-node runtime verification with deterministic pattern"
        " matching. Checks stated predictions against actual node output."
    ),
    "CAP-57": (
        "Count range verification claim parsed into CountRangeClaim"
        " Pydantic model with min/max validation."
    ),
    "CAP-59": (
        "loop_exits graph-level config maps node names to custom exit"
        " targets when loop limit is reached."
    ),
    "CAP-60": (
        "Worktree venv corruption guard: validate_venv_health() raises"
        " on missing or broken venv, clean_stale_pth_entries() prevents"
        " import corruption from dangling editable installs."
    ),
    "CAP-61": (
        "4-phase pipeline (condemn-fix-verify-submit_pr) for bugfix with"
        " condemning test first. Commandment 7 compliance."
    ),
    "CAP-62": (
        "watch.sh runs enforce and bugfix pipelines in the foreground,"
        " eliminating merge conflicts on shared files."
    ),
    "CAP-63": (
        "Critique-refine reflexion loop between test_and_demo and"
        " precommit_check in examples/enforce/graph.yaml."
    ),
    "CAP-64": (
        "docs/concurrency-safety.md documents every concurrency pattern"
        " in YAMLGraph with verdict, model, shared state, and evidence."
    ),
}


def _parse_architecture_reqs() -> dict[str, dict[str, str | list[str]]]:
    """Parse requirement descriptions and modules from ARCHITECTURE.md.

    Returns mapping: req_id -> {"description": str, "modules": list[str]}
    """
    text = ARCHITECTURE_MD.read_text()

    cap_start = text.find("## Capabilities & Requirements Traceability")
    if cap_start == -1:
        print("ERROR: Cannot find capabilities section in ARCHITECTURE.md")
        sys.exit(1)

    next_section = text.find("\n## ", cap_start + 10)
    cap_text = text[cap_start:next_section] if next_section != -1 else text[cap_start:]

    req_info: dict[str, dict[str, str | list[str]]] = {}
    req_pattern = re.compile(
        r"\|\s*(REQ-YG-\d{3})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|"
    )
    for match in req_pattern.finditer(cap_text):
        req_id = match.group(1)
        description = match.group(2).strip().replace("**", "")
        modules_raw = match.group(3).strip()
        modules = re.findall(r"`([^`]+)`", modules_raw)
        req_info[req_id] = {"description": description, "modules": modules}

    return req_info


def _get_capabilities() -> dict[str, tuple[str, list[str]]]:
    """Import CAPABILITIES from req_coverage.py and apply fixes."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from req_coverage import CAPABILITIES  # noqa: E402

    caps: dict[str, tuple[str, list[str]]] = {}
    for cap_id, (name, reqs) in CAPABILITIES.items():
        if cap_id in RETIRED_CAPS:
            print(f"  Skipping retired: {cap_id}")
            continue

        reqs = list(reqs)

        # Fix: add orphan REQ-YG-113 to CAP-17
        if cap_id == "CAP-17" and "REQ-YG-113" not in reqs:
            reqs.append("REQ-YG-113")
            print(f"  Added orphan REQ-YG-113 to {cap_id}")

        # Fix: remove duplicate REQ-YG-075 from CAP-11 (keep in CAP-24)
        if cap_id == "CAP-11" and "REQ-YG-075" in reqs:
            reqs.remove("REQ-YG-075")
            print(f"  Removed duplicate REQ-YG-075 from {cap_id}")

        caps[cap_id] = (name, reqs)

    return caps


def _to_kebab(name: str) -> str:
    """Convert name to kebab-case for filenames."""
    result = re.sub(r"[^a-zA-Z0-9]+", "-", name)
    result = re.sub(r"-+", "-", result)
    return result.strip("-").lower()


def _yaml_escape(value: str) -> str:
    """Escape a YAML scalar value if it contains special characters."""
    if any(c in value for c in ":{}[]&*?|>!%@`#,\"'"):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _generate_yaml(
    cap_id: str,
    name: str,
    reqs: list[str],
    req_info: dict[str, dict],
) -> str:
    """Generate YAML content for a single capability."""
    cap_num = int(cap_id.split("-")[1])

    # Determine FR
    if cap_num <= 26:
        fr = "legacy"
    else:
        fr = FR_MAP.get(cap_id, "legacy")

    # Capability description
    description = SECTION_DESC.get(cap_id, f"{name} capability")

    # Collect all modules
    all_modules: list[str] = []
    for req_id in reqs:
        info = req_info.get(req_id, {})
        for m in info.get("modules", []):
            if m not in all_modules:
                all_modules.append(m)

    lines: list[str] = []
    lines.append(f"id: {cap_id}")
    lines.append(f"name: {_yaml_escape(name)}")

    # Description as folded scalar
    desc_text = description.replace("\n", " ").strip()
    if len(desc_text) > 70:
        lines.append("description: >")
        words = desc_text.split()
        current = ""
        for w in words:
            if current and len(current) + 1 + len(w) > 78:
                lines.append(f"  {current}")
                current = w
            else:
                current = f"{current} {w}" if current else w
        if current:
            lines.append(f"  {current}")
    else:
        lines.append(f"description: {_yaml_escape(desc_text)}")

    # Modules
    if all_modules:
        lines.append("modules:")
        for m in sorted(set(all_modules)):
            lines.append(f"  - {m}")
    else:
        lines.append("modules: []")

    # Requirements
    lines.append("requirements:")
    for req_id in reqs:
        info = req_info.get(req_id, {})
        desc = str(info.get("description", f"{name} requirement"))
        desc = desc.replace("\n", " ").strip()
        modules = info.get("modules", [])
        lines.append(f"  - id: {req_id}")

        # Description — use folded scalar for long text
        if len(desc) > 70:
            lines.append("    description: >")
            words = desc.split()
            current = ""
            for w in words:
                if current and len(current) + 1 + len(w) > 74:
                    lines.append(f"      {current}")
                    current = w
                else:
                    current = f"{current} {w}" if current else w
            if current:
                lines.append(f"      {current}")
        else:
            lines.append(f"    description: {_yaml_escape(desc)}")

        if modules:
            lines.append("    modules:")
            for m in modules:
                lines.append(f"      - {m}")
        else:
            lines.append("    modules: []")

    lines.append(f"fr: {fr}")
    lines.append("")  # trailing newline

    return "\n".join(lines)


def main() -> None:
    req_info = _parse_architecture_reqs()
    print(f"Parsed {len(req_info)} requirements from ARCHITECTURE.md")

    caps = _get_capabilities()
    print(f"Processing {len(caps)} active capabilities")

    OUTPUT_DIR.mkdir(exist_ok=True)

    count = 0
    for cap_id in sorted(caps, key=lambda x: int(x.split("-")[1])):
        name, reqs = caps[cap_id]
        cap_num = int(cap_id.split("-")[1])
        kebab = _to_kebab(name)
        filename = f"CAP-{cap_num:02d}-{kebab}.yaml"
        filepath = OUTPUT_DIR / filename

        content = _generate_yaml(cap_id, name, reqs, req_info)
        filepath.write_text(content)
        count += 1
        print(f"  Created: {filename}")

    print(f"\nDone! {count} files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
