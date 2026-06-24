# Roadmap: FR-573 → FR-580 Plot Modeller pipeline (conditional on FR-572 GO)

**Status:** Judged — ACCEPTED as a roadmap (not as 8 grants); conditional on FR-572 GO (2026-06-23)
**Date:** 2026-06-23

These FRs are stubs. Each will be written as a full spec (following the FR-570
pattern: plan → judge → enforce) when its predecessor completes. Writing full
specs now would be speculative planning beyond evidence (R1 from the review).

**Two rules every stub inherits when promoted to a full spec:**

- **Order is schedulable, not forced (J:N1).** The numbered chain below is a
  *risk-control* sequence (one spike-and-measure at a time), not a data
  dependency. The real data-coupling is looser: L3 reads the synopsis (not L2's
  goals), and L5/L6/L7 each read glosses+kinds (not each other). If a gate KILLs
  mid-chain, the independent layers can be re-planned without re-deriving the
  whole sequence. Each stub's spec must state which predecessor it needs for
  *data* versus merely for *scheduling*.
- **Thresholds trigger; analysis decides (J:N2).** The per-layer gates below
  (90% recall, 80% beat match, 70% predicate match, …) are provisional starting
  points, not derived constants. Each spec must inherit FR-570's J3 rule
  explicitly: a bare miss-by-one against a *coherent, fixable* error cluster is
  a REVISE, not a KILL. A gate that mechanically pass/fails on the number alone
  risks killing a salvageable layer.

---

## FR-573 — L1 extract agents spike

**Phase:** 2a
**Depends on:** FR-572 GO
**Scope:** Graph + prompt + validator for extracting agents, initial world
state, and initial beliefs from a synopsis. Spike against 5 synopses.
**Gate:** ≥ 90% agent recall.

## FR-574 — L2 extract goals spike

**Phase:** 2b
**Depends on:** FR-573
**Scope:** Graph + prompt + validator for extracting goals from a synopsis +
extracted agents. Spike against 5 synopses with ground-truth agents.
**Gate:** Goals match ground truth structurally (predicate + args correct).

## FR-575 — L3 extract glosses spike

**Phase:** 2c (the hard one)
**Depends on:** FR-574
**Scope:** Graph + prompt + validator for decomposing a synopsis into ~7–12
beat glosses. Spike against 5 synopses. This is the creative pivot — the model
decides where beats begin and end.
**Gate:** ≥ 80% of ground-truth beats have a corresponding gloss (fuzzy match).
**Risk:** Medium. Beat decomposition is subjective. Two humans may disagree on
where one beat ends and another begins. The evaluation metric must account for
this — exact match is too strict; semantic overlap is the right measure.

## FR-576 — L5 assign pre/eff spike

**Phase:** 3a
**Depends on:** FR-575
**Scope:** Graph + prompt + validator for assigning world-state and belief
preconditions/effects to classified beats. Spike against 5 synopses with
ground-truth glosses + kinds.
**Gate:** ≥ 70% of predicates match ground truth.
**Risk:** Medium-high. The model must invent predicates, not just classify.
This is the first formalization layer that requires creative generation within
a constrained vocabulary (5 predicates × open args).

## FR-577 — L6 assign causality spike

**Phase:** 3b
**Depends on:** FR-576
**Scope:** Graph + prompt + validator for assigning `enables`, `motivation`,
and `threatens` links between beats. Spike against 5 synopses.
**Gate:** ≥ 75% of `enables` links match ground truth.

## FR-578 — L7 assign affects spike

**Phase:** 3c
**Depends on:** FR-577
**Scope:** Graph + prompt + validator for assigning affect open/close operations
(6 kinds + relational `toward`). Spike against 5 synopses.
**Gate:** ≥ 70% accuracy on affect operations.

## FR-579 — Merge node + orchestrator + full pipeline

**Phase:** 4
**Depends on:** FR-578
**Scope:** Deterministic merge node (join per-layer state keys by function id),
orchestrator graph (L1 → L2 → L3 → L4 → L5 → L6 → L7 → merge), bounded
backtrack, `report_failure` node, full structural validation (causality SAT,
goal reachability, Rule 8 motivated action).
**Gate:** Full pipeline produces a valid plan for ≥ 4 of 5 synopses. All
produced plans pass `validate_plan()`. At least one has partial-order structure.

## FR-580 — Plan contract + documentation

**Phase:** 5
**Depends on:** FR-579
**Scope:** Formalise the plan file as a versioned contract. YAML schema spec,
machine-readable schema, `PlotPlan.to_yaml()` / `PlotPlan.from_yaml()`,
full README update.
**Gate:** A consumer can read a pipeline-produced plan using only the documented
contract. Schema round-trips: `from_yaml(to_yaml(plan)) == plan`.

---

## Dependency chain

```
FR-570 (L4 spike)        ← DONE (0.80, GO optimistic)
    │
FR-571 (schema)           ← ready to implement
    │
FR-572 (vocab + blind)    ← KILL gate
    │
FR-573 (L1 agents)
    │
FR-574 (L2 goals)
    │
FR-575 (L3 glosses)       ← hardest extraction layer
    │
FR-576 (L5 pre/eff)       ← hardest formalization layer
    │
FR-577 (L6 causality)
    │
FR-578 (L7 affects)
    │
FR-579 (merge + pipeline)
    │
FR-580 (contract + docs)
```

Each FR is written as a full spec only when its predecessor completes and
passes its gate. This roadmap is a guide, not a commitment.

---

## Judgement (2026-06-23)

**Verdict: ACCEPTED as a roadmap.** Holding eight specs as stubs until each
predecessor passes its gate is exactly right — it answers the review's R1
(planning depth must not outrun evidence depth). No authority is granted to
implement FR-573+ here; that comes per-FR, post-FR-572-GO. Two notes to carry
forward when each stub is promoted to a full spec.

### N1 — the numbered chain overstates the real data-coupling

The chain is drawn strictly sequential (FR-573 → … → FR-580), but the *data*
dependencies are looser than the *FR* dependencies:

- L3 (glosses) reads the **synopsis**, not L2's goals — FR-575 does not truly
  need FR-574's output.
- L5/L6/L7 each read **glosses + kinds**, not each other — FR-576/577/578 are
  mutually independent given L3+L4.

[architecture.md](../examples/plot_modeller/docs/architecture.md) already says
Phase 1 and Phase 2 can parallelize. Serializing the FRs is a legitimate
**risk-control** choice (one spike-and-measure at a time), not a data
requirement — say so in each stub, so a future implementer knows the order is
schedulable, not forced. This matters if a gate KILLs mid-chain: the
independent layers can be re-planned without re-deriving the whole sequence.

### N2 — the intermediate gate thresholds are provisional; carry FR-570's caveat

The gates (90% recall, 80% beat match, 70% predicate match, 75% enables, 70%
affect) are asserted, not derived. They are reasonable starting points, but each
stub-promoted-to-spec must inherit FR-570's J3 rule explicitly: **the threshold
is a trigger; the confusion/error analysis carries the verdict.** A bare 0.68
that misses by one coherent, fixable cluster is a REVISE, not a KILL. Without
this caveat each gate risks becoming a mechanical pass/fail that kills a
salvageable layer (review's `audit_as_ritual` / `gate_checks_shape_not_substance`).

Neither note blocks the roadmap. Both are conditions on the *future* per-layer
specs, recorded here so they are not rediscovered seven FRs from now.
