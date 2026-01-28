# FR-012-3: Remove Legacy CLI Code (Phase 2)

**Priority:** MEDIUM  
**Status:** Proposed  
**Parent:** FR-012 (Deprecate Legacy CLI)  
**Target:** v0.5.0

## Summary

Remove all deprecated legacy CLI code after deprecation warnings have been in place for one release cycle.

## Prerequisites

All completed in v0.4.0:
- ✅ FR-012-0: Fix CLI checkpointer
- ✅ FR-012-1: Deprecate legacy resume
- ✅ FR-012-2: Deprecate list-runs, trace, export; delete dead cmd_run

## Code to Remove

| Item | Lines | Location |
|------|-------|----------|
| `cmd_list_runs` | ~30 | `yamlgraph/cli/commands.py` |
| `cmd_trace` | ~20 | `yamlgraph/cli/commands.py` |
| `cmd_export` | ~20 | `yamlgraph/cli/commands.py` |
| `cmd_resume` | ~50 | `yamlgraph/cli/commands.py` |
| CLI parser entries | ~40 | `yamlgraph/cli/__init__.py` |
| `YamlGraphDB` | ~320 | `yamlgraph/storage/database.py` |
| `build_resume_graph` | ~20 | `yamlgraph/builder.py` |
| Dead checkpointer code | ~10 | `yamlgraph/builder.py` |
| `test_database.py` | ~145 | `tests/unit/` |
| `test_resume.py` | ~75 | `tests/integration/` |
| CLI docs | ~40 | `reference/cli.md` |
| **Total** | **~770** | |

## Exports to Update

```python
# yamlgraph/__init__.py - REMOVE
from yamlgraph.builder import build_graph, run_pipeline, build_resume_graph
from yamlgraph.storage import YamlGraphDB

# yamlgraph/__init__.py - ADD (alias for backward compat)
from yamlgraph.graph_loader import load_and_compile as build_graph

# __all__ - REMOVE
"run_pipeline",
"build_resume_graph", 
"YamlGraphDB",
```

## Implementation Plan

### Step 1: Remove CLI Commands
- Delete `cmd_list_runs`, `cmd_trace`, `cmd_export`, `cmd_resume` from `commands.py`
- Delete CLI parser entries from `__init__.py`

### Step 2: Remove YamlGraphDB
- Delete `yamlgraph/storage/database.py`
- Update `yamlgraph/storage/__init__.py` exports

### Step 3: Clean up builder.py
- Delete `build_resume_graph()`
- Delete dead `graph._checkpointer` line
- Consider deleting entire file if only `run_pipeline` remains

### Step 4: Remove Tests
- Delete `tests/unit/test_database.py`
- Delete `tests/integration/test_resume.py`
- Update `tests/unit/test_issues.py` if it uses legacy functions

### Step 5: Update Documentation
- Remove legacy commands from `reference/cli.md`
- Update README.md if needed

## Validation Checklist

- [ ] All deprecated commands removed
- [ ] YamlGraphDB deleted
- [ ] build_resume_graph deleted
- [ ] Legacy tests deleted
- [ ] No import errors
- [ ] All remaining tests pass
- [ ] Documentation updated

## Timeline

This FR should be implemented after v0.4.0 is released and users have had time to migrate.
