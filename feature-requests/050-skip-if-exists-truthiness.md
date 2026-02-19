# Feature Request: Skip-If-Exists Truthiness Fix

**FR-050**
**Priority:** HIGH
**Type:** Bug Fix (Breaking Change)
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-19
**Implemented:** 2026-02-19

## Summary

Change `skip_if_exists` semantics from existence check (`is not None`) to truthiness check. This fixes a bug where empty collections (`[]`, `{}`) would trigger skip, preventing nodes from executing when they should.

## Problem

The diary-digest pipeline's `curate_seeds` node never executed because `skip_if_exists: seeds` treated an empty list (`[]`) as "exists".

**Developer intent:** "skip if already has useful data"
**Actual behavior:** "skip if key has any value in state dict, including `[]`, `""`, `0`"

```python
# Current (buggy)
if skip_if_exists and state.get(state_key) is not None:
    return {}  # Skip — triggers on [], "", 0, False

# Fixed (correct)
if skip_if_exists and state.get(state_key):
    return {}  # Skip — only triggers on truthy values
```

## Behavior Change

| Value | Old Behavior | New Behavior |
|-------|-------------|--------------|
| `None` | Skip | Execute |
| `[]` | Skip | **Execute** |
| `""` | Skip | **Execute** |
| `0` | Skip | **Execute** |
| `False` | Skip | **Execute** |
| `[1, 2]` | Skip | Skip |
| `"hello"` | Skip | Skip |
| `42` | Skip | Skip |

## Why Breaking Change is Acceptable

1. **Current behavior is a bug.** The diary-digest failure proves it.
2. **Intent alignment.** Developers use `skip_if_exists` to avoid re-computation when data is present. Empty data isn't "present" in any useful sense.
3. **No existing graphs rely on skip-on-empty.** If they did, they'd have the same bug.
4. **Semantic correctness.** "Exists" in programming idiom means "has meaningful value".

## Acceptance Criteria

- [x] `skip_if_exists` checks truthiness, not existence
- [x] Empty list `[]` does NOT trigger skip
- [x] Empty string `""` does NOT trigger skip
- [x] `None` does NOT trigger skip
- [x] `0` and `False` do NOT trigger skip
- [x] Non-empty collections trigger skip
- [x] CHANGELOG documents breaking change
- [x] reference/graph-yaml.md updated

## Implementation

**Location:** `yamlgraph/node_factory/llm_nodes.py` line 118

```python
# Before
if skip_if_exists and state.get(state_key) is not None:

# After
if skip_if_exists and state.get(state_key):
```

## Test Cases

See `tests/unit/test_skip_if_exists_truthiness.py`

## Related

- FR-046 — Diary World Digest (source of bug)
- Diary entry: "The Onion of Silent Failures" (2026-02-19)
- REQ-YG-074 — Skip-if-exists truthiness behavior
