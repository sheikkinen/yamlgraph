# Feature Request: Consolidate Chaplain and Copilot Demo Graph

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-25
**Implemented:** 2026-02-25

## Summary

Eliminate duplication between `.chaplain/graph.yaml` and `examples/copilot/graph.yaml` by establishing `examples/copilot/graph.yaml` as the single source of truth and making `.chaplain/watch.sh` reference it.

## Value Statement

Maintainers get a single canonical graph to evolve, eliminating drift between the production chaplain workflow and the copilot demo.

## Problem

The Plan → Judge workflow exists in two locations that have diverged:

| Aspect | `.chaplain/graph.yaml` | `examples/copilot/graph.yaml` |
|--------|----------------------|-------------------------------|
| **Stages** | Plan → Judge → Summarize → Write Diary | Plan → Judge → Summarize |
| **Summarize prompt** | DiaryEntry schema (theme, body, seed) | Generic executive summary |
| **Timeout** | 500s | 300s |
| **State variables** | `{state.plan_result}` (Jinja2) | `{state.plan_result.output}` (simple) |
| **Extra state** | date, diary_prefix, diary_entry, written | — |
| **Tools** | write_diary_tool | — |
| **Exports** | — | summary → markdown |

The `.chaplain/` version was forked from `examples/copilot/` (FR-084), then extended with diary append (FR-093). Now improvements to either file don't propagate to the other.

## Proposed Solution

Merge all production features from `.chaplain/graph.yaml` into `examples/copilot/graph.yaml` and make `.chaplain/` consume it by reference.

### Step 1: Merge graph features into `examples/copilot/graph.yaml`

Add the diary append stage (write_diary tool, DiaryEntry schema, date/diary_prefix state fields) from `.chaplain/graph.yaml` into `examples/copilot/graph.yaml`. Keep timeout at 500s (production value). The merged graph has 4 stages: Plan → Judge → Summarize → Write Diary.

The tool declaration uses the cross-example import path `examples.diary_digest.nodes.writing` with a `# TODO: FR-097` comment, accepting this as tech debt until FR-097 (refactor diary writing to `examples/shared/diary.py`) is implemented. Once FR-097 lands, the module path updates to `examples.shared.diary` — a single-line change.

### Step 2: Merge prompts

The `plan.yaml` and `judge.yaml` prompts are identical except for FR-084 comment headers — keep the chaplain comments (which include provenance) in the canonical copy under `examples/copilot/prompts/`.

Replace `examples/copilot/prompts/summarize.yaml` with the `.chaplain/` version (DiaryEntry schema). The merged summarize prompt uses Jinja2 syntax (`{{ plan_output | default("No plan available") }}`) and the graph variables map to `{state.plan_result}` (full CopilotResult object, not `.output`). This is correct because: (a) Jinja2 will stringify the CopilotResult via its `__str__` method, providing the full context including exit code and backend, and (b) `default()` filters provide graceful degradation if a preceding node fails.

### Step 3: Update `.chaplain/watch.sh`

```bash
# Before
yamlgraph graph run .chaplain/graph.yaml \

# After
yamlgraph graph run examples/copilot/graph.yaml \
```

### Step 4: Remove `.chaplain/graph.yaml` and `.chaplain/prompts/`

Delete the duplicated files. The `.chaplain/` directory retains only operational files: `watch.sh`, `inquisitor.sh`, `inbox/`, `drafts/`.

### Step 5: Update exports

Remove the `exports` section from the merged graph. The original export (`summary` → markdown file) referenced a state key that no longer exists after the summarize node's `state_key` changes from `summary` to `diary_entry` (DiaryEntry schema). Since `write_diary` handles the actual output by appending to `docs/diary.md`, the export is redundant — diary entries are persisted by the tool, not by file export.

### Step 6: Update references

