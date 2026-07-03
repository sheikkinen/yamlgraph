# Feature Request: Proactive module splits for near-ceiling modules

**Priority:** LOW
**Type:** Enhancement
**Status:** Judged
**Effort:** 1 day
**Requested:** 2026-07-03

## Summary

Five modules are in the 435-447 line band, close to the 450-line hard ceiling:
`node_compiler.py` (447), `models/state_builder.py` (442),
`models/graph_schema.py` (441), `linter/checks_semantic.py` (435), and
`executor_async.py` (435). Split only where a natural seam exists before the
next feature edit forces an emergency refactor.

## Value Statement

Feature work touching these modules never stalls on an emergency refactor;
each split lands as a reviewed, mechanical, behavior-preserving change.

## Problem

Codebase standard: modules < 400 lines, max 450 (Commandment 8: split before
bloat). These modules are not yet over the hard ceiling, but they are one
ordinary feature edit away from it. Relevant active work may touch
`graph_schema.py` (FR-673) and `state_builder.py` if a replacement cleanup for
FR-668 is filed. Splitting proactively avoids mixing mechanical movement into
behavioral FRs.

## Proposed Solution

Mechanical extractions along existing seams — no behavior change, no new
abstractions:

| Module | Lines | Extraction |
|--------|-------|------------|
| `node_compiler.py` | 447 | Extract dispatch registry / per-type handlers only if needed before feature edits |
| `models/state_builder.py` | 442 | `generate_typeddict_code` + helpers → `models/codegen.py` |
| `models/graph_schema.py` | 441 | Guard/verification configs → `models/guard_schema.py` if FR-673 needs room |
| `linter/checks_semantic.py` | 435 | Cycle checks (`check_unguarded_cycles`, `check_skip_if_exists_in_cycle`) → `linter/checks_cycles.py` |
| `executor_async.py` | 435 | Split only if a natural async streaming seam presents |

One commit per module split (`refactor(scope): FR-674 split X`), each
re-exporting moved names from the original module's namespace only where an
external import exists (check `examples/` and `tests/` first; prefer fixing
importers over re-exports — no shims, Commandment 8).

Sequencing: optional before FR-673 if the schema work would push
`graph_schema.py` over the ceiling. FR-672 is rejected (duplication claim was
false). FR-668 is rejected as written, so no sequencing dependency remains
there unless a replacement cleanup FR is filed.

## Acceptance Criteria

- [ ] Each touched near-ceiling module ends under 400 lines
- [ ] Do not split untouched modules solely to satisfy this FR
- [ ] No behavior change: full test suite green with zero test edits other
      than import paths
- [ ] `lint-imports` contracts still KEPT
- [ ] One commit per module split
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

- **Wait until a feature breaches the ceiling** — rejected for modules already
   needed by active FRs: it forces the split into an unrelated feature branch,
   mixing concerns.
- **Raise the ceiling** — rejected: the limit exists to force cohesion; the
  seams above are natural, not contrived.

## Related

- docs/2026-07-03-review-fable.md (Refactoring: module-size band)
- FR-668, FR-672, FR-673 (sequencing)

## Judgement

**APPROVED AS LOW-PRIORITY PROACTIVE REFACTORING.** Current line counts are:

| Module | Review claim | Actual | Status |
|--------|-----------|--------|--------|
| node_compiler.py | 447 | 447 | Under ceiling, closest to limit |
| state_builder.py | 442 | 442 | Under ceiling |
| graph_schema.py | 441 | 441 | Under ceiling |
| checks_semantic.py | 435 | 435 | Under ceiling |
| executor_async.py | 435 | 435 | Accurate |

No module currently exceeds the 450 hard ceiling. The original Fable review's
"435-450 band" framing was correct; the later correction claiming active
ceiling violations was wrong.

**Amendments:**
1. Keep priority LOW. This is useful headroom work, not a blocking defect.
2. Split only modules touched by imminent feature work or with especially
   obvious seams; avoid broad churn.
3. FR-673 may justify splitting `graph_schema.py` first, but the split must
   remain behavior-preserving and separate from schema enforcement.
4. FR-672 is rejected, so `executor_async.py` will not shrink from retry
   extraction. If it is split later, identify a real async/streaming seam.
5. One commit per module remains the right enforcement rule.
