# Diary: The Gate That Guards Shape, Not Provenance

**Date:** 2026-07-03
**FRs:** FR-663 (changelog req legacy cap false positive)
**Session:** FR-660/661 enforcement → acceptance testing → FR-663

## Trap: gate_checks_shape_not_substance (variant)

The `test_no_req_collision_across_unrelated_frs` test checks whether an FR's changelog fragment claims a REQ that the FR "owns" via a capability entry. But `fr: legacy` capabilities have no owning FR — they predate the traceability system. Any FR that enhances a legacy capability (FR-660 → CAP-05, FR-661 → CAP-84) triggers a false positive.

The workaround was to omit `req:` from the changelog fragment, losing the traceability the test was designed to enforce. The gate preserved its shape (no collisions) by destroying its substance (no traceability).

## Insight: Provenance ≠ Ownership

The test conflates two concepts:
- **Provenance**: "Which FR created this capability?" (`fr: FR-247`)
- **Enhancement**: "Which FRs contribute to this capability?" (any FR claiming its REQs)

Legacy capabilities have no provenance (they were born before the registry). But they accept enhancements. The test's ownership model doesn't account for this.

## Heuristic

**When a gate forces you to remove the data it was designed to protect, the gate's model is wrong — not the data.** The cheapest fix (omit `req:`) satisfied the gate but violated its purpose. FR-663 fixes the model.

## Seed

Could `enhances: CAP-XX` become a first-class field in changelog frontmatter? Instead of inferring capability membership from `fr:` in the registry, declare it explicitly. This would make the test trivially correct and add a new traceability dimension: which changes touched which capabilities, regardless of who created them.
