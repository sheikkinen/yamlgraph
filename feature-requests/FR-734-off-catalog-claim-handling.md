# Feature Request: FR-734 Off-Catalog Claim Handling — Full-Catalog Reconciliation

**Priority:** MEDIUM
**Type:** Fix/refinement (examples/cwe-classifier, reducer semantics)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-07-15
**Parent:** FR-733 (baseline finding; recorded there as strike-one
follow-up material)
**Evidence:** logs/fr733-baseline.json + logs/cwe-classifier/*.log —
19 of 33 baseline runs killed at the reducer boundary, 13 of them by a
single failure class

## Problem

The FR-733 baseline exposed a failure class ICPC structurally could
not show: **the model volunteers famous MITRE-Discouraged Classes from
prior knowledge** (CWE-119 four times, CWE-200, CWE-20, CWE-664 — plus
CWE-122, Allowed but outside view-699). None appear in any cluster
brief; the closed-list check (`candidate code not in catalog`) raises,
killing the entire 39-cluster run for one volunteered code.

Structural, permanent, dominant: for an obscure vocabulary (ICPC) the
cluster brief is the model's only source of codes; for a famous
vocabulary the model brings its own — and what it brings is precisely
the overused junk drawers MITRE demoted. 13/33 runs (39%) died this
way, discarding 38 good clusters' work each time and starving the
measurement spine (agreement columns at n=1, n=2).

## Key fact the current reducer ignores

Every volunteered code is a **real row in the generated catalog** (the
builder emits all 944; the loader ships only the 345 clustered rows to
state). The rejection is not "this code does not exist" but "this code
is not in the candidate population" — a distinction the reducer cannot
currently see.

## Proposed Solution

Reconcile candidate codes against the FULL catalog, not the cluster
union, with three tiers (unifying with law 4's demote-never-drop):

1. **In-population code** — current behavior unchanged (verdict caps,
   review flag, abstraction guard).
2. **Real catalog row without view-699 membership** (incl. Prohibited
   and off-view Discouraged) — demote to `partial_match`, `capped:
   true`, plus a new `off_population: true` marker; NEVER
   primary/secondary; recorded in `meta.off_population_claims` so the
   audit trail names what the model volunteered. This extends the
   judgement's own F3 Discouraged semantics (demote-not-drop) to the
   codes the model imports from its weights.
3. **Nonexistent code** (after CWE-prefix repair) — still raises.
   Fabrication remains fatal.

Mechanism: the loader already carries the full payload; add an
`off_population` lookup (code → usage) to each cluster dict or a
separate state key, so the reducer stays a pure function of state.

## Tension with the judged FR-733 pins (why this needs a judge)

- AC-02 pinned "Prohibited codes never candidates" — tier 2 keeps them
  out of primary/secondary/best-partial-as-genuine but makes them
  VISIBLE as capped, recorded claims. Judge must rule whether
  visibility-with-cap satisfies or violates the pin's intent
  (junk_drawer_cap says demote-never-drop; the current behavior is
  neither — it is total loss).
- The icpc precedent ("anything else is an invention and raises")
  stays true for tier 3; the FR claims tier 2 is not invention but
  out-of-population citation.

## Acceptance Criteria

- [ ] AC-01 Witness: a CWE-119 match claim from any cluster yields a
      capped, off-population partial; run completes; meta records it.
- [ ] AC-02 Witness: a nonexistent code (e.g. CWE-99999) still raises.
- [ ] AC-03 Prohibited codes remain unreachable as primary/secondary
      (pin preserved under the new semantics).
- [ ] AC-04 Re-run the 3×11 baseline; run mortality from this class
      drops to zero; disagreements re-read; FR documents before/after
      (gate on the defect class, not the aggregate —
      threshold_encodes_forecast).
- [ ] AC-05 Pattern doc: law 4 gains the "model-prior junk drawer"
      finding (famous vocabularies import their own junk drawers
      through the model's weights; the cap list must cover
      out-of-population citations, not just catalog members).

## Out of scope

- Span-alignment changes (working as designed; editing-by-omission
  stays fatal).
- The Shellshock CWE-78 named residual.
- ICPC reducer changes (no evidence of the phenomenon there — obscure
  vocabulary; record only).
- A-priori cap_candidates builder (diary Seed; separate proposal).
