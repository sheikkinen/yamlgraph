# FR-012-1: Deprecate Legacy Resume System

**Priority:** HIGH  
**Status:** ✅ IMPLEMENTED (deprecation warnings added)  
**Parent:** FR-012 (Deprecate Legacy CLI)  
**Blocked By:** FR-012-0 (Fix CLI Checkpointer) - ✅ DONE

## Implementation Status

- [x] FR-012-0: `cmd_graph_run` now uses `get_checkpointer_for_graph()`
- [x] `build_resume_graph()` emits `DeprecationWarning`
- [x] `cmd_resume` emits `DeprecationWarning` and prints deprecation message
- [ ] v0.5.0: Remove deprecated code entirely

---

## Summary

Deprecate `yamlgraph resume` CLI command and `build_resume_graph()` function. These implement a legacy resume pattern that's been superseded by LangGraph checkpointers + `Command(resume=...)`.

## Two Different "Resume" Concepts

### 1. Legacy Resume (TO DEPRECATE)

**What it does:** Re-runs a pipeline from saved state, skipping nodes whose outputs already exist (`skip_if_exists`).

**Components:**
- `yamlgraph resume --thread-id <id>` - CLI command
- `build_resume_graph()` - Just an alias for `build_graph()`
- `YamlGraphDB` - Custom SQLite storage for state
- `skip_if_exists: true` on LLM nodes - Skip if state_key already populated

**Use case:** Linear pipelines (generate → analyze → summarize) where you want to:
1. Run partially, fail/interrupt
2. Fix the issue
3. Re-run skipping already-completed steps

**Limitations:**
- ❌ Only works with default `graphs/yamlgraph.yaml`
- ❌ Hardcoded for `topic`, `style`, `word_count` params
- ❌ Custom `YamlGraphDB` storage, not LangGraph checkpointers
- ❌ No support for interrupt nodes (human-in-the-loop)

### 2. Modern Resume (TO KEEP)

**What it does:** Continues execution from an interrupt point using LangGraph's native checkpointing.

**Components:**
- `Command(resume=value)` - LangGraph primitive
- `checkpointer` in graph YAML - sqlite/redis/memory
- `--thread-id` flag on `yamlgraph graph run`
- Interrupt nodes with `resume_key`

**Use case:** Human-in-the-loop flows where you need to:
1. Ask user a question (interrupt)
2. Wait for response
3. Continue execution with their answer

**Examples:**
```python
# Modern: interrupt resume via Command
result = app.invoke(Command(resume="Alice"), config)

# Modern: checkpointer-based session continuity
result = app.invoke({"input": "continue"}, {"configurable": {"thread_id": "session-123"}})
```

## Code Analysis

### `build_resume_graph()` - Dead Code

```python
# yamlgraph/builder.py
def build_resume_graph() -> StateGraph:
    """Build a graph for resuming an interrupted pipeline."""
    return build_graph()  # Just an alias!
```

This function:
- Returns exactly the same graph as `build_graph()`
- Resume behavior comes from `skip_if_exists` on nodes, not from the graph itself
- Only works because `YamlGraphDB` stores/loads state between runs

### `cmd_resume` - Legacy CLI

```python
# yamlgraph/cli/commands.py
def cmd_resume(args: Namespace) -> None:
    db = YamlGraphDB()
    state = db.load_state(args.thread_id)  # Custom DB, not checkpointer
    
    # Hardcoded logic for yamlgraph.yaml nodes
    if state.get("generated"):
        skipping.append("generate")
    if state.get("analysis"):
        skipping.append("analyze")
    
    graph = build_resume_graph().compile()  # No checkpointer!
    result = graph.invoke(state)
    
    db.save_state(args.thread_id, result)  # Save back to custom DB
```

Problems:
1. Uses `YamlGraphDB` instead of graph's configured checkpointer
2. Hardcoded for `generated`, `analysis`, `final_summary` state keys
3. Doesn't use `Command(resume=...)` for interrupt handling
4. Only works with `graphs/yamlgraph.yaml`

### Modern Equivalent

```bash
# Using checkpointer + thread_id (REQUIRES FR-012-0 FIX)
yamlgraph graph run graphs/my-graph.yaml --thread abc123
```

