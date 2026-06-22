# Feature Request: FR-569 DM v3 — plan-projected forward-carry

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed (2026-06-22)
**Effort:** 3–4 days
**Requested:** 2026-06-22
**Plan:** [`plan-v3-planner.md`](../examples/dungeon_master/docs/plan-v3-planner.md) Phase 4

## Summary

The chapter close validates its proposed delta against the plan's projection instead
of re-deriving load-bearing state from prose. The plan owns lifecycle, belief, and
affect; the close owns physical detail. Two chapters that share no causal link in the
plan can generate concurrently.

## Value Statement

DM maintainers get a chapter close that **validates** against the plan rather than
**reconstructing** from prose. A protected-character prose death is caught before
commit. The lifecycle/belief/affect forward-carry comes from the plan, not prose.
This retires the central architectural gap: two parallel truth sources running
unsynchronized.

## Problem

Today `close_chapter` (in `chapter_ops.py`) re-derives world state from the chapter's
prose at each chapter boundary. The `character_lifecycle` is parsed from prose. The
`world_state` ledger accumulates prose-derived facts. The plan, if attached, is read
for exclusion and beat instruction but never consulted at close time.

This means:
- A prose death of a protected character (needed alive for a later plan function) is
  accepted and committed, breaking the plan's causal chain silently.
- Belief state is prose-derived, not plan-projected — a reveal that the prose forgot
  to narrate means the belief lane diverges from the plan.
- The forward-carry for lifecycle/belief/affect depends on prior prose, serializing
  all chapter generation.

## Proposed Solution

### 1. `validate_close(plan, chapter, proposed_delta) → ValidatedDelta`

A validation function that compares the chapter close's proposed delta against the
plan's projected state:

- **Plan-covered lanes** (lifecycle, belief, affect): the plan's projected state is
  **authoritative**. The close's proposed delta for these lanes is validated against
  the projection — contradictions are rejected.
- **Prose-covered lanes** (location, inventory, relationships): the close's proposed
  delta is **validated** for safety (protected-character death is rejected) but
  otherwise accepted.
- **Merged state** = plan projection (for covered lanes) + validated prose delta
  (for uncovered lanes).

### 2. Protected set enforcement

The plan's `goals` predicates define a protected set — characters and predicates that
must hold at the finale. This protected set is fed to:
- The director (turn-level steering)
- The final cut (chapter-level review)
- The chapter close (commit-level validation)

A prose death of a character in the protected set is **rejected** at close time, not
just logged.

### 3. `apply_chapter_close` amendment

The existing `apply_chapter_close` is amended to overlay the plan's projected state
onto the close's physical delta:
- Lifecycle: plan projection wins
- Belief: plan projection wins
- Affect: plan projection wins
- Location/inventory/relationships: prose delta wins (plan has no typed lane)

### 4. Integration

`close_chapter` checks for an attached plan. If present, calls `validate_close`
before committing the delta. If the delta contradicts the plan, the close is rejected
with a diagnostic. The strangler-fig posture: without a plan, the existing
prose-derived close runs unchanged.

## Acceptance Criteria

1. **Plan contradiction rejected.** A chapter close that asserts `alive(Arnulf) = false`
   when the plan's projection has `alive(Arnulf) = true` at that chapter is rejected
   with a diagnostic.
2. **Protected-character death caught.** A prose death of a character needed for a
   later plan function is rejected before commit.
3. **Plan projection authoritative.** The forward-carry for lifecycle/belief/affect
   comes from `project_chapter_state`, not prose parsing.
4. **Prose delta accepted for uncovered lanes.** Location, inventory, and relationship
   deltas pass through to the ledger unchanged.
5. **Merged state correct.** The committed state after close = plan projection (covered)
   + validated prose delta (uncovered).
6. **Strangler-fig.** Without a plan, `close_chapter` runs byte-for-byte unchanged.
7. **Regression.** All existing close and plot tests pass unchanged.

## Dependencies

- **FR-567 (Phase 2):** `project_chapter_state` — the projection function.
- **FR-568 (Phase 3):** plan-derived outline — ensures chapter structure matches plan.
- **FR-566 (Phase 1):** complete grammar — the projection is only trustworthy if all
  7 rules are enforced.

## Out of Scope

- Physical lane projection (expanding `at`/`holds` usage for location/inventory) —
  stays prose-derived. Full parallel-safety requires this but it is a future phase.
- Plan re-authoring mid-book — the plan is immutable once attached.
- Concurrent chapter generation — this FR enables it for lifecycle/belief/affect but
  the prose-derived physical lane still serializes. Full concurrency is a future phase.

## Risks

- **Prose/plan conflict UX.** When `validate_close` rejects a prose delta, the
  generation must recover — either retry the chapter with a corrected directive, or
  fall back to plan-less close. The recovery strategy needs design.
- **Partial coverage.** The plan covers lifecycle/belief/affect but not
  location/inventory/relationships. The merged state has two provenance sources, which
  adds complexity to debugging.
