# Reflection: FR-350 Agent Export — `.agent.md` Tool-Scoped Personas

**Date:** 2026-05-07
**FR:** FR-350 — Add `agent-md` export format to `yamlgraph skill export`
**Phase:** Post-implementation

## What Happened

Extended the FR-348 skill export architecture with a new `agent-md` format that writes a
single `.github/agents/<skill-name>.agent.md` artifact. The output contains YAML frontmatter
(`description`, `tools: [yamlgraph/*]`, `model: Claude Sonnet 4`) and a markdown body with
the agent heading, required inputs, and invocation guidance.

Implementation deliberately reused the existing `skill_export.py` orchestration layer and
`skill_export_writer.py` for the new `write_agent_md_file` function, keeping CLI dispatch in
`skill_commands.py` thin. All six acceptance criteria (REQ-YG-327 through REQ-YG-332) are
covered by tests in `test_fr350_agent_export_red.py`.

## Trap

### `working_system_inertia` — single-file vs. directory output

The FR-348 architecture is directory-oriented: `_resolve_target_dir`, `_assert_target_is_safe`,
and `SkillPackage.target_dir` all assume a directory as the target. The `agent-md` output is a
single file nested inside `.github/agents/`. The Judge surfaced this in Issue 1: the collision
check, path resolution, and return value semantics all diverge for single-file outputs.

Resolution: `SkillPackage` was extended with an optional `target_file: Path | None` field.
The `agent-md` path sets both `target_dir` (the parent `.github/agents/` directory) and
`target_file` (the full `.agent.md` path). Collision detection checks `target_file.exists()`
rather than `any(target_dir.iterdir())`. This keeps the return type stable for callers while
making file-vs-directory semantics explicit.

### `downstream_fix` — collision check location

The initial impulse was to add a file-exists guard inside `write_agent_md_file`. That would
have been a downstream fix: the symptom manifests in the writer, but the boundary is the
`export_skill` orchestration layer. The guard was placed in `export_skill` before dispatch,
consistent with where directory-empty checks live for other formats.

## What Worked

- Reusing `load_graph_config()` kept the export deterministic and non-LLM without parsing
  the graph YAML a second time.
- The `state` field in graph YAML provided all needed input schema data (name, type,
  description) without requiring new graph YAML fields.
- Extending `SkillPackage` with `target_file` was the minimal change that resolved the
  Judge's Issue 1 without renaming existing fields or breaking callers.
- The frontmatter `tools: [yamlgraph/*]` list renders correctly in both YAML-parsed and
  raw-string comparisons due to the list-literal YAML encoding.

## Root Cause (original problem)

FR-348 `SKILL.md` exports describe capability but do not constrain agent execution to
YAMLGraph tools. A graph author who publishes a skill bundle had no path to a Copilot
agent-mode file with explicit tool scoping. FR-350 closes this gap with a single
deterministic export step.

## Seed

The `model` field is hardcoded to `"Claude Sonnet 4"` for MVP. A follow-on FR could expose
`--model` as a CLI override that passes through to frontmatter, following the same pattern as
`--output-dir`. If multiple Copilot-compatible model identifiers are in use across a
workspace, a `model` key in graph YAML metadata (already present for LLM nodes) could serve
as the default source, making the export value derived rather than hardcoded.
