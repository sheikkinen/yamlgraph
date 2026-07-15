# Feature Request: FR-733 CWE Vulnerability Classifier (Coded-Classification Second Instance)

**Priority:** MEDIUM
**Type:** Feature (new example: `examples/cwe-classifier/`)
**Status:** Proposed
**Effort:** 2-3 days (phased; phase 1 independently committable)
**Requested:** 2026-07-15
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
