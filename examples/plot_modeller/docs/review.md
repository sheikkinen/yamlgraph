# Review: Plot Modeller docs

**Date:** 2026-06-23
**Reviewer:** adversarial read (per the doctrine — review agent output as
untrusted input, regardless of plausibility)
**Scope:** [vision.md](vision.md), [architecture.md](architecture.md),
[plan-implementation-phases.md](plan-implementation-phases.md)

---

## Verdict

A strong, research-grounded design set. The core thesis — *a structured plot
plan is a lossy-but-sufficient compression that lets prose exceed the context
window* — is sound and well cross-checked (Propp, Greimas, Todorov, Bremond,
CPOCL, MEXICA, OCC). The honesty of the status tables ("designed, not built")
is the docs' best feature.

The defects below were found and fixed. This section records the original
findings and their resolutions for traceability.

---

## Concrete defects (all resolved)

### D1 — "16 vs 17" drift inside vision.md — FIXED

The headline alphabet is **17 kinds**, but the lower body originally asserted
**16** in two places.

**Fix applied:** historical references now read "pre-`mediation` 16-kind set";
current vocabulary claims say "17."

### D2 — duplicate heading — FIXED

`### Genre-agnostic by composition` appeared **twice** with contradicting kind
counts (17 vs 16).

**Fix applied:** second instance updated to "17 kinds." Both headings retained
— they serve different contexts (vocabulary rationale vs. what-this-enables).

### D3 — "What was kept (10 direct)" miscounts its own list — FIXED

The list enumerates **12**: villainy, lack, departure, struggle, victory,
liquidation, return, pursuit, rescue, recognition, exposure, punishment. The
arithmetic requires 12:

```
12 kept + 2 merged (donor_test, provision) + 2 added (death, mediation)
        + 1 generalised (reconciliation) = 17
```

**Fix applied:** label reads "12 direct."

### D4 — `hope` affect closers mix two vocabularies — FIXED

`hope`'s closers originally named "betrayal, death, loss" — but `betrayal` and
`loss` are **affect kinds**, not **function kinds**. The open/close model states
affects are opened and closed *by function beats*. There is no `betrayal` beat
in the 17-kind alphabet.

**Fix applied:** closers now read `villainy, death, exposure` — beats that
destroy hope. The "beats open/close affects" invariant is preserved.

### D5 — unverified specific claims — FIXED

- "48 tests, 1361 lines" — now links to the
  [2026-06-23 inventory](../../dungeon_master/docs/inventory-2026-06-23.md).
- "What was dropped (15)" — softened to "The remaining Proppian functions" with
  explicit group names (preparation sequence, false-hero sequence, branding,
  transfiguration).

### D6 — traceability hole — FIXED

The status table originally said "15/16 exercised" without naming the missing
kind. Verification showed **all 16 are exercised** across the 35-gloss corpus
(`exposure` has n=1, the thinnest).

**Fix applied:** status reads "all 16 exercised, `exposure` n=1."

---

## Structural risk (resolved)

### R1 — the KILL gate races the expensive build — FIXED

The original dependency graph permitted Phase 1b (blind-corpus re-test) to run
in parallel with Phase 2 (build L1–L3, ~600 lines). Phase 1b is the project's
KILL gate. Parallelizing the cheapest kill-test against the most expensive build
work defeated the plan's own "spike before build" principle.

**Fix applied:** dependency graph is now strictly sequential:
`Phase 0 → Phase 1 (KILL gate) → Phase 2 → Phase 3 → Phase 4 → Phase 5`.
Guiding principle #5 added: "The kill gate runs before the expensive build."
Conditionality statement added at the top of the phase plan: Phases 2–5 are
conditional on the Phase 1b blind-corpus GO.

### R1 (deeper form) — planning depth has outrun evidence depth — ACKNOWLEDGED

The 5-phase ~2500-line plan rests on one measured number (0.80) on self-derived
data. The conditionality statement now makes this explicit: Phases 2–5 are
speculative plans conditional on the blind test, not committed scope.

---

## Minor / stylistic (resolved)

- **"forward-compatible growth"** in architecture.md — changed to "additive
  schema evolution."
- Cross-links between the three docs are clean and consistent.

---

## Open items (no defects — things to watch)

1. **`mediation` is untested.** Added post-cross-check, no empirical evidence
   yet. Phase 1b (blind-corpus re-test) is the first test. If it causes L4
   confusion with `lack`, consider merging them back.

2. **`hope` is untested.** Added post-cross-check. The 4 existing genre plans
   don't use it yet. Phase 1a (retrofit ground truth) is the first exercise.

3. **Relational `toward` on affects is unexercised.** No existing plan uses it.
   Phase 1a retrofit will be the first test of whether relational affects add
   signal or just noise.

4. **`exposure` has n=1.** The blind synopsis should include an exposure beat
   to improve coverage of this thin kind.
