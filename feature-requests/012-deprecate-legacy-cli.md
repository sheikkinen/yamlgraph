# Feature Request: Deprecate Legacy CLI Commands

**Priority:** HIGH  
**Status:** Proposed  

## Summary

Remove legacy CLI commands (`run`, `resume`, `trace`, `export`, `list-runs`) and associated modules that duplicate functionality now handled by `yamlgraph graph run` and LangGraph checkpointers.

## Problem

The codebase has two parallel systems for running pipelines:

### Legacy Pattern (TO REMOVE)
```bash
yamlgraph run --topic AI --style casual --word-count 300
yamlgraph list-runs
yamlgraph resume <thread-id>
yamlgraph trace
yamlgraph export --thread-id <id>
```

### Modern Pattern (TO KEEP)
```bash
yamlgraph graph run graphs/any-graph.yaml --var topic=AI --var style=casual
yamlgraph graph run ... --thread-id <id>  # Resume with checkpointer
```

### Issues with Legacy System

1. **Hardcoded parameters**: `cmd_run` only works with `topic`, `style`, `word_count` - useless for any other graph
2. **Duplicate storage**: `YamlGraphDB` (320 lines) duplicates LangGraph's SqliteSaver
3. **Confusion**: Two ways to run graphs, different state management
4. **Maintenance burden**: ~660 lines of code that adds no value
5. **Dead code**: `builder.py` sets `graph._checkpointer` which is never read

## Proposed Solution

### Phase 1: Add Deprecation Warnings (v0.4.0)

Add `DeprecationWarning` to all legacy commands:

```python
def cmd_run(args: Namespace) -> None:
    """Run the yamlgraph pipeline."""
    import warnings
    warnings.warn(
        "yamlgraph run is deprecated. Use: yamlgraph graph run graphs/yamlgraph.yaml --var topic=X",
        DeprecationWarning,
        stacklevel=2
    )
    # ... existing code
```

### Phase 2: Remove Legacy Code (v0.5.0)

Delete the following:

| File | Lines | Purpose |
|------|-------|---------|
| `yamlgraph/cli/commands.py` | 231 | Legacy cmd_* functions |
| `yamlgraph/storage/database.py` | 320 | YamlGraphDB (custom SQLite) |
| `yamlgraph/builder.py` | 110 | Thin wrapper (dead checkpointer code) |
| `tests/unit/test_database.py` | 145 | Tests for YamlGraphDB |
| `tests/integration/test_resume.py` | 75 | Tests for build_resume_graph |
| **Total** | **~880** | |

### CLI Commands to Remove

| Command | Replacement |
|---------|-------------|
| `yamlgraph run` | `yamlgraph graph run <graph.yaml> --var key=value` |
| `yamlgraph list-runs` | Use LangSmith or checkpointer directly |
| `yamlgraph resume` | `yamlgraph graph run <graph.yaml> --thread-id <id>` |
| `yamlgraph trace` | LangSmith trace URL (already shown in output) |
| `yamlgraph export` | `yamlgraph graph run ... --output results.json` |

## Migration Guide

### Before (Legacy)
```bash
# Run with hardcoded params
yamlgraph run --topic "Quantum Computing" --style informative

# Resume interrupted run
yamlgraph resume abc123

# List past runs
yamlgraph list-runs --limit 10

# Export run
yamlgraph export --thread-id abc123 --output results.json
```

### After (Modern)
```bash
# Run any graph with any variables
yamlgraph graph run graphs/yamlgraph.yaml \
  --var topic="Quantum Computing" \
  --var style=informative

# Resume with checkpointer
yamlgraph graph run graphs/yamlgraph.yaml --thread-id abc123

# List runs - use LangSmith UI or:
# sqlite3 ~/.yamlgraph/checkpoints.db "SELECT * FROM checkpoints"

# Export - output flag on graph run
yamlgraph graph run graphs/yamlgraph.yaml --output results.json
```

### Python API Migration

The `build_graph` function is used by `examples/yamlgraph_gen/` and tests.
Keep it as an alias in `__init__.py`:

```python
# yamlgraph/__init__.py - KEEP build_graph as alias
from yamlgraph.graph_loader import load_and_compile as build_graph
```

This preserves backward compatibility:
```python
# Before and after (still works)
from yamlgraph import build_graph
graph = build_graph("path/to/graph.yaml").compile()

# Or use explicit API
from yamlgraph.graph_loader import load_and_compile
graph = load_and_compile("path/to/graph.yaml").compile()
```

## Impact Analysis

### Code Removed
- `yamlgraph/cli/commands.py` - 231 lines
- `yamlgraph/storage/database.py` - 320 lines  
- `yamlgraph/builder.py` - 110 lines
- `tests/unit/test_database.py` - 145 lines
- `tests/integration/test_resume.py` - 75 lines
- CLI parser entries in `yamlgraph/cli/__init__.py` - ~50 lines

### Exports Updated in `__init__.py`
```python
# REMOVE from yamlgraph/__init__.py
from yamlgraph.builder import build_graph, run_pipeline, build_resume_graph
from yamlgraph.storage import YamlGraphDB

# ADD alias (backward compatible)
from yamlgraph.graph_loader import load_and_compile as build_graph

# REMOVE from __all__
"run_pipeline",
"build_resume_graph",
"YamlGraphDB",

# KEEP in __all__ (now aliased)
"build_graph",
```

### Tests to Update
| Test File | Action |
|-----------|--------|
| `tests/unit/test_database.py` | DELETE (tests YamlGraphDB) |
| `tests/integration/test_resume.py` | DELETE (tests build_resume_graph) |
| `tests/integration/test_pipeline_flow.py` | UPDATE imports to use load_and_compile |
| `tests/unit/test_issues.py` | UPDATE imports to use load_and_compile |
| `tests/conftest.py` | REMOVE temp_db fixture |

### External Code (examples/yamlgraph_gen)
No changes needed - `build_graph` alias preserves compatibility.

## Dead Code Identified

### `builder.py` checkpointer logic (NEVER USED)
```python
# This line in builder.py sets an attribute that's never read:
graph._checkpointer = checkpointer  # Dead code - remove
```

### `build_resume_graph` (ALIAS ONLY)
```python
def build_resume_graph() -> StateGraph:
    return build_graph()  # Just an alias - remove
```

## Validation

- [x] All examples use `yamlgraph graph run`, not `yamlgraph run`
- [x] `build_graph` is used by yamlgraph_gen - preserve as alias
- [x] `graph._checkpointer` is dead code - never read
- [ ] No external docs reference legacy commands
- [ ] Deprecation warnings appear for 1 release cycle
- [ ] Clean removal with no import errors

## Timeline

| Version | Action |
|---------|--------|
| v0.4.0 | Add deprecation warnings, update docs |
| v0.5.0 | Remove legacy code entirely |

## Alternatives Considered

### Keep Both Systems
❌ Maintenance burden, user confusion, technical debt

### Immediate Removal (No Deprecation)
❌ Breaking change without warning, poor DX

### Merge YamlGraphDB into Checkpointer
❌ Adds complexity for no benefit - just use LangGraph's SqliteSaver
