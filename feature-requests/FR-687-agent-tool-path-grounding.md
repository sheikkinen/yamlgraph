# FR-687: Agent Tool Path Grounding

**Status:** Proposed
**Priority:** High (security + availability)
**Related:** FR-686 (genesis), FR-658 (graph-tools)

## Problem

Agent-facing tools that accept filesystem paths (e.g. `canon_dir` parameter) have no basepath grounding. The LLM can pass arbitrary paths like `/`, causing:

1. **Availability failure**: `list_canon_ids({'canon_dir': '/'})` scans the entire filesystem tree, effectively hanging the process indefinitely. This halted the FR-686 genesis pipeline.
2. **Information disclosure**: Tools could read files outside the project boundary.
3. **Silent failure mode**: The parent agent sees no response (timeout), retries, wastes tokens, eventually gives up — with no indication that a tool parameter was malformed.

## Root Cause

The `canon_dir` parameter exists as an LLM-facing argument because the tool was originally designed for flexible invocation. But an agent operating within a pipeline has no legitimate reason to pass anything other than the default canon path. The parameter is an attack surface with zero utility.

## Observation: Broader Pattern

This is `the_one_law` — normalize at the boundary where external data enters. For agent tools, the boundary is the tool's function signature. Any parameter that accepts a filesystem path from an LLM must be grounded:

```
LLM output → tool parameter → filesystem access
              ^^^^^^^^^^^^^^^^^
              Normalize HERE: resolve + assert startswith(basepath)
```

## Fix Applied (Immediate)

`examples/novel_fandom/nodes/canon_tools.py`: `_load_canon()` now resolves the candidate path and rejects anything outside the project directory. Falls back to `_CANON_DIR`.

## Acceptance Criteria

- [x] AC-1: `_load_canon` rejects paths outside project boundary
- [ ] AC-2: `list_canon_ids`, `lookup_canon_page`, `validate_draft` cannot scan outside canon
- [ ] AC-3: Test: `list_canon_ids(canon_dir="/")` returns empty list (not hang)
- [ ] AC-4: Test: `list_canon_ids(canon_dir="/etc")` returns empty list
- [ ] AC-5: Consider removing `canon_dir` parameter entirely from LLM-facing tools (it serves no purpose when grounded)

## Broader Consideration (Future FR)

Any `type: python` tool exposed to an agent should have a declarative `basepath:` constraint in the tool config. The framework could enforce grounding mechanically rather than relying on each tool implementation to guard itself. Pattern:

```yaml
tools:
  list_canon_ids:
    type: python
    path: nodes/canon_tools.py
    function: list_canon_ids
    sandbox:
      filesystem: relative  # all path params grounded to graph source dir
```

This is a framework-level concern — not just novel_fandom.

## Scripture Connection

- **Trap**: `downstream_fix` — the symptom (hang) manifests downstream, but the entry boundary is the tool's parameter interface.
- **Cure**: `ask_before_generate` — the LLM should never need to specify a filesystem path for a grounded resource. Remove the affordance.
