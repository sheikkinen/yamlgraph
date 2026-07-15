# Feature Request: FR-733 CWE Vulnerability Classifier (Coded-Classification Second Instance)

**Priority:** MEDIUM
**Type:** Feature (new example: `examples/cwe-classifier/`)
**Status:** Completed (enforced 2026-07-15)
**Effort:** 2-3 days (phased; phase 1 independently committable)
**Requested:** 2026-07-15
**Judged:** 2026-07-15 — scope frozen; two load-bearing numbers overturned by candidate-population verification
**Pattern:** `reference/patterns/coded-classification.md` — this FR is the
**second instance** whose completion promotes the pattern from
provenance to proven (and reopens the rule-of-two extraction question)
**Evidence:** catalog exploration 2026-07-15 (this conversation; key
numbers verified against cwec_v4.20.xml, 18 MB, in tmp/)

## Purpose (demo + research, like icpc-2-rfe)

Classify a free-text vulnerability description (CVE submission, bug
report, pentest finding, scanner output) into CWE weakness code(s) with
quoted evidence spans and reasoning. Real-world seat: analyst
assistance for CVE→CWE assignment (NVD enrichment backlog is a known
industry pain; assignments are manual and inconsistent). The classifier
proposes with an audit trail; humans dispose.

## Why CWE is the right second instance (verified 2026-07-15)

| Pattern prerequisite | CWE fit |
|---|---|
| Definitional catalog | cwec_v4.20.xml: 969 weaknesses (25 deprecated → 944 live) with Description, Extended_Description, Alternate_Terms, Observed_Examples (CVE-referenced). Free under MITRE terms with attribution — **committable**, unlike Wonca |
| Clusterable facet | View-699 (Software Development): **40 categories, median 9 / max 60 members** — same shape as ICPC's 38 clusters |
| Extractive evidence | CVE/bug descriptions quote the flaw; spans checkable |

Two properties upgrade the pattern's laws:

1. **Law 4 becomes catalog-derived**: `Mapping_Notes/Usage` ships the cap
   as Tier-1 data — Allowed 749 / Allowed-with-Review 93 /
   **Discouraged 44 / Prohibited 83**. No project curation needed
   (dissolves the FR-730-F2 tension). Prohibited → excluded from
   candidacy; Discouraged → verdict-capped (demote-not-drop);
   Allowed-with-Review → demote-to-partial unless evidence is explicit
   (exact semantics judged at freeze).
2. **Law 5's rule is official and machine-readable**: "map to the lowest
   abstraction" + `Related_Weakness ChildOf` chains → prefer
   Base/Variant over Class/Pillar when both match, ~10 lines, the
   structural analog of ICPC rule 3.

And the measurement-spine economics flip: **NVD assigns CWE labels to
every enriched CVE** — thousands of gold-labeled fixtures for the
crosscheck harness at near-zero labeling cost (vs 6+2 hand-authored for
ICPC).

## Proposed Solution (phase ladder, mirrors PLAN.md of icpc-2-rfe)

**Phase 1 — catalog + contracts + fixtures:**
- `nodes/build_catalog.py`: **versioned** URL pin
  (`cwec_v4.20.xml.zip`) + sha256 — `cwec_latest` is a moving pointer
  and violates the refusal contract; parse Weakness rows (skip
  Deprecated), derive `cluster_id` from View-699 category membership
  (multi-membership allowed; reducer dedup already handles it), carry
  `abstraction`, `mapping_usage`, ChildOf parents. Emit
  `data/cwe_catalog.yaml`.
- Labeled fixtures: ~10 NVD-labeled CVE descriptions across common
  classes (XSS, SQLi, path traversal, buffer overflow, ambiguous
  short-description case) — labels are NVD's assignments,
  rank-tolerant where NVD itself maps to a Class.
- Cluster briefs Description-only (~24 codes/cluster avg is denser than
  ICPC; brief budget matters).

**Phase 2 — graph + prompts + reducer:**
- Same architecture: catalog loader → 40-cluster map fan-out →
  deterministic reducer. Reuse the icpc reducer discipline (span
  alignment, membership repair, caps, dedup, low-confidence path) —
  **copy-adapt, do not yet extract a shared library** (that decision
  belongs to the post-completion pattern promotion, rule of two).
