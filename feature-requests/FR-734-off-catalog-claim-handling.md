# Feature Request: FR-734 Boundary Run-Mortality — Off-Catalog Claims + Interior-Omission Spans

**Priority:** MEDIUM
**Type:** Fix/refinement (examples/cwe-classifier, reducer semantics)
**Status:** Completed (enforced 2026-07-15)
**Effort:** 1 day (two independent witnesses, one shared re-baseline)
**Requested:** 2026-07-15
**Judged:** 2026-07-15 — evidence recounted; the proposal's dominant-killer
attribution was wrong and a second, larger defect class surfaced during
verification
**Parent:** FR-733 (baseline finding; recorded there as strike-one
follow-up material)
**Evidence:** logs/fr733-baseline.json + logs/cwe-classifier/*.log —
19 of 33 baseline runs killed at the reducer boundary

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

- [ ] AC-01 Witness: a CWE-119 match claim from any cluster is diverted
      to `meta.off_population_claims` (code, usage, cluster, verdict,
      confidence, best-effort spans); the run completes; classification
      slots (primary/secondary/best_partial) contain ONLY population
      members.
- [ ] AC-02 Witness: a nonexistent code (e.g. CWE-99999) still raises.
- [ ] AC-03 Prohibited codes remain unreachable in every classification
      slot (FR-733 pin preserved verbatim — meta is audit, not output).
- [ ] AC-04 Witness (two-block repair): "TLS and DTLS implementations"
      repairs against "(1) TLS and (2) DTLS implementations"; the
      Log4Shell ellipsis claim (67/70 chars in 2 blocks) repairs to the
      true contiguous window; a genuine fabrication (scattered blocks /
      coverage below floor) still raises — both directions witnessed.
- [ ] AC-05 Re-run the 3×11 baseline; run mortality from BOTH classes
      drops to zero (gate on the defect classes, not the aggregate —
      threshold_encodes_forecast); disagreements re-read; before/after
      documented here; FR-733's completion table numbers corrected with
      a dated note.
- [ ] AC-06 Pattern doc: law 4 gains the model-prior junk-drawer
      finding; law 3's span-shape list gains interior-omission-repair
      (with the two-block coverage mechanism and its floor).
- [ ] AC-07 icpc parity decision RECORDED (not implemented): the same
      `_align_span` copy lives in examples/icpc-2-rfe/nodes/reduce.py;
      divergence of the copies is accepted for this FR and noted as
      shared-library-manifest evidence in the pattern doc.

## Out of scope

- The Shellshock CWE-78 named residual.
- ICPC reducer changes (AC-07 records the divergence; no icpc edits).
- A-priori cap_candidates builder (diary Seed; separate proposal).
- Any new tolerance for LOW-coverage span claims: the floor moves from
  window-similarity to block-coverage, it does not drop.

## Judgement (2026-07-15)

**Verdict: APPROVED — with the proposal's central factual claim
overturned and scope EXPANDED by what the verification found.** Every
number below recomputed from logs/cwe-classifier/*.log, per-file
(first error = the killer), not from memory.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **The dominant-killer attribution was FALSE.** The proposal (and FR-733's completion table) claimed 13 off-population / 6 span kills. Recount: **8 catalog kills / 11 span kills** — span mortality DOMINATES. The 13/6 split was written from recollection of a uniq -c output, never re-summed | FR-733's table gets a dated correction (AC-05). Meta-lesson diary-bound: a completion table is a measurement artifact — recompute from the source before freezing, never from conversation memory |
| F2 | **The span kills are NOT fabrications.** All four killed shapes verified: 100% of claimed characters present in the description in exactly TWO contiguous blocks (37/37, 28/28, 34/34; Log4Shell 67/70). The model omits interior enumeration markers ("(1)…(2)"), list segments ("Content-Type, Content-Disposition, or"), or inflects tense ("to run on"→"running on"). `_align_span`'s single-block window anchor mis-places the comparison window and the 0.85 similarity check fails claims whose true contiguous window exists | This is a REPAIR-COVERAGE DEFECT in the boundary, not a new tolerance request — in scope (AC-04). Mechanism pinned: multi-block alignment via `get_matching_blocks`; accept when matched-character coverage ≥ 0.85 of the claim AND all blocks fall inside one plausible window (span_len + slack); output is the true contiguous description window covering the outermost blocks. Below coverage floor or scattered blocks → still raises. icpc's known-fatal "editing-by-omission" verdict is REFINED, not repealed: what dies is fabrication, not elision of interior noise — the output window restores the elided text verbatim, so evidence honesty is strengthened, never weakened |
| F3 | **Tier-2 semantics decided: meta-only, never classification slots.** The proposal offered capped-partial visibility in best_partial; that relitigates FR-733's AC-02 pin for no analyst benefit (a Discouraged/Prohibited code shown as best_partial invites exactly the mapping MITRE forbids) | Off-population claims (real catalog row, no view-699 membership) divert to `meta.off_population_claims` with best-effort span alignment (never fatal for meta-tier claims; unalignable spans recorded raw with `span_unverified: true`). Classification slots remain population-only — the FR-733 pin is preserved VERBATIM, no reinterpretation needed. Demote-not-drop is satisfied by the audit record |
| F4 | **Mechanism for full-catalog visibility pinned**: the loader returns a merged dict `{cwe_clusters: [...], usage_index: {code: usage}}` (dict returns merge into state — the reduce node precedent); reducer stays a pure function of state; no graph-topology change, no 39× duplication | Graph gains the `usage_index` state key; builder unchanged (all 944 rows already emitted) |
| F5 | Effort re-estimated 0.5 → 1 day (two defect classes, two witness sets, one shared re-baseline). AC-05's gate covers both classes; span kills were previously misfiled as "working as designed" in FR-733's completion table — the correction note covers that line too | — |

**Purge list:** capped-partial visibility for off-population claims
(F3), any similarity-floor reduction, dynamic/learned floors, icpc
backport (AC-07 records only), retry-the-cluster strategies.

## Enforcement (2026-07-15) — Completed

RED 3f54443a (7 condemning + 3 regression-guard witnesses,
REQ-YG-561), GREEN 68acbbca, decoy-anchor fix 8f9dc1c2 (found by the
first re-baseline read — see below). All 33 witnesses green; full
sweep green.

**Mortality ladder (3×11 runs each, azure gpt-4o, archives
quarantined by provenance between passes):**

| Pass | Kills | Reading |
|---|---|---|
| FR-733 baseline | 19/33 | 8 catalog + 11 span (judgement F1 recount) |
| Pass 1 (GREEN) | 4/33 | 3 × the SAME Tomcat shape pinned to repair + 1 new. Raw read: global `get_matching_blocks` anchored the claim's 'running' prefix to a decoy occurrence 137 chars away ('running on JDK 9+'), blowing the window cap — greedy global matching fails when a short prefix has a decoy; fixed by a second LOCAL re-anchoring pass around the longest match (8f9dc1c2) |
| Gate (logs/fr734-baseline2.json) | **1/33 — ZERO from both gated classes** | The survivor: 'possible for remote code execution' vs 'vulnerable to remote code execution' — a REORDERED PARAPHRASE, correctly fatal: rewording is fabrication, not elision. New named span shape, recorded in the pattern doc |

**AC-05 gate satisfied.** Off-population kills 8 → 0: the audit trail
now holds exactly what used to kill — 8 of 32 archived runs carry
`meta.off_population_claims` (CWE-119 ×4, CWE-200 ×3, CWE-122,
CWE-20), every one a formerly-fatal volunteered code, every one with
usage attached. Span kills 11 → 1 (the paraphrase, by design).

**Scoring effects (18 pass / 8 fail / 6 unscoreable, up from 9/3/3
on 3× more surviving runs):** Spring4Shell 0→3/3 pass (the repaired
Tomcat span now flows into a CWE-94 = NVD gold primary); Heartbleed
3/3 on CWE-125 = gold. Substantive disagreements now measurable with
full n: Shellshock CWE-78 named residual stands (agreement 2/3 on
CWE-454); Log4Shell misses gold CWE-917, model prefers CWE-470
(JNDI-as-code-selection — a defensible literal reading, 2/3); PHP-FPM
surfaces CWE-787 but not gold CWE-120 (multi-label partial);
Drupalgeddon2/Struts gold_unscoreable working as designed (our CWE-94
vs Discouraged golds). All residuals are LABEL/JUDGEMENT tensions, not
boundary mortality — the instrument now measures the classifier, not
its own kill rate.

AC checklist: AC-01–03 ✓ (witnessed), AC-04 ✓ (both directions +
decoy witness), AC-05 ✓ (this section; FR-733 table corrected in
68acbbca), AC-06 ✓ (pattern doc law 3 + law 4 model-prior corollary),
AC-07 ✓ (icpc divergence recorded in the pattern doc's shared-library
manifest — `_align_span` copies have now diverged: cwe has
multi-block + local re-anchor, icpc has single-block; the manifest
names this the first concrete extraction motivation).
