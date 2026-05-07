# Feature Request: FR-351 Agent export `.agent.md` for tool-scoped Copilot modes

**Priority:** HIGH
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-07

## Summary

Extend `yamlgraph skill export` with `--format agent-md` to generate Copilot agent-mode files (`.agent.md`) that lock tool usage to YAMLGraph MCP tools and encode a graph-scoped persona.

## Value Statement

YAMLGraph authors can ship constrained, invocation-ready Copilot agent modes from existing graphs, improving delegation reliability over descriptive Skills-only bundles.

## Problem

Issue #351 identifies a gap between exported Skills metadata and constrained execution:

1. FR-348 already exports portable skill bundles (`SKILL.md`, scripts, schema), but this is descriptive packaging, not tool-constrained agent mode.
2. Existing MCP integration already exposes callable YAMLGraph tools (`yamlgraph/discovery.py`, `yamlgraph/mcp_server.py`), but no export path emits `.agent.md` wrappers that force those tools.
3. There is no `agent` CLI group, no `agent-md` format in `yamlgraph/skill_export.py`, and no `.agent.md` docs in current reference pages.

Result: users can export Skills docs, but cannot generate a dedicated Copilot agent mode that is pre-scoped to YAMLGraph tools.

## Research: Existing Patterns and Prior Art

1. **Export extension point already exists.**
   - `yamlgraph/skill_export.py` uses `SkillFormat` and format-specific path resolution.
   - `yamlgraph/cli/__init__.py` wires `yamlgraph skill export --format ...`.
   - This is the minimal insertion point for adding `agent-md`.

2. **Tool-scoped invocation contract already exists at MCP layer.**
   - `yamlgraph/mcp_server.py` serves generic and per-graph typed tools.
   - `yamlgraph/discovery.py` already normalizes graph names and derives typed inputs (`tool_name`, `input_schema`).
   - `.agent.md` can reuse this layer without adding runtime execution logic.

3. **No existing `.agent.md` export in this worktree.**
   - Code search shows no `yamlgraph agent export`, no `.agent.md` writer module, and no agent-mode docs under `reference/`.

4. **Topic-source discrepancy in this worktree.**
   - Requested source `.chaplain/processing/gh-351.md` is absent.
   - Planning source used: GitHub issue #351 (`feat: yamlgraph agent export — .agent.md generation with tool-scoped personas`).

## Objectives

1. Add a deterministic export path for Copilot `.agent.md` artifacts from existing graph metadata.
2. Ensure generated agent mode enforces YAMLGraph MCP tool scope (`tools: [yamlgraph/*]`).
3. Keep scope to export packaging only (no runtime Copilot/MCP/A2A behavior changes).

## Constraints

1. **Single responsibility:** add export format only.
2. **Deterministic output:** no LLM calls in export path.
3. **No new runtime dependencies:** reuse existing CLI/export architecture.
4. **Fail-fast filesystem behavior:** explicit collision/invalid-path errors; no silent overwrite.
5. **No schema expansion required:** derive from existing graph fields (`name`, `description`, `state`, `nodes`).

## Proposed Solution

### In Scope

1. Extend `yamlgraph skill export` with `--format agent-md`.
2. Add writer path for agent mode artifact:
   - `<output-dir>/.github/agents/<skill-name>.agent.md`
3. Generate `.agent.md` content contract:
   - YAML frontmatter with:
     - `description`: graph description (or fallback text)
     - `tools: [yamlgraph/*]`
   - Body with graph-scoped persona/instructions that direct execution through YAMLGraph MCP tools only.
4. Add docs updates:
   - `reference/cli.md` (new format in command/options/examples)
   - `reference/skills-export.md` (agent-md layout and sample output)
   - `reference/README.md` link updates if needed
5. Add RED acceptance tests for parser wiring, output path, content contract, collision behavior, and docs.

### Out of Scope

1. New top-level `yamlgraph agent ...` command group.
2. Auto-installation into user-level agent directories.
3. A2A export or registry publishing.
4. End-to-end telephony runtime verification (Twilio/ElevenLabs calls).

## Requirement IDs

Assign these IDs before enforcement. Add corresponding rows to `ARCHITECTURE.md` and register a new capability file.

| REQ ID | Maps to |
|--------|---------|
| REQ-YG-327 | AC-01: CLI parser accepts `--format agent-md` for `yamlgraph skill export` |
| REQ-YG-328 | AC-02: agent-md export writes `.github/agents/<skill-name>.agent.md` |
| REQ-YG-329 | AC-03: `.agent.md` frontmatter includes `description` and `tools: [yamlgraph/*]` |
| REQ-YG-330 | AC-04: body contains graph-scoped persona and MCP-only execution guidance |
| REQ-YG-331 | AC-05: explicit failure on output collision and missing/invalid graph path |
| REQ-YG-332 | AC-06: CLI/reference docs include `agent-md` usage and output layout |

## Acceptance Criteria

- [x] **AC-01 (REQ-YG-327):** `yamlgraph skill export ... --format agent-md` parses and dispatches from CLI.
- [x] **AC-02 (REQ-YG-328):** Export writes exactly one agent artifact at `<output-dir>/.github/agents/<skill-name>.agent.md`.
- [x] **AC-03 (REQ-YG-329):** Generated `.agent.md` frontmatter includes `description` and `tools: [yamlgraph/*]`.
- [x] **AC-04 (REQ-YG-330):** Generated body includes graph-scoped persona text and explicit instruction to operate through YAMLGraph tools.
- [x] **AC-05 (REQ-YG-331):** Missing graph path, invalid graph YAML, and target collision return non-zero CLI exit + explicit error text.
- [x] **AC-06 (REQ-YG-332):** `reference/cli.md` and `reference/skills-export.md` document `agent-md` with path example.

## Failing Acceptance Tests (RED)

RED artifact added in this planning branch:

- `tests/unit/test_fr351_agent_export_red.py`

Planned RED tests:

1. `test_ac01_cli_registers_agent_md_format`
2. `test_ac02_export_agent_md_writes_file_in_github_agents`
3. `test_ac03_agent_md_contains_required_frontmatter_and_tool_scope`
4. `test_ac04_export_agent_md_errors_on_target_collision`
5. `test_ac05_docs_include_agent_md_format_and_layout`

RED command (expected to fail before implementation):

```bash
pytest tests/unit/test_fr351_agent_export_red.py -q --no-cov
```

## Alternatives Considered

1. **New `yamlgraph agent export` command**
   - Rejected for this FR: adds parallel command surface when existing `skill export` format extension is sufficient.
2. **Generate both `SKILL.md` bundle and `.agent.md` in one export**
   - Rejected: mixes artifact responsibilities and complicates deterministic contracts.
3. **Rely on manual handwritten `.agent.md` files**
   - Rejected: duplicates metadata and drifts from graph source of truth.

## Related

- Issue: <https://github.com/sheikkinen/yamlgraph/issues/351>
- `yamlgraph/cli/__init__.py`
- `yamlgraph/cli/skill_commands.py`
- `yamlgraph/skill_export.py`
- `yamlgraph/skill_export_writer.py`
- `yamlgraph/discovery.py`
- `yamlgraph/mcp_server.py`
- `feature-requests/FR-348-skill-export-portable-skills-packaging.md`