- CWE-specific reducer rules: mapping_usage caps (catalog-driven);
  lowest-abstraction preference via ChildOf (a Base match demotes its
  matched ancestors, not vice versa).

**Phase 3 — harness + baseline:**
- Crosscheck harness (copy-adapt from icpc): NVD-labeled fixtures,
  k-of-n agreement, archived runs, provenance quarantine.
- Baseline vs NVD assignments documented in the FR; disagreements READ
  (read_raw_output_first) before any threshold is proposed — NVD labels
  are analyst opinions, not ground truth; a disagreement may indict the
  label.

## Acceptance Criteria

- [ ] AC-01 Builder: versioned pin + sha256 refusal; 944 live rows; the
      Prohibited/Discouraged/Review counts from Mapping_Notes are
      asserted (83/44/93 at v4.20) so a future catalog bump that shifts
      MITRE's curation is loud, not silent.
- [ ] AC-02 Reducer: Prohibited codes never candidates; Discouraged
      match claims demoted with evidence preserved; lowest-abstraction
      rule witnessed both directions (Base beats matched Class parent;
      lone Class match survives).
- [ ] AC-03 Evidence honesty: spans verbatim from the input description
      (the icpc span-alignment boundary, same floor).
- [ ] AC-04 Fixtures: ≥10 NVD-labeled CVEs; every label carries the CVE
      id + NVD's CWE as rationale; baseline k-of-n vs NVD documented
      with each disagreement read and classified (our miss vs
      label-questionable).
- [ ] AC-05 Short-description honesty: "buffer overflow" alone yields
      low_confidence, never a forced Base code.
- [ ] AC-06 Pattern doc promotion: on completion,
      reference/patterns/coded-classification.md header flips to proven
      (two instances), with a divergence section listing what CWE
      forced that ICPC didn't (multi-membership, catalog-derived caps,
      abstraction chains).
- [ ] AC-07 REQ(s) under a new CAP; fragment (feat, FR-733 in title);
      diary; README with purpose header (demo + research, not a
      security-decision tool).

## Constraints

1. All six pattern laws apply; deviations are judged, not improvised.
2. No shared-library extraction in this FR (purge: premature
   abstraction) — copy-adapt and record what a library WOULD need.
3. Analyst-assistance posture in all docs: proposes with audit trail,
   never autonomous assignment.

## Risks

- Cluster-brief token budget at ~24 codes/cluster (mitigate:
  Description-only briefs; judge may split the two largest categories).
- NVD label quality: treat disagreement as data (AC-04), not error.
- View-699 doesn't cover all 944 weaknesses (some only in Research
  view) — coverage meta must declare the actual candidate population,
  exactly like ICPC's components field.

## Judgement (2026-07-15)

**Verdict: APPROVED — with 5 findings; the proposal's candidate
population and its centerpiece rule were both re-measured.** The
versioned URL verified live (200 OK). All numbers below computed
against cwec_v4.20.xml scoped to the ACTUAL candidate set, which the
proposal never did.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **Candidate population is 399, not 944.** View-699 categories contain 399 live weaknesses (42% of catalog); the proposal's "944 live rows" conflated catalog rows with candidacy | Builder emits all 944 rows (catalog completeness) but clusters only the 399 view-699 members; coverage meta declares `view: 699, candidates: 345, excluded_prohibited: 54, catalog_total: 944` — a no-match is interpretable |
| F2 | **The lowest-abstraction rule is nearly vacuous in-population**: inside view-699 the abstraction mix is 384 Base / 9 Variant / 6 Class, with only 22 fully-inside ChildOf pairs. The "ICPC rule 3 analog" billing overstated it | Rule KEPT (cheap, correct, witnessed both directions per AC-02) but demoted from centerpiece to secondary guard. The primary CWE-specific discipline is F3 |
| F3 | **Prohibited codes sit INSIDE the candidate clusters**: 54 of 399 view-699 members (13.5%) are Mapping_Notes Prohibited; Discouraged 5, Allowed-with-Review 13 in-population | Exclusion/cap semantics pinned: Prohibited → removed from cluster briefs at BUILD time (never shown to the model); Discouraged → candidacy allowed, match demoted to partial (FR-727 mechanism); Allowed-with-Review → match allowed, flagged `review: true` in output (analyst-assistance posture makes review a first-class outcome, not a demotion) |
| F4 | **Brief-budget risk withdrawn**: 399 candidates / 40 clusters ≈ 10 median — LIGHTER than ICPC's briefs, not denser; the proposal's ~24/cluster arithmetic divided the wrong numerator | Description-only briefs stay (simplicity, not budget); the category-split contingency is purged |
| F5 | AC-01's count pins were catalog-wide only | Pins now two-level: catalog-wide 83/44/93 AND in-population 54/5/13 — a catalog bump shifting either level is loud |

