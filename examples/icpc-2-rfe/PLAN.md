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

## Phase 3 — Labeled crosscheck harness (FR-725, Proposed)

Measurement before mitigation: committed labeled fixtures
(transcript + expected codes with rank tolerance), a regression runner
over the per-run archive (`logs/icpc2-rfe/*.result.json`), and an
agreement report across N repeat runs. No behavior change to the
classifier itself. Gate: phase 4 may not merge without phase-3 numbers
proving the baseline it improves.

## Phase 4 — Verdict stability (FR-726, Proposed)

Per-cluster self-consistency voting (N samples, majority verdict,
median confidence) or equivalent — mechanism to be judged AFTER the
FR-725 harness quantifies baseline variance and the cost/benefit of
N× calls. Explicitly out of scope until phase 3 lands.

## Deliberately not planned

ICD/SNOMED mapping, diagnosis coding, calibrated confidences,
multi-language prompt optimization (Finnish already works via the
alignment layer), embedding retrieval. Any of these needs a fresh
problem statement, not a phase number.
