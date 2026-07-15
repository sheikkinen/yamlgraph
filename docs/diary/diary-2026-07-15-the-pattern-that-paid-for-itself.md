# The pattern that paid for itself on the second use

**Date:** 2026-07-15
**Context:** FR-733 — the CWE vulnerability classifier, second instance
of `reference/patterns/coded-classification.md`, enforced RED→GREEN in
one session.

## What happened

The ICPC arc (FR-722→730) took eight FRs and ~90 field runs to harden:
five span-failure shapes, three verdict-inflation families, two cap
taxonomies, one composition rule — each paid for by a measured failure.
The CWE instance inherited all of it by copy-adapt and went from judged
FR to green suite plus a working end-to-end run in a single session.
The first smoke run's primary matched NVD gold. The first baseline run
rejected a fabricated span ("crafted Content-Length HTTP header" —
editing-by-omission, collapsing a three-item list into one) that the
naked eye would have accepted as a plausible quote. The boundary built
for Finnish medical transcripts caught an English CVE fabrication
unchanged.

## The trap I nearly walked into

`quick_confidence` wearing measurement clothes: the judgement pinned
"83 Prohibited catalog-wide" and I nearly encoded it. Recomputing
against the actual source scoped to what the builder actually does
(skip Deprecated) gave 58 — the 83 counted the 25 deprecated rows. The
pin would have failed on first build, but the LESSON is cheaper: every
count pin must be computed by the same filter chain that produces the
pinned population. A number verified against the wrong denominator is
a forecast, not a fact (`threshold_encodes_forecast`'s little sibling).

Second field deviation, same shape: "40 clusters" was true of
categories but not of briefs — CAT-1225 (Documentation Issues) is 100%
Prohibited and vanishes at build time. 39 briefed clusters. The
build-time strip, designed for candidacy honesty, silently performed
cluster-level curation too. Correct behavior, unforecast consequence —
found only because the builder prints what it did.

## Session-mechanics traps (recorded, both survived)

- A guard-denied command took its heredoc with it: the retry committed
  with the PREVIOUS message still in tmp/msg.txt. Cure: verify the
  subject line in the same breath as the commit rc, every time.
- A terminal-reuse race dropped an amend into a foreign nested repo
  (csap-black-box-tests); it failed only because tmp/msg.txt didn't
  exist there. `one_session_one_repo` extends to terminals: prefix
  destructive git commands with an explicit cd.

## Heuristic

**A pattern is proven not when the second instance works, but when the
second instance's failures are all NEW.** Every failure the CWE
instance produced (miscounted pin, vanishing cluster, gold labels that
violate the vocabulary's own guidance) was a domain fact, not a
mechanism regression. The mechanisms — span boundary, caps,
dedup, k-of-n — absorbed the domain change without edits beyond
renaming. That is what "extract a shared library" should mean: the six
things that survived contact unchanged (recorded in the pattern doc),
not the twenty things that exist.

## The baseline read (added after the 33-run measurement)

9 pass / 3 fail / 3 unscoreable, and 19 of 33 runs killed at the
boundary. The dominant kill was something ICPC structurally could not
show: the model volunteers famous MITRE-**Discouraged** Classes
(CWE-119 four times, -200, -20, -664) that appear in NO cluster brief.
For an obscure vocabulary (ICPC) the closed cluster list is the
model's only source of codes; for a famous vocabulary the model brings
its own — and what it brings is precisely the overused junk drawers
the vocabulary's curators demoted. **The junk_drawer_cap phenomenon
arrives through model weights, not just catalog membership.** The
closed-list pin kills those runs honestly; whether an off-catalog
claim of a real-but-demoted code should drop-with-record instead of
killing 39 clusters' work is strike-one material for a follow-up FR,
not an enforce-time improvisation — the pin is judged.

Second reading: Shellshock failed 3/3 with agreement 2/3 on CWE-454
(External Initialization of Trusted Variables) against gold CWE-78 (OS
Command Injection). The description literally states env-variable
processing; NVD coded the exploit consequence. Mechanically our_miss
(CWE-78 is Allowed, in-population); substantively a label-vs-
description tension — the A13-style named residual, kept failing,
permanently detectable. And gold_unscoreable earned its keep on first
contact: Drupalgeddon2 3/3 proposing CWE-94 where NVD's gold is the
Discouraged CWE-20.

## The judgement that overturned its own proposal (FR-734 addendum)

I wrote FR-734 from the baseline read, confident in the split: "13
off-population kills dominate, 6 span kills working as designed." The
judge's first act — recounting per-file from the logs — proved both
halves false: 8 catalog / 11 span, and the span kills were not
fabrications but **repairable interior omissions** (every killed claim
had 100% of its characters in the description, in exactly two
contiguous blocks; the single-block window anchor just mis-placed the
comparison). The proposal had filed the DOMINANT defect class under
"working as designed" — the strongest possible form of
`quick_confidence`: a wrong number I had already published in a
completed FR's table.

Two heuristics, both graduation candidates:

- **A completion table is a measurement artifact** — recompute from
  the source before freezing, never from conversation memory. The 13/6
  split was a mis-recalled uniq -c sum.
- **"Working as designed" is a claim about the DEFECT, not the
  mechanism.** The boundary raising was designed behavior; the claims
  it raised on were not fabrications. Before filing rejections under
  by-design, read what was rejected with the same care as what was
  accepted — the boundary's kills deserve the read_raw_output_first
  treatment too.

## Red Hat, end of day: is the example adding value?

Asked directly, answered honestly. As a classifier it is not
competitive (n=3 scoring, ~40 LLM calls per description) and as a
framework demo it is redundant (same graph shape as icpc-2-rfe, zero
new primitives). Its value was as a MEASUREMENT INSTRUMENT for the
pattern, and that value is already banked: the PROVEN promotion, three
findings ICPC structurally could not produce (model-prior junk
drawers, interior-omission/decoy span shapes, guidance-violating
gold), and the first evidence-motivated extraction case. By
`constraint_over_code`, deleting the example tomorrow would lose
almost nothing — the treasure lives in the pattern doc and the
boundary code. The operative heuristic: **an example built to prove a
pattern is spent the moment the pattern is proven; its future
marginal value is near zero unless it serves the extraction.** The
`growth_as_default` temptation now is a third instance; the justified
next step is subtractive or consolidating (shared-library FR with
both instances as test bed) — or nothing.

## Seed

The harness now partitions disagreements by the vocabulary's own
meta-curation (`Mapping_Notes/Usage`) — the gold label can be wrong by
the standard's own rules. ICPC has no machine-readable equivalent, but
its process-code junk drawers were the same phenomenon discovered
manually. **Can a builder detect junk-drawer candidates a priori across
vocabularies — empty inclusion terms, meta-language in definitions,
degree-centrality outliers in the hierarchy — and emit a
`cap_candidates` list for the judge, turning law 4's curation from
per-instance archaeology into a mechanical pre-read?** And its new
twin: for famous vocabularies, the same list predicts what the MODEL
will volunteer off-list — one artifact, two guards.
