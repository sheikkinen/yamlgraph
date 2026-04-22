# Feature Request: FR-269 CLI Inter-Run State Chaining (`--import-state` / `--export-state`)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-04-22

## Summary

Add `--export-state <path>` and `--import-state <path>` flags to `yamlgraph graph run`, enabling external orchestrators to chain separate graph invocations across shell boundaries while preserving state — including `CopilotResult.session_id` for copilot session resume.

## Value Statement

Pipeline authors can chain independent `yamlgraph graph run` calls across shell boundaries without losing state, enabling patterns like plan → shell tests → enforce with session continuity.

## Problem

Each `yamlgraph graph run` invocation is stateless — state produced by one run is unavailable to the next. External orchestrators (shell scripts, CI pipelines) that execute commands between graph invocations have no mechanism to hand off state explicitly.

The concrete pain point is the watcher2 pipeline:

1. Run a `plan` graph → produces `CopilotResult` with a `session_id`
2. Run shell commands between graph invocations (`pytest`, `git commit`, `pre-commit`)
3. Run an `enforce` graph → must resume the prior copilot session by reading `session_id`

Currently step 3 has no access to state from step 1.

Passing `session_id` via `--var` is fragile: callers must know the key name and parse it from the previous run's stdout, coupling the caller to output format.

## Proposed Solution

Two new flags on `yamlgraph graph run`:

### `--export-state <path>`

Writes the full post-run graph state as JSON to the explicit path provided.

```bash
yamlgraph graph run plan.yaml \
  --var topic_file="$TOPIC" \
  --export-state tmp/state.json \
  --full
```

- Serializes the entire state dict using the existing `_serialize_state()` logic (Pydantic models via `.model_dump()`)
- Writes to the explicit path (not a timestamped auto-generated name)
- Creates parent directories if they do not exist
- Distinct from the existing `--export` flag, which exports specific fields via the graph's `exports:` YAML config

### `--import-state <path>`

Loads a previously exported state JSON as the base initial state before the run.

```bash
yamlgraph graph run enforce.yaml \
  --import-state tmp/state.json \
  --full
```

Merge priority (highest last wins):

```
imported JSON state < --var-file values < --var CLI values
```

Combined chaining example:

```bash
# Step 1: Plan graph — export state
yamlgraph graph run plan.yaml --var topic_file="$TOPIC" --export-state tmp/state.json --full

# Step 2: Shell scripts run between graph invocations
pytest tests/ -x --no-cov -q
git add -A && git commit -m "..."

# Step 3: Enforce graph — import prior state (session_id available for resume)
yamlgraph graph run enforce.yaml --import-state tmp/state.json --full
```

### Round-trip fidelity

`CopilotResult` objects serialize to plain dicts via `.model_dump()`. On import they remain plain dicts. The existing `resolve_state_expression()` in `expressions.py` handles both dict key access and object attribute access (`isinstance(value, dict)` checked first), so `{state.prev_result.session_id}` resolves correctly from either form.

## Acceptance Criteria

- [ ] `--export-state <path>` writes the full post-run state to `<path>` as JSON
- [ ] `--export-state` creates parent directories if they are missing
- [ ] `--import-state <path>` loads state from `<path>` and uses it as the base initial state
- [ ] Merge order: imported state < `--var-file` < `--var` (CLI vars always win)
- [ ] `--import-state` combined with `--var` overrides: `--var` values overwrite matching imported keys
- [ ] Round-trip: `CopilotResult.session_id` survives export → import and is accessible via `{state.prev_result.session_id}` in graph YAML
- [ ] Both flags are independent (usable alone or together)
- [ ] `--import-state` with a non-existent file prints a clear error message and exits 1
- [ ] `--export-state` failure (permissions, invalid path) prints a clear error message and exits 1
- [ ] Tests cover: export then import round-trip, merge precedence (imported < var-file < var), missing file error
- [ ] `yamlgraph graph run --help` shows both new flags with description
- [ ] REQ-YG-267 and REQ-YG-268 added to `ARCHITECTURE.md` capabilities table

