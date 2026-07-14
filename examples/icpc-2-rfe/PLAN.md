# ICPC-2 RFE Classifier — Phase-In Plan

Status ledger for the ICPC-2 example. Each phase is a separate FR with
its own judgement; scope frozen per phase, later phases must not leak
into earlier ones (FR-722 purge list).

## Phase 1 — Symptom/disease RFE (FR-722, **Completed** 2026-07-14)

Components 1 (symptoms/complaints) and 7 (diseases): 686 rubrics,
33 chapter×component clusters. Shipped: sha256-pinned catalog builder
(ClaML, catalog generated locally — Wonca data never committed),
cluster map fan-out, deterministic reducer, evidence-span alignment in
code, `classify.sh` runner with per-run archive.

Field-proven limits (all documented in the FR):
- **HP-36 finding**: a prescription-renewal call has no honest C1/C7
  answer — its canonical RFE is a *process code*. Result is
  `low_confidence` + K86 top partial, with the gap declared in
  `meta.catalog_coverage`. This is phase 2's motivating fixture.
- **Verdict variance**: per-cluster "match" verdicts vary run-to-run;
  the reducer is deterministic *given* candidates. Phases 3–4 address
  measurement and mitigation, in that order.
- LLM token-fidelity (span quoting) and verdict semantics both required
  code/prompt discipline — see diary 2026-07-14 (two-strike rule).

## Phase 2 — Process codes (FR-724, **Completed** 2026-07-14)

Components 2–6 (the 40 shared `-30…-69` process rubrics: medication
renewal, exams, results, administrative, referrals) are RFE candidates
— 5 `PROC-C<n>` clusters, fan-out 38. Process-over-chapter primacy and
reducer-derived `chapter_context` are explicit witnessed rules.
HP-36 acceptance met: primary `-50 Medication/prescription/renewal`,
not low_confidence. Which chapter candidate becomes context still
varies run-to-run — phase 3's measurement target.

## Phase 3 — Labeled crosscheck harness (FR-725, **Completed** 2026-07-14)

Six labeled fixtures + LLM-free evaluation over the run archive; raw
k-of-n agreement. **First baseline (N=5): 11 pass / 19 fail — the
harness caught a phase-2 regression within the hour it landed**: meta-
process rubrics (`-48`, `-69`) + process primacy flip symptom
transcripts to process primaries with perfect agreement (bias, not
variance). See FR-727.

## Phase 3b — Process discipline & combined codes (FR-727, **Completed** 2026-07-14)

Meta-process cap `{-43,-46,-48,-69}` (demote-not-drop, capped entries
rank behind genuine partials) + mechanical `combined_code` composition
(K86 + `-50` → K50; chapter A contextless). Definitive baseline
**22/30 (from 11/30)**; zero residual failures involve capped codes.
The 8 residuals quantify the deferred defect: chapter-code inflation
(A13/Z10/P76 secondary leaks, wrong composed chapter letter Z50-vs-K50)
and model variance on ambiguous fixtures — the next FR's opening
evidence.

## Phase 3c — Chapter-inflation discipline (FR-730, **Completed** 2026-07-14)

Z10 cap (the Z-side `-48`; A13/A23/A29 verified stateable, uncapped),
same-chapter symptom-over-diagnosis (ICPC practical rule 3 mechanized:
P03 demotes P76), composition context eligibility non-Z with C7-over-C1
preference. All three gating classes at zero (Z10 leaks, P76-class,
Z-composition); hp36 composes K50, never Z50. Accepted A13 residual
measured at its upper bound (4/29) — hp36 label is the permanent
detector.

## Phase 4 — Verdict stability (FR-726, gated — likely CONDEMNED)

Baseline shows agreement ≈90%+ with the failures being bias, which
voting amplifies rather than fixes. Mechanism judgement deferred until
FR-727 lands and a fresh baseline isolates residual variance.

## Deliberately not planned

ICD/SNOMED mapping, diagnosis coding, calibrated confidences,
multi-language prompt optimization (Finnish already works via the
alignment layer), embedding retrieval. Any of these needs a fresh
problem statement, not a phase number.