Additional pins:
- Multi-membership: builder duplicates the code into each member
  cluster's list; reducer's per-code dedup (existing mechanism) keeps
  the best-ranked occurrence.
- Fixtures: CVE descriptions are US-government work (NVD public data)
  — committable verbatim with CVE id + NVD's CWE as the label
  rationale; no paraphrase needed (unlike Wonca).
- REQ ids allocated at enforce, verified free against origin; new CAP
  file for the example.
- The pattern-doc promotion (AC-06) happens in this FR's completion
  commit, not a separate FR.

**Out of scope (purge list):** shared-library extraction (recorded-not-
built), CAPEC/ATT&CK cross-mapping, hardware CWE view (1194),
source-code (diff) input mode — text descriptions only in phase 1,
autonomous assignment posture anywhere, category-split contingency
(F4), two-stage triage architectures.

## Judgement Addendum (2026-07-15): fixtures gathered, label audit done

Eleven NVD-labeled CVE fixtures fetched from the live API and committed
under `examples/cwe-classifier/data/labeled/` (raw description +
provenance-stamped gold label; the harness's `expected_*` schema is
defined at enforce):

| CVE | NVD label | Class exercised |
|---|---|---|
| CVE-2024-49038 | CWE-79 | XSS (also a CWE Observed_Example — doubly gold) |
| CVE-2014-6271 (Shellshock) | CWE-78 | OS command injection |
| CVE-2019-19781 (Citrix) | CWE-22 | path traversal, terse description |
| CVE-2014-0160 (Heartbleed) | CWE-125 | OOB read |
| CVE-2023-4863 (libwebp) | CWE-787 | OOB write |
| CVE-2021-3156 (Baron Samedit) | CWE-193 | off-by-one — specificity test vs 787 |
| CVE-2022-22965 (Spring4Shell) | CWE-94 | code injection, Review-flagged label |
| CVE-2021-44228 (Log4Shell) | CWE-20 + CWE-917 | **multi-label** fixture |
| CVE-2019-11043 (PHP-FPM) | CWE-120 + CWE-787 | multi-label, overlapping codes |
| CVE-2018-7600 (Drupalgeddon2) | CWE-20 | **label = Discouraged code** |
| CVE-2017-5638 (Struts) | CWE-755 | **label = Discouraged code** |

**Label-vs-guidance audit finding (pre-enforce gold):** two of eleven
NVD gold labels (CWE-20, CWE-755) are codes MITRE itself marks
Mapping-Discouraged, and CWE-20 also rides Log4Shell's multi-label.
This settles AC-04's disagreement protocol IN ADVANCE: the harness must
score against `nvd_cwes` while separately reporting when the gold label
itself violates MITRE guidance — "our classifier proposes a more
specific Allowed code than NVD's Discouraged label" is a SUCCESS
narrative, not a miss. Labels must therefore carry an
`nvd_label_usage` field (computed by the builder from Mapping_Notes)
so the harness can partition disagreements mechanically. The fixture
set also bakes in: multi-label (2), Allowed-with-Review labels (4),
one terse near-underdetermined description (Citrix), and a
specificity-pair (193 vs 787).

## Enforcement (2026-07-15) — Completed

RED f34a07d3 (22 witnesses, CAP-204 / REQ-YG-557..560), GREEN a70921df.
All 22 pass; full unit sweep green; graph lints; smoke run on
cve-2024-49038 returned primary CWE-79 = NVD gold on first attempt.

**Deviations from the judgement (all evidence-forced, none silent):**

