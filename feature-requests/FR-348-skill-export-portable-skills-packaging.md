# Feature Request: FR-348 Skill export — portable Skills standard packaging

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 2 days
**Requested:** 2026-05-07

## Summary

Add `yamlgraph skill export` to package an existing graph into a portable Skills directory (`SKILL.md`, runnable script, references, and schema assets) so Skills-aware agents can discover graph capabilities without MCP/A2A runtime setup.

## Value Statement

Graph authors can publish reusable, agent-discoverable skill bundles directly from YAMLGraph graphs, reducing integration friction across Copilot/Cursor/Claude-style Skills workflows.

## Problem

The topic in `gh-348` is valid and currently unserved in this branch:

1. There is no `skill` CLI command group in `yamlgraph/cli/__init__.py` (only `graph`, `schema`, `diary`, `a2a`).
2. Existing interoperability is runtime-only:
   - MCP exposes graphs as tools (`yamlgraph/mcp_server.py`)
   - A2A exposes graphs as agent skills (`yamlgraph/a2a_server.py`)
3. Discovery metadata already exists (`yamlgraph/discovery.py`: `name`, `description`, `input_vars`, `tool_name`, `input_schema`) but is not exported as portable filesystem artifacts.
4. A planning note exists at `/Users/sheikki/Documents/src/yamlgraph/docs/plan-skills-export.md`, but there is no implementation in this worktree.

Result: YAMLGraph graphs can be invoked live, but cannot be shipped as standalone Skills packages.

## Research: Existing Patterns and Prior Art

1. **Discovery already provides the core input contract.**
   - `yamlgraph/discovery.py` derives typed `input_schema` from graph `state` and `nodes[*].state_key`.
   - `tests/unit/test_discovery.py` and `tests/unit/test_mcp_typed_tools.py` validate this behavior.

2. **Graph → skill mapping is already established in A2A.**
   - `yamlgraph/a2a_server.py` and `reference/a2a-server.md` map graph metadata to `skills[]`.
   - This provides stable prior art for naming/description semantics.

3. **CLI command extension pattern is established.**
   - `yamlgraph/cli/__init__.py` registers command groups.
   - `yamlgraph/cli/schema_commands.py` shows `export`-style subcommand + dispatcher structure.
   - `tests/unit/test_json_schema_export.py` shows parser and command-handler test pattern.

4. **No current skill export surface exists.**
   - No `yamlgraph/cli/skill_commands.py`, no `yamlgraph/skill_export.py`, no `reference/skills-export.md`, and no `yamlgraph skill` parser wiring in this branch.

## Objectives

1. Add a single, deterministic export surface for portable Skills packaging.
2. Reuse existing graph metadata extraction instead of introducing new graph YAML schema.
3. Keep scope to packaging/export only (no runtime or registry concerns).

## Constraints

1. **Single responsibility:** export and packaging only.
2. **No new graph schema fields required:** derive from existing graph/prompt metadata.
3. **Deterministic output:** no LLM calls during export.
4. **Architecture-aligned layering:** CLI orchestration in `yamlgraph/cli/*`, export logic in reusable module.
5. **Safe filesystem behavior:** fail clearly on invalid paths or collisions; no silent overwrite by default.

## Proposed Solution

### In scope

1. Add CLI group and subcommand:
   - `yamlgraph skill export <graph_path_or_dir> --format {skill-md,copilot,cursor} [--output-dir PATH]`
2. Add export module (e.g. `yamlgraph/skill_export.py`) that:
   - resolves graph metadata and typed input schema via existing discovery/config loaders,
   - derives output schema from graph state keys produced by nodes (`state_key` targets),
   - writes package structure:
     - `SKILL.md`
     - `scripts/run.sh`
     - `references/*.md` (prompt YAML rendered to readable markdown)
     - `assets/schema.json` (input/output schema bundle)
3. Format variants:
   - `skill-md` → `<output-dir>/<skill-name>/...`
   - `copilot` → `<output-dir>/.copilot/skills/<skill-name>/...`
   - `cursor` → `<output-dir>/.cursor/skills/<skill-name>/...`
4. Add focused docs update in CLI/reference docs for usage and format differences.
5. Add unit/integration tests for parser wiring, filesystem layout, and artifact content contracts.

### Out of scope

1. Skills registry/marketplace publishing.
2. `yamlgraph skill install` or runtime loading of exported bundles.
3. LLM-generated trigger descriptions or autonomous enrichment.
4. MCP/A2A runtime behavior changes.

## Requirement IDs

Assign the following IDs before enforcement. Add these rows to `ARCHITECTURE.md` and create `capabilities/CAP-142-skill-export.yaml` referencing all seven.

