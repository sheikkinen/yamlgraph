# Feature Request: FR-350 Agent export — `.agent.md` generation with tool-scoped personas

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-07

## Summary

Add `--format agent-md` to `yamlgraph skill export` so a graph can be exported as a Copilot agent-mode file (`.agent.md`) with YAMLGraph MCP tool scoping (`tools: [yamlgraph/*]`).

## Value Statement

Graph authors get a deterministic path from YAMLGraph graph metadata to Copilot agent modes that enforce YAMLGraph-tool-only delegation instead of relying on heuristic skill activation.

## Problem

Issue #350 identifies a gap between portable skills and constrained agent execution:

1. FR-348 exports `SKILL.md` bundles, which describe capabilities but do not enforce tool-scoped behavior.
2. There is no `agent` export command or `agent-md` format variant in CLI parser wiring (`yamlgraph/cli/__init__.py`).
3. There is no `.agent.md` artifact writer in `yamlgraph/skill_export.py` / `yamlgraph/skill_export_writer.py`.
4. Repository scan shows no committed `.github/agents/` directory and no `*.agent.md` files.

Result: YAMLGraph can package skill descriptions, but cannot emit a first-class Copilot agent-mode artifact that constrains execution to YAMLGraph MCP tools.

## Research: Existing Patterns and Prior Art

1. **Portable export foundation already exists (FR-348).**
   - `yamlgraph skill export` is implemented with deterministic filesystem writes.
   - Existing format variants (`skill-md`, `copilot`, `cursor`) prove CLI + layout mapping pattern.
2. **Reusable metadata extraction already exists.**
   - `yamlgraph/skill_export.py` already derives graph name, description, input schema, output keys, and prompt references.
   - This avoids adding new graph YAML schema fields for MVP agent export.
3. **MCP integration already exists and is stable.**
   - `yamlgraph/mcp_server.py` exposes YAMLGraph tools under MCP server namespace `yamlgraph`.
   - `yamlgraph/discovery.py` already provides per-graph typed tool metadata.
4. **No current `.agent.md` export surface exists.**
   - No `agent-md` CLI format, no `.agent.md` writer, and no reference docs for agent export in current branch.

## Objectives

1. Add one deterministic export surface for Copilot agent-mode files.
2. Reuse FR-348 export architecture instead of introducing a parallel exporter stack.
3. Keep scope to artifact generation only (no runtime MCP/A2A behavior changes).

## Constraints

1. **Single responsibility:** export `.agent.md` artifacts only.
2. **No runtime protocol changes:** no edits to MCP invocation flow or A2A behavior.
3. **Deterministic and non-LLM:** export must perform no model calls.
4. **Architecture aligned:** CLI orchestration in `yamlgraph/cli/*`, generation logic in export module/writer.
5. **Explicit failure behavior:** invalid graph, unsupported format, and output collisions fail with clear errors.

## Proposed Solution

### In scope

1. Extend CLI format choices:
   - `yamlgraph skill export <graph_path_or_dir> --format agent-md [--output-dir PATH]`
2. Add `agent-md` target mapping:
   - `<output-dir>/.github/agents/<agent-name>.agent.md`
3. Generate `.agent.md` content from graph metadata with frontmatter contract:
   - `description`: graph description
   - `tools`: `[yamlgraph/*]`
   - `model`: `Claude Sonnet 4`
4. Include markdown body sections:
   - purpose/role sentence from graph metadata,
   - required input variables,
   - invocation guidance for the exported agent mode.
5. Update docs for new format and output layout in `reference/cli.md`, `reference/skills-export.md`, and `reference/README.md`.

### Out of scope

1. New top-level `yamlgraph agent ...` command group.
2. Agent marketplace publishing/registration flows.
3. Automatic installation of agent files into user-level global directories.
4. MCP/A2A server behavior changes.

## Requirement IDs

Reserve capability and requirement IDs for enforcement:

- Capability: `CAP-143`
- Requirements: `REQ-YG-327` through `REQ-YG-332`

| REQ ID | Maps to |
|--------|---------|
| REQ-YG-327 | AC-01: CLI parser accepts `--format agent-md` for `skill export` |
| REQ-YG-328 | AC-02: `agent-md` output path layout is `.github/agents/<name>.agent.md` |
| REQ-YG-329 | AC-03: `.agent.md` frontmatter includes `description`, `tools: [yamlgraph/*]`, and `model` |
| REQ-YG-330 | AC-04: `.agent.md` body includes role/purpose, inputs, and invocation guidance |
| REQ-YG-331 | AC-05: deterministic explicit errors for invalid graph, unsupported format, and path collisions |
| REQ-YG-332 | AC-06: CLI/reference docs include `agent-md` usage and layout examples |

## Acceptance Criteria

- [x] **AC-01 (REQ-YG-327):** `yamlgraph skill export` parser accepts `--format agent-md` and dispatches without new top-level command group.
- [x] **AC-02 (REQ-YG-328):** Export with `--format agent-md` writes a single file at `<output-dir>/.github/agents/<skill-name>.agent.md`.
- [x] **AC-03 (REQ-YG-329):** Generated file starts with valid YAML frontmatter containing:
  - `description` (non-empty string),
  - `tools: [yamlgraph/*]`,
  - `model` (default value `Claude Sonnet 4`).
- [x] **AC-04 (REQ-YG-330):** Generated markdown body includes:
  - agent heading/name,
  - inputs section derived from graph input schema,
  - concise invocation instructions for `@<agent-name>` usage.