## Implementation Approach

### Files to change

| File | Change |
|------|--------|
| `yamlgraph/cli/__init__.py` | Add `--export-state` and `--import-state` argument definitions to `graph_run_parser` |
| `yamlgraph/cli/graph_commands.py` | In `cmd_graph_run()`: load imported state before `_build_run_config()`; call export after successful run |
| `yamlgraph/storage/export.py` | Add `export_state_to_path(state, path)` writing to an explicit filepath (wraps `_serialize_state()`) |
| `ARCHITECTURE.md` | Add REQ-YG-267 and REQ-YG-268 to capabilities table |

### Argument definitions (`cli/__init__.py`)

```python
graph_run_parser.add_argument(
    "--import-state",
    type=str,
    default=None,
    dest="import_state",
    help="Load initial state from JSON file exported by --export-state",
)
graph_run_parser.add_argument(
    "--export-state",
    type=str,
    default=None,
    dest="export_state",
    help="Write full state JSON to this path after run (for inter-run chaining)",
)
```

### State merge in `cmd_graph_run()` (`graph_commands.py`)

```python
# After parse_vars / var_file loading, before _build_run_config:
if args.import_state:
    import_path = Path(args.import_state)
    if not import_path.exists():
        print(f"❌ --import-state file not found: {import_path}")
        sys.exit(1)
    from yamlgraph.storage.export import load_export
    imported = load_export(import_path)
    initial_state = {**imported, **file_vars, **cli_vars}
else:
    initial_state = {**file_vars, **cli_vars}
```

### New export helper (`storage/export.py`)

```python
def export_state_to_path(state: dict, path: str | Path) -> Path:
    """Export full pipeline state to an explicit file path.

    Used by --export-state CLI flag for inter-run state chaining.
    """
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(_serialize_state(state), f, indent=2, default=str)
    return filepath
```

### Export call in `cmd_graph_run()` (after result)

```python
if getattr(args, "export_state", None):
    from yamlgraph.storage.export import export_state_to_path
    p = export_state_to_path(result, args.export_state)
    print(f"\n💾 State exported: {p}")
```

## Constraints

- `--export-state` is **distinct** from the existing `--export` flag (field-level YAML `exports:` config). No change to existing `--export` behavior.
- Imported state is shallow-merged at the top level only. Deep merging of nested dicts is out of scope.
- No type reconstruction on import: Pydantic models remain plain dicts after round-trip. Graph YAML must use dict-compatible state expressions — already satisfied by `resolve_state_expression()`.
- No schema validation of the imported JSON against the graph's state class — out of scope.

## Alternatives Considered

- **Extend `--export` to accept a path**: `--export` is currently `action="store_true"` and semantically refers to field-level YAML exports. Overloading it would be confusing and break existing behavior.
- **Checkpoint/resume via LangGraph checkpointer**: Requires matching `thread_id` and a persistent checkpointer (SQLite/Redis). Too heavy for shell-script orchestration. Complements but does not replace this feature.
- **Pass `session_id` via `--var`**: Requires callers to know the key name and parse it from the previous run's stdout. Fragile and couples the caller to output format.

## Related

- `yamlgraph/storage/export.py` — `export_state()`, `load_export()`, `_serialize_state()`
- `yamlgraph/cli/__init__.py` — argument parser
- `yamlgraph/cli/graph_commands.py` — `cmd_graph_run()`, `_build_run_config()`
- `yamlgraph/utils/expressions.py` — `resolve_state_expression()` (handles dict + object access)
- `yamlgraph/models/schemas.py` — `CopilotResult` (session_id field)
- `docs/refactoring-watcher-pipeline-v3.md` section 7 — design rationale
- REQ-YG-267: `--import-state` loads exported JSON as initial graph state
- REQ-YG-268: `--export-state` writes full run state to an explicit JSON path