| REQ ID | Maps to |
|--------|---------|
| REQ-YG-320 | AC-01: CLI parser registers `skill export` subcommand |
| REQ-YG-321 | AC-02: export produces SKILL.md, scripts/run.sh, references/, assets/schema.json |
| REQ-YG-322 | AC-03: SKILL.md content contract (metadata + run instructions) |
| REQ-YG-323 | AC-04: assets/schema.json input+output sections |
| REQ-YG-324 | AC-05: format-variant path layout (skill-md / copilot / cursor) |
| REQ-YG-325 | AC-06: deterministic, non-LLM, explicit errors on invalid input or collision |
| REQ-YG-326 | AC-07: CLI and reference docs include usage and layout examples |

## Acceptance Criteria

- [x] **AC-01 (REQ-YG-320):** `yamlgraph skill export` command is available from CLI parser and dispatch.
- [x] **AC-02 (REQ-YG-321):** Exporting a demo graph creates a complete package with `SKILL.md`, `scripts/run.sh`, `references/`, and `assets/schema.json`.
  - `scripts/run.sh` must call `yamlgraph graph run <graph_path>` and include one `--var <key>=<example>` flag per input variable; the script must be executable (`chmod +x`).
  - `references/` must contain one `.md` per prompt YAML referenced by graph nodes (filename: `<prompt-name>.md`), rendering at minimum the prompt `description` and `template` fields as markdown sections. If the graph has no prompt references, `references/` is created as an empty directory.
- [x] **AC-03 (REQ-YG-322):** `SKILL.md` contains: skill name (H1), description paragraph, `## Inputs` section listing each input var with type and description, `## Outputs` section listing each output state key with type, and `## Run` section with a copy-paste CLI invocation example.
- [x] **AC-04 (REQ-YG-323):** `assets/schema.json` is a JSON object with top-level keys `"input"` (JSON Schema object properties derived from `input_vars`) and `"output"` (JSON Schema object properties derived from `state_key` targets).
- [x] **AC-05 (REQ-YG-324):** `--format skill-md|copilot|cursor` writes to the correct target layout for each variant.
- [x] **AC-06 (REQ-YG-325):** Export is deterministic and non-LLM. All of the following return a non-zero exit code and an explicit error message (no silent partial writes):
  - graph path does not exist or is not a valid graph YAML;
  - `--format` value is not one of `skill-md`, `copilot`, `cursor`;
  - output target directory already exists and is non-empty (no `--force` flag; fail-fast is the only behavior).
- [x] **AC-07 (REQ-YG-326):** CLI and reference documentation include command usage and output layout examples.

## Failing Acceptance Tests (RED)

Planned RED artifact:

- `tests/unit/test_fr348_skill_export_red.py`

Each test must carry `@pytest.mark.req("REQ-YG-32X")` matching the table above.

Planned RED tests:

1. `test_ac01_cli_registers_skill_export_subcommand`
2. `test_ac02_export_generates_required_skill_package_files`
3. `test_ac03_skill_md_contains_graph_metadata_and_run_instructions`
4. `test_ac04_schema_json_contains_input_and_output_sections`
5. `test_ac05_format_variant_paths_skill_md_copilot_cursor`
6. `test_ac06_export_errors_on_invalid_graph_or_target_collision`
7. `test_ac07_cli_reference_docs_include_skill_export_usage`

RED command:

```bash
pytest tests/unit/test_fr348_skill_export_red.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
python -m yamlgraph.cli skill export examples/demos/hello/graph.yaml --format skill-md
test -f output/hello-world/SKILL.md
test -f output/hello-world/scripts/run.sh
test -f output/hello-world/assets/schema.json
```

## Alternatives Considered

1. **Rely on MCP/A2A only**
   - Rejected: requires runtime setup and does not produce portable, repo-committable skill bundles.
2. **Add new graph YAML fields for Skills metadata first**
   - Rejected: unnecessary for initial export because discovery and prompt metadata already cover minimum viable package generation.
3. **Support only one format (`skill-md`)**
   - Rejected: misses immediate interoperability targets from issue scope (`copilot`, `cursor`) with minimal additional path-mapping cost.

## Related

- Topic source: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-348.md`
- GitHub issue #348: <https://github.com/sheikkinen/yamlgraph/issues/348>
- Planning note: `/Users/sheikki/Documents/src/yamlgraph/docs/plan-skills-export.md`
- `yamlgraph/discovery.py`
- `yamlgraph/mcp_server.py`
- `yamlgraph/a2a_server.py`
- `yamlgraph/cli/__init__.py`
- `yamlgraph/cli/schema_commands.py`
- `tests/unit/test_discovery.py`
- `tests/unit/test_mcp_typed_tools.py`
- `tests/unit/test_json_schema_export.py`