- [x] **AC-05 (REQ-YG-331):** Export remains deterministic and non-LLM; the following fail with non-zero exit + explicit message:
  - graph path missing/invalid,
  - format unsupported,
  - target `.agent.md` path already exists (collision, no silent overwrite).
- [x] **AC-06 (REQ-YG-332):** Documentation updated with `agent-md` command usage and layout examples.

## Failing Acceptance Tests (RED)

Planned RED artifact:

- `tests/unit/test_fr350_agent_export_red.py`

Each test must include `@pytest.mark.req("REQ-YG-32X")` markers matching this FR.

Planned RED tests:

1. `test_ac01_cli_registers_agent_md_format_for_skill_export`
2. `test_ac02_agent_md_format_writes_expected_github_agents_path`
3. `test_ac03_agent_md_frontmatter_contains_description_tools_and_model`
4. `test_ac04_agent_md_body_contains_inputs_and_invocation_guidance`
5. `test_ac05_agent_md_export_errors_on_invalid_graph_format_or_collision`
6. `test_ac06_docs_include_agent_md_usage_examples`

RED command:

```bash
pytest tests/unit/test_fr350_agent_export_red.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
python -m yamlgraph.cli skill export examples/demos/hello/graph.yaml --format agent-md --output-dir /tmp/yg-agent-export
test -f /tmp/yg-agent-export/.github/agents/hello-world.agent.md
```

## Judge Issues (must resolve before APPROVE)

### Issue 1 — File-vs-directory output mismatch (blocks implementation)

The entire FR-348 export architecture is **directory-oriented**:

- `_resolve_target_dir` → returns a `Path` directory
- `_assert_target_is_safe` → checks `is_dir()` and `any(iterdir())`
- `write_skill_package` → writes multiple files atomically into that directory
- `SkillPackage.target_dir: Path` → named and typed as directory

The `agent-md` output is a **single file** (`<output-dir>/.github/agents/<name>.agent.md`), not a directory. This creates three concrete gaps that must be addressed:

1. **`_resolve_target_dir` semantics**: Should it return the parent directory `.github/agents/` (consistent naming: `target_dir`) and the writer derives the filename, OR should it return the full file path?  The FR must pick one and be consistent with the `SkillPackage` return value.

2. **`_assert_target_is_safe` semantics**: The existing check is `if any(target_dir.iterdir())` (directory not empty). For a single-file output, collision detection must be `if target_file.exists()`. The collision check in AC-05 must specify whether it checks the **file** path, not the parent directory.

3. **`SkillPackage.target_dir` return value**: The CLI prints `✓ Skill exported: {package.target_dir}`. For agent-md the useful value is the file path (`<name>.agent.md`), not the parent dir. Either rename the field to `target_path` for agent-md outputs, or add a `target_file: Path | None` optional field.

**Required clarification**: Explicitly specify whether `agent-md` format uses a new code path (separate writer function `write_agent_md_file` in `skill_export_writer.py`) or whether the existing `write_skill_package` is extended to support single-file modes. The former is strongly preferred given the semantic divergence.

### Issue 2 — RED test file must exist in the worktree before authority is granted

The FR lists 6 planned tests and marks them "Planned RED artifact" but no test file exists at `tests/unit/test_fr350_agent_export_red.py`. Per Commandment 7 and the Sermon, the failing test must be committed RED before implementation authority is granted. The judge cannot verify that tests "compile and fail for the right reasons" without the file.

**Required action**: Commit `tests/unit/test_fr350_agent_export_red.py` with all 6 tests (using the exact names and `@pytest.mark.req` markers listed in the FR) so they fail with `ImportError` or `AssertionError` on missing implementation — not on missing fixtures or syntax errors.

### Issue 3 — AC-05 collision semantics are ambiguous

AC-05 says: _"target `.agent.md` path already exists (collision, no silent overwrite)"_. But the current `_assert_target_is_safe` operates on a directory, not a file. The acceptance criterion must specify:

- The **collision check is on the output file** (not a directory), i.e. `if Path(output_dir / ".github/agents" / f"{skill_name}.agent.md").exists(): raise FileExistsError(...)`
- The error message must include the file path, not a directory path.

### Issue 4 — `model` field hardcoded without override path

AC-03 says model defaults to `"Claude Sonnet 4"`. The FR scope is MVP/default-only, which is acceptable. However, the frontmatter YAML key must be specified exactly (`model` vs `models`; singular is correct for `.agent.md` spec). Confirm the key name matches the GitHub Copilot agent file schema before implementation.

---

## Alternatives Considered

1. **New command group `yamlgraph agent export`**
   - Rejected for MVP: duplicates FR-348 export path and increases CLI surface without functional gain.
2. **Manual `.agent.md` authoring only**
   - Rejected: non-deterministic, error-prone, and not scalable across many graphs.
3. **Keep skills-only export**
   - Rejected: does not satisfy issue #350 need for explicit tool-constrained persona mode.

## Related

- GitHub issue #350: <https://github.com/sheikkinen/yamlgraph/issues/350>
- FR-348: `feature-requests/FR-348-skill-export-portable-skills-packaging.md`
- `yamlgraph/cli/__init__.py`
- `yamlgraph/cli/skill_commands.py`
- `yamlgraph/skill_export.py`
- `yamlgraph/skill_export_writer.py`
- `yamlgraph/mcp_server.py`
- `yamlgraph/discovery.py`