1. **Catalog-wide Prohibited pin is 58, not 83** — the judgement's 83
   counted the 25 Deprecated rows the builder skips. Every count pin
   must be computed by the same filter chain that produces the pinned
   population. In-population 54/5/13 confirmed exactly.
2. **39 briefed clusters, not 40** — CAT-1225 (Documentation Issues) is
   100% Prohibited and vanishes at build time: the candidacy strip
   silently performs cluster-level curation. Correct, unforecast.
3. **`nvd_label_usage` lives in the harness report, not the committed
   label files** — usage is computed from the generated catalog at
   evaluation time; committed fixtures stay raw provenance (a builder
   writing into committed files would blur the generated/committed
   boundary of law 1).

**AC-04 baseline (3 runs × 11 fixtures, azure gpt-4o, 2026-07-15;
logs/fr733-baseline.json):** TOTAL 9 pass / 3 fail / 3 unscoreable;
19 of 33 runs died at the reducer boundary (a failed run is data).
Every disagreement read and classified:

| Class | Evidence | Reading |
|---|---|---|
| Off-population volunteering (13 run-kills) | CWE-119 ×4, CWE-200, CWE-20, CWE-664 (all MITRE-**Discouraged** non-members), CWE-122 (Allowed, not in view-699) | NEW domain fact ICPC could not show: the model KNOWS CWE by heart and volunteers exactly the famous junk-drawer Classes MITRE demoted — the junk_drawer_cap phenomenon arriving via model prior instead of catalog membership. The closed-list pin (AC-02, judged) kills the whole 39-cluster run for one volunteered code — heavy but honest; softening reject→drop-with-record is a SEMANTICS change to a judged pin → follow-up FR, not an enforce-time improvisation |
| Span fabrications (6 run-kills) | ellipsis editing ("From version 2.16.0 ... this functionalit"), enumeration-marker omission ("(1) TLS and (2) DTLS" → "TLS and DTLS"), paraphrase ("to run on" → "running on"), and one candidate quoting the CWE **catalog brief** as evidence ("does not neutralize or incorrectly neutral…") | All four are known icpc shapes or their close kin; the brief-as-evidence shape is new and correctly rejected — the boundary built for Finnish transcripts caught English CVE fabrications unchanged |
| our_miss: CWE-78 (Shellshock, 3/3 fail, agreement 2/3 on CWE-454) | Description states env-variable processing ("processes trailing strings after function definitions in the values of environment variables"); NVD coded the exploit consequence (OS command injection). CWE-454 (External Initialization of Trusted Variables) is the literal reading | The named residual (icpc's A13 analog): mechanically our_miss because CWE-78 is Allowed and in-population; substantively a label-vs-description tension. Kept failing, permanently detectable |
| gold_unscoreable: cve-2018-7600 (3/3) | Gold CWE-20 is Discouraged; our primaries CWE-94/CWE-439 | The success narrative working as designed: we propose specific Allowed codes where NVD's label violates MITRE's own guidance |
| label_questionable: CWE-20 (Log4Shell) | CWE-20 has NO view-699 membership — it can never surface | Partition handles it mechanically; the Allowed gold CWE-917 is what the classifier is scored on |

Passing fixtures: cve-2019-19781 3/3 on CWE-22 (the terse Citrix
description resolved, no forced low-confidence needed),
cve-2024-49038 3/3 on CWE-79, cve-2021-3156 2/2 on CWE-193 (the
specificity pair held: 193 chosen over 787), cve-2023-4863 1/1 on
CWE-787.

**Recorded for a follow-up FR (not built):** off-catalog candidate
handling — drop-with-record (meta lists rejected claims) vs run-kill.
Strike one at the mechanism level; the two-strike rule wants a second
occurrence or a judge's decision before the pin changes.

AC checklist: AC-01 ✓ (pins two-level, corrected), AC-02 ✓, AC-03 ✓,
AC-04 ✓ (this section), AC-05 ✓ (witnessed via Discouraged-only match
→ low_confidence; terse Citrix fixture resolved rather than forced),
AC-06 ✓ (pattern doc promoted to PROVEN with divergence section),
AC-07 ✓ (CAP-204, fragment, diary, README with purpose header).