**⚠️ NOTE:** This currently does NOT work! See FR-012-0.

After FR-012-0 is implemented, this will:
- Use graph's configured checkpointer
- Work with any graph
- Handle interrupts via `Command(resume=...)`
- No custom database needed

## Usage Analysis

### Who uses `build_resume_graph()`?

| Location | Usage | Verdict |
|----------|-------|---------|
| `yamlgraph/__init__.py` | Export | Remove |
| `yamlgraph/cli/commands.py` | `cmd_resume` | Remove with cmd_resume |
| `tests/unit/test_issues.py` | One test | Update to use `load_and_compile` |
| `tests/integration/test_resume.py` | 2 test classes | Delete (tests legacy behavior) |
| `tests/integration/test_pipeline_flow.py` | TestBuildResumeGraph class | Delete class |

### Who uses `yamlgraph resume`?

```bash
grep -r "yamlgraph resume" reference/ docs/ examples/
# Result: reference/cli.md (documentation only)
```

No actual usage in examples - only documented.

### Who uses `YamlGraphDB.load_state()` for resume?

Only `cmd_resume` in `commands.py`.

## Migration Path

### For CLI Users

```bash
# Before (legacy)
yamlgraph run --topic AI
# ... fails partway through ...
yamlgraph resume --thread-id abc123

# After (modern)
yamlgraph graph run graphs/yamlgraph.yaml --var topic=AI --thread-id session1
# ... fails partway through ...
yamlgraph graph run graphs/yamlgraph.yaml --thread-id session1
# Checkpointer resumes from last state automatically
```

### For Python API Users

```python
# Before (legacy)
from yamlgraph import build_resume_graph
from yamlgraph.storage import YamlGraphDB

db = YamlGraphDB()
state = db.load_state("thread-123")
graph = build_resume_graph().compile()
result = graph.invoke(state)

# After (modern)
from yamlgraph.graph_loader import load_and_compile, get_checkpointer_for_graph

config = load_graph_config("graphs/my-graph.yaml")
graph = compile_graph(config)
checkpointer = get_checkpointer_for_graph(config)
app = graph.compile(checkpointer=checkpointer)

# Resume via thread_id (checkpointer loads state)
result = app.invoke(
    {"input": "continue"},
    {"configurable": {"thread_id": "thread-123"}}
)
```

## What to Remove

| Item | Lines | Location |
|------|-------|----------|
| `build_resume_graph()` | 15 | `yamlgraph/builder.py` |
| `cmd_resume()` | 45 | `yamlgraph/cli/commands.py` |
| Resume CLI parser | 5 | `yamlgraph/cli/__init__.py` |
| `test_resume.py` | 75 | `tests/integration/` |
| TestBuildResumeGraph | 15 | `tests/integration/test_pipeline_flow.py` |
| Export | 2 | `yamlgraph/__init__.py` |
| CLI docs | 10 | `reference/cli.md` |
| **Total** | **~170** | |

## What to Keep

- `skip_if_exists` on LLM nodes - Still useful for idempotency
- `Command(resume=...)` - LangGraph native resume for interrupts
- `--thread-id` on `yamlgraph graph run` - Already works with checkpointers
- Checkpointer system - Modern state persistence

## Validation Checklist

- [ ] **FR-012-0 complete** (CLI uses checkpointer)
- [ ] No examples use `yamlgraph resume`
- [ ] No examples use `build_resume_graph()`
- [ ] Modern resume via checkpointer works: `yamlgraph graph run --thread`
- [ ] Interrupt resume via `Command(resume=...)` documented in reference/interrupt-nodes.md

## Timeline

| Version | Action |
|---------|--------|
| v0.3.34 | **FR-012-0**: Fix CLI to use checkpointer |
| v0.4.0 | Add deprecation warning to `cmd_resume`, `build_resume_graph` |
| v0.5.0 | Remove `cmd_resume`, `build_resume_graph`, tests, docs |

## Related

- **FR-012-0**: Fix CLI checkpointer (PREREQUISITE)
- FR-012: Parent feature request (deprecate all legacy CLI)
- reference/checkpointers.md: Modern resume documentation
- reference/interrupt-nodes.md: Interrupt resume with `Command(resume=...)`
