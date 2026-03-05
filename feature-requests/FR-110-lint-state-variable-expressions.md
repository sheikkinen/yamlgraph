# Feature Request: Promote W014 to error — undeclared `{state.X}` expressions

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-03-04

## Summary

Promote the existing `W014` lint check from `severity="warning"` to `severity="error"`,
rename it to **E007**, and update all references accordingly.

## Value Statement

Graph authors get a hard lint failure — not a silenceable warning — when a node variable
expression references an undeclared state field, preventing `KeyError` crashes at runtime.

## Problem

`W014` (`_check_w014_unknown_state_refs` in `linter/checks_semantic.py`) already detects
`{state.X}` expressions that reference fields not in `known_fields`. However it fires as a
**warning**, which:

- Can be ignored or suppressed in CI
- Does not block `yamlgraph graph lint` with a non-zero exit code
- Understates the severity: a missing `{state.X}` binding is **always** a runtime
  `KeyError`; there is no partial-graph scenario where it is merely advisory

The original FR-110 proposed a new `E003` check but was blocked because W014 already
existed (ISSUE-1) and `E003` was already taken (ISSUE-2). The correct resolution is to
promote W014 to an error and reclassify it as `E007` (the next free error slot).

## Proposed Solution

1. In `yamlgraph/linter/checks_semantic.py`, change `_check_w014_unknown_state_refs`:
   - `severity="warning"` → `severity="error"`
   - `code="W014"` → `code="E007"`

2. Update the docstring of `check_expression_syntax` to list `E007` instead of `W014`.

3. Update `ARCHITECTURE.md` REQ-YG-069: change description from "warn" to "error", code
   from `W014` to `E007`.

4. Update `scripts/req_coverage.py` if `W014` appears in any code-to-req mapping.

5. Update all tests in `tests/unit/test_linter_fr025.py` that assert on `"W014"` to
   assert on `"E007"`, and update fixture comments.

6. Update fixture files `state_ref_undeclared_pass.yaml` and
   `state_ref_undeclared_fail.yaml` header comments.

```python
# Before
LintIssue(
    severity="warning",
    code="W014",
    message=...,
    fix=...,
)

# After
LintIssue(
    severity="error",
    code="E007",
    message=...,
    fix=...,
)
```

No logic change is required — only the code label and severity string change.

## Acceptance Criteria

- [x] `_check_e007_unknown_state_refs` emits `severity="error"` with `code="E007"` for
      any `{state.X}` where `X` is not in `known_fields`
- [x] The old code `W014` no longer appears in any lint output
- [x] `yamlgraph graph lint examples/demos/hello/graph.yaml` still exits 0 (no regression)
- [x] A graph YAML containing `{state.undeclared}` causes `yamlgraph graph lint` to exit
      non-zero (error, not just warning)
- [x] All existing W014 tests in `tests/unit/test_linter_fr025.py` updated to assert
      `"E007"` and pass
- [x] `ARCHITECTURE.md` REQ-YG-069 updated: `W014` → `E007`, "warn" → "error"
- [x] `scripts/req_coverage.py` — no W014 mapping existed; no change needed
- [x] `CHANGELOG.md` updated

## Alternatives Considered

**Keep W014 as warning but raise separately** — A second check that also fires as an error
would duplicate logic and confuse readers. Reusing the existing implementation is cleaner.

**Keep W-prefix, just change severity** — The `W`/`E` prefix convention in the codebase
signals the severity (`W` = warning, `E` = error). Keeping `W014` with `severity="error"`
would violate that convention and confuse tooling that filters by prefix.

**Add a new E-code alongside W014** — Redundant. W014 already captures the right condition.
Keeping both would require deprecating one immediately.

**Validate at compile time** — `graph_loader.py` is the wrong feedback stage; lint is the
author-facing layer.

## Related

- `yamlgraph/linter/checks_semantic.py` — `_check_w014_unknown_state_refs`, `check_expression_syntax`
- `yamlgraph/linter/checks.py` — E001–E006, E008–E012 (E007 is free)
- `tests/unit/test_linter_fr025.py` — existing W014 tests (lines ~176–192)
- `tests/fixtures/linter/state_ref_undeclared_{pass,fail}.yaml` — W014 fixture files
- `ARCHITECTURE.md` — REQ-YG-069
- `scripts/req_coverage.py` — req traceability mapping
