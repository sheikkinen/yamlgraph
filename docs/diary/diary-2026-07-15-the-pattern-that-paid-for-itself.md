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

## Seed

The harness now partitions disagreements by the vocabulary's own
meta-curation (`Mapping_Notes/Usage`) — the gold label can be wrong by
the standard's own rules. ICPC has no machine-readable equivalent, but
its process-code junk drawers were the same phenomenon discovered
manually. **Can a builder detect junk-drawer candidates a priori across
vocabularies — empty inclusion terms, meta-language in definitions,
degree-centrality outliers in the hierarchy — and emit a
`cap_candidates` list for the judge, turning law 4's curation from
per-instance archaeology into a mechanical pre-read?**
