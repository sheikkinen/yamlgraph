# FR-688: CLI Variables Injection from Graph YAML

**Status**: Closed (implemented by FR-689)
**Type**: feat
**Scope**: cli
**Closed**: 2026-07-05 — Fix shipped in commit `b249c98c` as part of FR-689 enforcement. Both graph-tool and CLI paths now inject `variables:` from YAML.

## Problem

The `variables:` section in graph YAML works for graph-tools (FR-686 added `default_variables` injection) but is ignored by the CLI when running the top-level graph. This creates an asymmetry: the same YAML key behaves differently depending on invocation context.

**Concrete failure**: Running `yamlgraph graph run examples/novel_fandom/genesis.yaml --full` fails with `"premise_file variable not set"` even though `genesis.yaml` declares:

```yaml
variables:
  premise_file: "examples/novel_fandom/premises/floodmark-saga.txt"
```

The workaround is `--var premise_file=...`, which defeats the purpose of declaring defaults in YAML.

## Current Behavior

```
CLI --var / --var-file / --import-state → initial_state → _build_run_config → merge graph_config.data → invoke
```

The `variables:` section from raw YAML config is never consulted for the top-level graph.

## Proposed Behavior

```
graph_config.raw_config["variables"] (lowest priority)
  < graph_config.data
    < --import-state
      < --var-file
        < --var (highest priority)
```

YAML `variables:` provides defaults; every other source overrides.

## Implementation

**File**: `yamlgraph/cli/graph_run_helpers.py`, function `_build_run_config`

Insert YAML variables as the lowest-priority layer, below `graph_config.data`:

```python
def _build_run_config(args, graph_config, initial_state):
    # FR-688: Inject YAML variables as defaults (lowest priority)
    yaml_vars = graph_config.raw_config.get("variables") or {}
    if yaml_vars:
        initial_state = {**yaml_vars, **initial_state}

    if graph_config.data:
        initial_state = {**graph_config.data, **initial_state}
    ...
```

**Alternatively**, inject in `graph_commands.py` before `_build_run_config`:

```python
graph_config = load_graph_config(str(graph_path))
# FR-688: YAML variables as lowest-priority defaults
yaml_vars = graph_config.raw_config.get("variables") or {}
initial_state = {**yaml_vars, **initial_state}
```

## Acceptance Criteria

1. `yamlgraph graph run examples/novel_fandom/genesis.yaml --full` succeeds without `--var premise_file=...`
2. `--var premise_file=other.txt` overrides the YAML default
3. `--var-file` overrides YAML defaults
4. `--import-state` overrides YAML defaults
5. Graph-tool `default_variables` behavior (FR-686) is unchanged
6. Test: YAML variables injected as defaults
7. Test: CLI --var overrides YAML variables

## Risks

- **Type coercion**: YAML `variables:` values are strings; CLI `--var` values are also strings. No mismatch.
- **Existing graphs**: No graph currently relies on `variables:` being ignored at the CLI level, so this is purely additive.
- **data_files overlap**: `graph_config.data` (from `data_files:`) already merges into state. `variables:` should layer below it.

## References

- FR-686: Added `default_variables` for graph-tools
- Diary: 2026-07-05 "The Agent Reads Before It Writes" — documents the asymmetry