- `examples/copilot/README.md` — update to document the full 4-stage workflow (Plan → Judge → Summarize → Write Diary), remove "See Also" link to `.chaplain/graph.yaml`, document CopilotResult variable handling
- `ARCHITECTURE.md` — update REQ-YG-090 file paths from `.chaplain/graph.yaml` and `.chaplain/prompts/summarize.yaml` to `examples/copilot/graph.yaml` and `examples/copilot/prompts/summarize.yaml` (requirement traceability per ADR-001)
- Any FR docs referencing `.chaplain/graph.yaml` — add note about consolidation
- `docs/diary.md` line 23 — historical Seed question references `.chaplain/graph.yaml`; acceptable as historical diary entry, no update needed

### Step 7: Resolve `defaults` section

The copilot graph has `defaults: temperature: 0.7` which the chaplain graph does not. Remove it — copilot nodes ignore temperature, and the summarize node uses a provider-specific model override in its prompt metadata. The `defaults` section is dead config.

## Acceptance Criteria

- [x] `examples/copilot/graph.yaml` contains all 4 stages: Plan → Judge → Summarize → Write Diary
- [x] `examples/copilot/graph.yaml` tool declaration uses `examples.shared.diary` (FR-097 landed concurrently)
- [x] `examples/copilot/prompts/summarize.yaml` uses DiaryEntry schema with theme, body, seed
- [x] `examples/copilot/prompts/summarize.yaml` uses Jinja2 syntax with `{{ plan_output | default(...) }}`
- [x] `examples/copilot/prompts/plan.yaml` and `judge.yaml` include FR-084 provenance comments
- [x] Graph variables map to `{state.plan_result}` (full object, not `.output`)
- [x] `exports` section is removed from the merged graph
- [x] `.chaplain/watch.sh` references `examples/copilot/graph.yaml`
- [x] `.chaplain/graph.yaml` and `.chaplain/prompts/` are deleted
- [x] `yamlgraph graph lint examples/copilot/graph.yaml` passes
- [x] `examples/copilot/README.md` documents the full 4-stage workflow
- [x] `ARCHITECTURE.md` REQ-YG-090 file paths updated to `examples/copilot/` locations
- [x] `defaults` section removed from merged graph (dead config)
- [x] No remaining references to `.chaplain/graph.yaml` in the codebase (except CHANGELOG, historical FR docs, and diary entries)
- [x] Tests pass (no existing tests depend on `.chaplain/graph.yaml` path)

## Constraints

- **FR-097 synergy**: FR-097 (shared diary module) landed concurrently, so the merged graph uses `examples.shared.diary` directly — no tech debt marker needed.
- **No new features**: This is a pure consolidation. No new stages, prompts, or capabilities are introduced.
- **Backward compatible**: `.chaplain/watch.sh` continues to work identically after the path change.

## Alternatives Considered

1. **Symlink `.chaplain/graph.yaml` → `examples/copilot/graph.yaml`**: Simpler but symlinks add git complexity and platform issues. The watch.sh path change is cleaner.

2. **Keep both, extract shared base**: Over-engineered for two files. YAML graph inheritance doesn't exist yet and shouldn't be built for this case.

3. **Make `.chaplain/` the canonical location**: Violates project convention that `examples/` is the discoverable demo location. Users browsing examples wouldn't find the copilot pattern.

4. **Update exports to reference `diary_entry`**: Rejected — DiaryEntry is a structured Pydantic object (theme, body, seed), not a markdown string. Exporting it as markdown would require a format adapter. Since `write_diary` already handles persistence, the export is unnecessary complexity.

## Related

- [FR-081](../../feature-requests/FR-081-copilot-node.md) — Copilot node type (original)
- [FR-084](../../feature-requests/FR-084-copilot-watch-migration.md) — Watch migration (created the fork)
- [FR-093](../../feature-requests/FR-093-chaplain-diary-append.md) — Diary append (diverged .chaplain/)
- [FR-097](../../feature-requests/FR-097-refactor-diary-writing-shared.md) — Refactor diary writing (related shared module)
- `.chaplain/watch.sh` — Consumer of the graph
- `examples/copilot/README.md` — Documentation to update
