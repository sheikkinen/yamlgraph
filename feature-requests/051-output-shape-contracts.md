# Feature Request: Output Shape Contracts

**FR-051**
**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Planning
**Effort:** 1-2 days
**Requested:** 2026-02-19

## Summary

Add graph-level `expects:` block to declare output shape constraints. Graph execution fails if outputs don't meet these constraints, preventing silent no-op pipelines.

## Problem

After FR-050 fixed `skip_if_exists`, pipelines can still silently "succeed" with zero useful output:

1. **Empty filter results** — No relevant articles today → proceeds with empty list
2. **Fallback content** — LLM produces "No content available" → valid string, useless output
3. **Valid no-op route** — Routing takes "skip" branch → graph completes, nothing produced

These are _operationally silent failures_. The graph succeeds from the runtime's perspective, but produces nothing useful. Developers discover this only by observing missing outputs (diary not updated) or inspecting LangSmith traces manually.

## Proposed Solution

### Graph-Level `expects:` Block

```yaml
# graph.yaml
name: diary_digest

expects:
  diary_entry:
    min_length: 100      # String must be ≥100 chars
  relevant_articles:
    min_items: 1         # List must have ≥1 items
  synthesis:
    non_empty: true      # Must be truthy (not None, [], "", 0)

nodes:
  # ... normal node definitions
```

### Validation Timing

Constraints are checked **at graph completion** (after END node), not during execution:

```python
# In graph_loader.py or executor.py
def validate_output_contracts(state: dict, expects: dict) -> list[ContractViolation]:
    violations = []
    for key, constraints in expects.items():
        value = state.get(key)

        if "non_empty" in constraints and not value:
            violations.append(ContractViolation(key, "non_empty", value))

        if "min_length" in constraints:
            if not isinstance(value, str) or len(value) < constraints["min_length"]:
                violations.append(ContractViolation(key, "min_length", value))

        if "min_items" in constraints:
            if not hasattr(value, "__len__") or len(value) < constraints["min_items"]:
                violations.append(ContractViolation(key, "min_items", value))

    return violations
```

### Violation Behavior

Options (TBD — pick one):

1. **Raise exception** — Pipeline fails with `OutputContractViolation`
2. **Warning + metadata** — Return `{"_contract_violations": [...]}` in state
3. **Configurable** — `expects_mode: strict|warn|log`

Recommendation: Default to **exception** with `expects_mode: warn` option.

### Constraint Types

| Constraint | Applies To | Example |
|------------|------------|---------|
| `non_empty` | Any | `non_empty: true` |
| `min_length` | str | `min_length: 100` |
| `max_length` | str | `max_length: 5000` |
| `min_items` | list/dict | `min_items: 1` |
| `max_items` | list/dict | `max_items: 50` |
| `matches` | str | `matches: "^[A-Z]"` (regex) |
| `type` | Any | `type: str` or `type: list` |

## Use Cases

### 1. Diary Digest — Detect No-Content Days

```yaml
expects:
  diary_entry:
    min_length: 200
    matches: "^## "  # Must start with markdown header
```

### 2. Code Review — Ensure Issues Found

```yaml
expects:
  issues:
    min_items: 0     # Explicit: zero issues is valid
    # No constraint = "at least empty list exists"
```

### 3. Map Processing — Verify Results

```yaml
expects:
  processed_items:
    min_items: 1
    # If map produces empty results, fail early
```

## Acceptance Criteria

- [ ] `expects:` block parsed in GraphConfig model
- [ ] Validation runs after graph completion
- [ ] `non_empty`, `min_length`, `min_items` implemented
- [ ] `OutputContractViolation` exception with clear message
- [ ] `expects_mode: warn` option logs instead of raising
- [ ] Linter validates `expects` keys match state keys
- [ ] Unit tests for each constraint type
- [ ] Documentation in reference/graph-yaml.md

## Non-Goals

- **Per-node contracts** — This is graph-level only (node outputs can use Pydantic schemas)
- **Complex validation** — No JSON Schema, no nested path expressions
- **Runtime type checking** — Use Pydantic schemas for that

## Alternatives Considered

### 1. Pydantic for Final State

Could define a `FinalStateSchema` that validates complete state:

```yaml
schema: schemas/final_state.yaml
```

**Rejected:** Overkill. Most contracts are simple (`non_empty`, `min_items`). Full Pydantic adds complexity without benefit.

### 2. Assertion Nodes

Add `assert` node type at graph end:

```yaml
nodes:
  validate:
    type: assert
    checks:
      - diary_entry.length >= 100
```

**Rejected:** Verbose. Requires new node type. Better to declare constraints declaratively.

### 3. Post-Hooks

Python callback after graph execution:

```python
def validate_output(state):
    assert len(state["diary_entry"]) > 100
```

**Rejected:** Defeats YAML-first principle. Validation logic should be in YAML.

## Related

- FR-050 — Skip-If-Exists Truthiness (fixed one silent failure cause)
- FR-052 — Map Output Flattening (separate shape issue)
- Diary entry: "The Onion of Silent Failures" (2026-02-19)

## Implementation Notes

1. Add `expects: dict[str, dict]` to `GraphConfig` model
2. Add `validate_output_contracts()` in `executor.py`
3. Call after `graph.invoke()` returns
4. Add `OutputContractViolation(Exception)` with formatted message
5. Include state key, constraint, actual value, expected value
