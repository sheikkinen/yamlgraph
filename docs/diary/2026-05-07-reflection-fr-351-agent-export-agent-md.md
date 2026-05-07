# Reflection: FR-351 Agent Export — `.agent.md` Generation

**Date:** 2026-05-07
**FR:** FR-351 — Add `yamlgraph skill export --format agent-md`
**Phase:** Post-implementation

## What Happened

Extended `SkillFormat` with an `agent-md` variant that emits a Copilot agent-mode
file at `.github/agents/<skill-name>.agent.md`. The format reuses the existing
`SkillExporter` dispatch path — no new CLI surface was needed. `write_agent_markdown()`
in `skill_export_writer.py` writes YAML frontmatter (`description`, `tools:
[yamlgraph/*]`) followed by a graph-scoped persona body.

Five acceptance criteria — CLI parser wiring, output path contract, frontmatter
content, body persona text, and collision/error behavior — were covered by five RED
tests, all passing GREEN after implementation.

## Trap

### `false_duplicate` — path vs directory target mismatch

The existing `_resolve_target_dir` + `_assert_target_is_safe` pair assumed the target
was always a directory. `agent-md` produces a single file, not a directory tree. Using
the same helpers naively would produce an incorrect collision check (file vs dir test)
and fail silently on a pre-existing agent file.

The cure: `_assert_target_is_safe` was extended with a `format_name` parameter that
branches on `AGENT_MD` to check file existence directly, while the directory-centric
path remained intact for all other formats. The fix lives at the entry boundary
(safety assertion), not scattered across the writer.

### `plausible_wrong_answer` — frontmatter multiline description

A graph description containing embedded newlines would produce invalid YAML frontmatter
(multi-line scalar without block indicator). The writer normalises the description to a
single line with `.replace("\n", " ").strip()` before emission, preventing a shape-
valid but semantically broken artifact.

## What Worked

- Reusing `SkillExporter._resolve_target_dir` with a single `if` branch kept the
  insertion point minimal and the format registry pattern uniform.
- Separating `write_agent_markdown()` into `skill_export_writer.py` preserved the
  single-responsibility boundary: exporter owns dispatch, writer owns content.
- Deriving skill name and description entirely from existing `GraphConfig` fields meant
  zero new YAML schema fields and zero LLM calls in the export path.

## Root Cause (original problem)

FR-348 produced descriptive Skills bundles but not constrained Copilot agent modes. A
graph author had no single command to generate a pre-scoped `.agent.md` file that
forces all execution through YAMLGraph MCP tools.

## Seed

The `tools: [yamlgraph/*]` scope is hardcoded. Could future graph YAML gain an optional
`agent.tools` list that overrides the default scope — allowing a graph author to
explicitly permit or restrict additional tool namespaces without forking the template?
This would make the export format a thin projection of graph-declared intent rather than
an opinionated default.
