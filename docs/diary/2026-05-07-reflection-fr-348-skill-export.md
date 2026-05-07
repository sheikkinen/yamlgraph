# Reflection: FR-348 Skill Export — Portable Skills Packaging

**Date:** 2026-05-07
**FR:** FR-348 — Add `yamlgraph skill export` command
**Phase:** Post-implementation

## What Happened

Implemented a deterministic CLI command that packages an existing YAML graph into a
portable Skills directory (`SKILL.md`, `scripts/run.sh`, `references/`, `assets/schema.json`).
The implementation reused existing discovery metadata (`discovery.py`) and config loaders
rather than introducing new graph YAML fields.

Seven acceptance criteria were covered by seven corresponding RED tests, all passing GREEN
after implementation. Format variants (`skill-md`, `copilot`, `cursor`) were path-mapped
deterministically. All error paths (missing graph, invalid format, non-empty output dir)
return non-zero exit codes with explicit messages.

## Trap

### `working_system_inertia` — discovery boundary overextension

The initial design impulse was to embed schema derivation logic inside the CLI command
handler directly. This pattern recurs when a feature "just needs one function" — the
shortcut is plausible because the data is already close at hand.

The cure: normalise at the boundary. `skill_export.py` owns all derivation and packaging
logic; `skill_commands.py` stays thin (arg parsing + dispatch only). This preserves the
three-layer contract: CLI orchestration layer does not own export logic.

### `plausible_wrong_answer` — run.sh executability

A run script written with correct content but missing the executable bit passes a content
test while silently failing in practice. The test was extended to assert `os.access(run_sh,
os.X_OK)` — shape alone is insufficient.

## What Worked

- Reusing `load_graph_config()` + `discovery.py` meant zero new graph YAML schema fields.
- `skill_export_writer.py` separation kept `skill_export.py` under the 400-line target.
- Fail-fast-only for output dir collisions (no `--force` flag) matches the determinism
  constraint without scope creep.
- Prompt reference rendering via reading the prompt YAML template field directly avoids any
  LLM call and keeps the output deterministic.

## Root Cause (original problem)

MCP and A2A provide runtime discovery but produce no portable, repo-committable artifact.
A `skill export` command closes this gap with a single, deterministic packaging step.

## Seed

The three format variants (`skill-md`, `copilot`, `cursor`) share identical artifact content
and differ only in output path layout. Could a general `output-format` registry — mapping
format names to path-layout lambdas — allow third-party agents to register new layouts
without modifying core? This would turn format support from a hardcoded list into an
extension point, following the same plug-in pattern used in `llm_factory.py`.
