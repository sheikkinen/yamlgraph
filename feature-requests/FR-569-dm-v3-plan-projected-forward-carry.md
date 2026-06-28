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
  **authoritative**. The close's proposed delta for these lanes is **overridden** by
  the plan's projection — the prose delta is informational, not load-bearing.
- **Prose-covered lanes** (location, inventory, relationships): the close's proposed
  delta is **validated** for safety (protected-character death is rejected) but
  otherwise accepted.
- **Merged state** = plan projection (for covered lanes) + validated prose delta
  (for uncovered lanes).

**Recovery strategy (load-bearing).** When the prose contradicts the plan (e.g., the
LLM kills a protected character), the close does **not** reject the chapter or retry.
Instead, it **overrides** the plan-covered lanes with the plan's projection and logs
the contradiction as a diagnostic. The prose text is accepted as-is (the Final Cut
already ran); only the derived state is corrected. This is option (b): accept the
chapter but override the delta. Rationale: the plan's projection is the source of
truth for lifecycle/belief/affect, and the prose is the source of truth for the
reader experience — they can momentarily disagree, and the state wins.

### 2. Protected set enforcement

The plan's `goals` predicates define a protected set — characters and predicates that
must hold at the finale. `protected_set(plan)` (project.py:101) already exists and
returns goal fluents' subject characters. It currently reaches the realize seam
(`beat_instruction` in `invoke_turn`) via FR-564. This FR extends the protected set
to additional consumers:
- The director (turn-level steering) — **new**
- The final cut (chapter-level review) — **new**
- The chapter close (commit-level validation) — **new**

A prose death of a character in the protected set is **overridden** at close time
(plan projection wins) and logged as a diagnostic.

### 3. `apply_chapter_close` amendment

The existing `apply_chapter_close` is amended to overlay the plan's projected state
onto the close's physical delta:
- Lifecycle: plan projection wins
- Belief: plan projection wins
- Affect: plan projection wins
- Location/inventory/relationships: prose delta wins (plan has no typed lane)

### 4. Integration

`close_chapter` checks for an attached plan. If present, calls `validate_close`
before committing the delta. Two mechanisms apply:
- **Plan-covered lanes** (lifecycle, belief, affect): contradictions are **overridden**
  by the plan's projection and logged as diagnostics. The chapter is not rejected.
- **Prose-covered lanes** (location, inventory, relationships): a protected-character
  death is **rejected** (the close refuses to commit a death the plan needs alive).

The strangler-fig posture: without a plan, the existing prose-derived close runs
unchanged.

## Acceptance Criteria

1. **Plan contradiction overridden.** A chapter close whose prose-derived delta asserts
   `Fluent(pred="alive", args=("Arnulf",), value=False)` when the plan's projection
   has `Fluent(pred="alive", args=("Arnulf",), value=True)` at that chapter is
   overridden: the committed state uses the plan's projection, and the contradiction
   is logged as a diagnostic.
2. **Protected-character death caught.** A prose-covered-lane death of a character in
   the protected set (needed for a later plan function) is rejected before commit.
   Plan-covered-lane deaths are overridden by the plan's projection (AC1).
3. **Plan projection authoritative.** The forward-carry for lifecycle/belief/affect
   comes from `project_chapter_state`, not prose parsing.
4. **Prose delta accepted for uncovered lanes.** Location, inventory, and relationship
   deltas pass through to the ledger unchanged.
5. **Merged state correct.** The committed state after close = plan projection (covered)
   + validated prose delta (uncovered).
6. **Strangler-fig.** Without a plan, `close_chapter` runs byte-for-byte unchanged.
7. **Regression.** All existing close and plot tests pass unchanged.

**Test exemptions (FR-474 J3):** example tests are requirement-exempt — no
`@pytest.mark.req`, no capability YAML. Diary reflection required for the feat PR
(diary-gate).

## Dependencies

- **FR-567 (Phase 2):** `project_chapter_state` — the projection function (hard
  dependency).
- **FR-566 (Phase 1):** complete grammar — the projection is only guaranteed
  consistent if all 7 rules are enforced (soft dependency — FR-569 can ship on the
  current 4-check validator with the understanding that unchecked rules may allow
  inconsistent projections).

**Note:** FR-568 (plan-derived outline) is **not** a dependency. The close validates
the chapter's *result* against the plan's *projection*, regardless of how the chapter
was outlined. A chapter outlined by the old `outline_chapters` path but closed with
`validate_close` still catches plan contradictions. FR-568 and FR-569 can ship
independently.

## Out of Scope

- Physical lane projection (expanding `at`/`holds` usage for location/inventory) —
  stays prose-derived. Full parallel-safety requires this but it is a future phase.
- Plan re-authoring mid-book — the plan is immutable once attached.
- Concurrent chapter generation — this FR enables it for lifecycle/belief/affect but
  the prose-derived physical lane still serializes. Full concurrency is a future phase.

## Risks

- **Prose/plan divergence visibility.** When the plan overrides a prose-derived delta,
  the prose text may describe events that the committed state doesn't reflect (e.g.,
  prose says "Arnulf fell" but the state says `alive(Arnulf) = true`). The diagnostic
  log makes this visible but a reader of the prose alone sees the contradiction.
  Mitigated by the Final Cut (which already constrains prose against confirmed-dead
  characters via FR-510/511) and by the director's protected-set awareness (which
  steers the LLM away from killing protected characters in the first place).
- **Partial coverage.** The plan covers lifecycle/belief/affect but not
  location/inventory/relationships. The merged state has two provenance sources, which
  adds complexity to debugging.
