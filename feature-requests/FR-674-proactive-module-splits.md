# Feature Request: Proactive module splits for the 435-450 line band

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged
**Effort:** 1 day
**Requested:** 2026-07-03

## Summary

Five modules sit in the 435–450 line band, one edit from the 450 hard
ceiling: `node_compiler.py` (447), `models/state_builder.py` (442),
`models/graph_schema.py` (441), `linter/checks_semantic.py` (435),
`executor_async.py` (435). Split them proactively along existing seams
before the ceiling forces an unplanned split mid-feature.

## Value Statement

Feature work touching these modules never stalls on an emergency refactor;
each split lands as a reviewed, mechanical, behavior-preserving change.

## Problem

Codebase standard: modules < 400 lines, max 450 (Commandment 8: split
before bloat). All five modules are legitimate change targets for active
FRs (FR-668 touches state_builder, FR-672 touches executor_async, FR-673
touches graph_schema and node_compiler). Any of those FRs adding net lines
breaches the ceiling and forces a mixed commit
(`mixed_commits_erode_auditability`).

## Proposed Solution

Mechanical extractions along existing seams — no behavior change, no new
abstractions:

| Module | Lines | Extraction |
|--------|-------|------------|
| `node_compiler.py` | 447 | Per-type compile helpers → `node_compiler_handlers.py` (keep `NODE_TYPE_HANDLERS` dispatch in place) |
| `models/state_builder.py` | 442 | `generate_typeddict_code` + helpers → `models/codegen.py` |
| `models/graph_schema.py` | 441 | Guard/verification configs (`GuardRuleBase`, `PreGuardRule`, `PostGuardRule`, `GuardConfig`, `VerificationConfig`) → `models/guard_schema.py` |
| `linter/checks_semantic.py` | 435 | Cycle checks (`check_unguarded_cycles`, `check_skip_if_exists_in_cycle`) → `linter/checks_cycles.py` |
| `executor_async.py` | 435 | Covered by FR-672 retry extraction — no separate action |

One commit per module split (`refactor(scope): FR-674 split X`), each
re-exporting moved names from the original module's namespace only where an
external import exists (check `examples/` and `tests/` first; prefer fixing
importers over re-exports — no shims, Commandment 8).

Sequencing: land before or interleaved with FR-668/FR-672/FR-673 so those
FRs work against the post-split layout.

## Acceptance Criteria

- [ ] All five modules < 400 lines (`find yamlgraph -name '*.py' | xargs wc -l`)
- [ ] No behavior change: full test suite green with zero test edits other
      than import paths
- [ ] `lint-imports` contracts still KEPT
- [ ] One commit per module split
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

- **Wait until a feature breaches the ceiling** — rejected: forces the
  split into an unrelated feature branch, mixing concerns.
- **Raise the ceiling** — rejected: the limit exists to force cohesion; the
  seams above are natural, not contrived.

## Related

- docs/2026-07-03-review-fable.md (Refactoring: module-size band)
- FR-668, FR-672, FR-673 (sequencing)

## Judgement

**APPROVED with corrections.** The line counts in the FR are wrong:

| Module | FR claims | Actual | Status |
|--------|-----------|--------|--------|
| node_compiler.py | 447 | 434 | Under ceiling |
| state_builder.py | 442 | 471 | OVER ceiling |
| graph_schema.py | 441 | ~610 | FAR over ceiling |
| checks_semantic.py | 435 | 469 | OVER ceiling |
| executor_async.py | 435 | 435 | Accurate |

Three modules already exceed the 450 hard ceiling. This is not
"proactive" — it's overdue remediation. Title should reflect urgency.

**Amendments:**
1. Rename to "Module splits for ceiling violations" — this is not
   proactive; state_builder.py, graph_schema.py, and checks_semantic.py
   are already in violation.
2. Priority: LOW → HIGH. Three ceiling violations are blocking.
3. `graph_schema.py` at ~610 lines needs more aggressive splitting than
   proposed — guard/verification configs alone won't bring it under 400.
   Plan two extraction targets.
4. `node_compiler.py` at 434 is under ceiling. Remove from scope unless
   it has a natural seam worth splitting. Don't split what isn't broken.
5. FR-672 is rejected, so `executor_async.py` won't shrink from retry
   extraction. If it needs splitting, identify a different seam.
6. Effort: 1-2 days → 1 day. These are mechanical moves with no behavior
   change. One commit per module, as proposed.
