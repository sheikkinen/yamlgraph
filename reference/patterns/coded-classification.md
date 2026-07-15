# Coded-Classification Pattern

Classify free text against a **controlled vocabulary** (a coded
taxonomy with official definitions) using one bounded LLM judgement per
cluster and a deterministic reducer that treats every model output as a
claim to be reconciled against a source of truth.

> **Evidence base: PROVEN (two instances).** Extracted from the
> field-hardened ICPC-2 RFE classifier
> ([examples/icpc-2-rfe](../../examples/icpc-2-rfe/README.md),
> FR-722→730, ~90 field runs, every law below paid for by a measured
> failure) and confirmed by the CWE vulnerability classifier
> ([examples/cwe-classifier](../../examples/cwe-classifier/README.md),
> FR-733) — a copy-adapt of ~4 modules that went RED→GREEN in one
> session with zero new law needed. See
> [What the second instance forced](#what-the-second-instance-forced-cwe-divergences)
> for where CWE stretched the laws without breaking them.

## When to use

All three prerequisites must hold:

1. **Definitional catalog** — an authoritative source per code
   (title + inclusion/exclusion terms), versioned and parseable.
2. **Clusterable facet** — a natural grouping (chapter × component,
   category × family) yielding ≤ ~100 clusters for the map fan-out.
3. **Extractive evidence** — the justification is quotable from the
   input text (evidence spans), not pure judgement.

Fits: ICD/SNOMED-subset coding, HS/customs tariffs, ESCO/ISCO
occupations, NACE/UNSPSC, CWE/CAPEC, support-ticket and moderation
taxonomies, chart-of-accounts assignment.

## The pipeline

```
input text ──► catalog loader (python) ──► map: one LLM judgement per cluster
                                       ──► deterministic reducer (all rules in code)
                                       ──► classification + coverage meta
                                       ──► LLM-free crosscheck harness (labeled fixtures)
```

No new framework primitives: `python` tool + `map` node + `python`
reducer. The only LLM judgement is per-cluster relevance; everything
else is code.

## The six laws

Each law below was adopted only after its prompt-level alternative
failed in the field (see the Scripture's `two_strike_split`).

### 1. Catalog is a generated artifact, never committed

Ship a builder (pinned URL + sha256, refuses unverified input) that
parses the official source locally; the user downloads under their own
license acceptance. Provenance becomes mechanical: rows derived from
the source are `verified`; hand-added rows are `provisional` and
excluded by default. Licensed-vocabulary redistribution risk: zero.

### 2. Cluster fan-out with closed candidate lists

Each map item sees ONE cluster's code list (rendered by code into the
prompt) and may only return candidates from it. The reducer rejects
inventions and repairs mechanical drift (dropped sigils) against
catalog membership.

### 3. The claim-reconciliation boundary

Every model output is a claim reconciled in the reducer:

- **Evidence spans** → aligned to the input text: exact hit returns the
  verbatim substring; near-miss (≥ similarity floor) is repaired to the
  true text; below floor is a fabrication and fails the run. Observed
  span-failure shapes: case-folds, editing-by-omission, one-character
  inflection drift, quote-wrapping, dropped code sigils — and
  **interior omission** (FR-734): claims eliding enumeration markers,
  list segments, or inflecting tense, with 100% of their characters
  present in ≤2 contiguous source blocks. Repair multi-block: matching
  blocks with character coverage ≥ floor inside ONE plausible window
  (capped at ~2× claim length — the load-bearing guard against
  stitching scattered fragments); the output is the true contiguous
  window restoring the elided text verbatim, so repair strengthens
  evidence rather than tolerating drift.
- **Codes** → catalog membership.
- **Verdicts** → caps and domain rules (laws 4–5).

LLM token fidelity is unfixable by prompt; copying belongs to code.

### 4. Cap the junk drawers (`junk_drawer_cap`)

Every taxonomy has "true-of-everything" members — codes describing the
ENCOUNTER or the SYSTEM rather than the subject's stated reason
(Other/NEC, clarification-of-demand, system-problem codes). They eat
correct answers with perfect agreement. They are detectable a priori
(empty or meta inclusion terms) — but verify each cap candidate against
its raw definition first: half of one proposed list turned out
genuinely stateable. Cap in code: demote-never-drop, evidence preserved
in the informational tier, capped entries ranked behind genuine claims.

**Model-prior corollary (FR-734):** for famous vocabularies the model
imports its own junk drawers — it volunteers the very Discouraged
Classes the curators demoted, codes that appear in NO cluster brief
(CWE-119 four times in one 33-run baseline). The cap must therefore
cover out-of-population citations, not just catalog members: claims of
real catalog rows outside the candidate population divert to a meta
audit record (never classification slots, never fatal); only
nonexistent codes stay fatal. An a-priori cap-candidates list doubles
as a prediction of what the model will volunteer off-list.

### 5. Mechanize the standard's own coding rules

Serious coding standards ship practical rules ("use the symptom code
while diagnostic uncertainty remains"). These mechanize into a few
lines of language-independent code (component from code ranges,
same-chapter demotion) and beat any heuristic about model behavior.
Encode the standard's rules, not guesses about the model.

### 6. The measurement spine

- Labeled fixtures beside the code: transcript + rank-tolerant label
  (`primary_any_of` where truth is genuinely tied), rationale
  mandatory, coverage-validity declared.
- Every run archived (`<fixture>-<timestamp>.result.json`); an LLM-free
  harness evaluates archives and reports raw k-of-n agreement — never
  significance at small n.
- Acceptance gates are scoped to the defect class under repair;
  aggregates are recorded as context (`threshold_encodes_forecast`).
- **Agreement is not accuracy**: a biased classifier agrees with
  itself perfectly. Read raw outputs before trusting any score.
- Translated fixtures make language invariance a free regression
  property — and expose cross-lingual hazards (a German compound noun
  lexically primed the wrong chapter's cluster).

## What does not transfer

- Judgement-only classification (no quotable evidence) loses law 3's
  strongest guard.
- Facets that cannot cluster under the map fan-out cap.
- Catalog licensing is per-vocabulary legwork.
- Confidence values remain uncalibrated everywhere: within-rank
  tie-break only, never a threshold.

## What the second instance forced (CWE divergences)

Each divergence stretched a law without contradicting it:

- **Multi-membership clusters** (law 2): a CWE belongs to several
  view-699 categories. The builder duplicates the code into every
  member cluster; the reducer's existing per-code dedup keeps the
  best-ranked occurrence — no new mechanism.
- **Catalog-derived caps** (law 4): MITRE ships the junk-drawer
  taxonomy as Tier-1 data (`Mapping_Notes/Usage`). Prohibited codes are
  stripped from candidacy at BUILD time (never shown to the model);
  Discouraged demotes-not-drops; Allowed-with-Review flags
  `review: true` without demotion — in an analyst-assistance posture,
  review is an outcome, not a penalty. Project curation shrinks to
  zero, but the counts get pinned two-level (catalog-wide AND
  in-population) so a vocabulary bump that shifts the curation is loud.
- **Abstraction chains** (law 5): the standard's own rule ("map to the
  lowest abstraction") mechanizes via `ChildOf` links — a match whose
  matched transitive descendant exists demotes. Verified nearly vacuous
  in-population (384 Base / 9 Variant / 6 Class) — measure the rule's
  live surface before billing it as a centerpiece.
- **Gold labels that violate the vocabulary's own guidance** (law 6):
  2 of 11 NVD gold labels are MITRE-Discouraged codes. The harness
  partitions disagreements mechanically by usage: a miss on an Allowed
  gold code fails (`our_miss`); a miss on a Discouraged gold code is
  recorded (`label_questionable`); a fixture whose entire gold set
  violates guidance is `gold_unscoreable` — reported for the human
  read, never a mechanical pass/fail. Proposing a more specific
  Allowed code than a Discouraged gold label is a success narrative.
- **Committable fixtures**: US-government CVE descriptions are
  redistributable verbatim — the fixture-labeling economics of law 6
  collapse to near zero when the domain has a public gold corpus.

## Reference implementations

[examples/icpc-2-rfe](../../examples/icpc-2-rfe/README.md) — builder,
prompt, reducer (~300 lines total), harness, labeled fixtures in three
languages, and [PLAN.md](../../examples/icpc-2-rfe/PLAN.md) recording
the measured evidence for every law above.

[examples/cwe-classifier](../../examples/cwe-classifier/README.md) —
the second instance (FR-733): view-699 fan-out over cwec_v4.20,
usage-partitioned NVD-gold harness. What a shared library WOULD need
(recorded, deliberately not built — rule of two satisfied, extraction
is now a judgeable FR): `_align_span`, candidate validation with
sigil/prefix repair, verdict-rank sorting with capped-last, per-code
dedup, k-of-n agreement, and timestamp-anchored archive attribution;
domain rules (caps, abstraction/chapter demotions, composition) stay
per-instance. **The copies have now diverged** (FR-734): the CWE
`_align_span` gained multi-block interior-omission repair with local
re-anchoring; the ICPC copy is still single-block. First concrete
extraction motivation on record.
