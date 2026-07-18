# The floor you guess is not the floor you measure

**Date:** 2026-07-18
**Context:** FR-748 enforcement — the FR Atlas demo, from RED witnesses
to two verified corpus runs.

## What happened

The deterministic spine (collector, chunker, coverage, render) went
GREEN without incident. Then the first full corpus run failed — and the
next two runs failed differently. Three live strikes at the same
boundary in one afternoon, each a *distinct* token-fidelity class:

1. **Bracket sigils** — the model copied ids WITH the `[brackets]` the
   digest block used as display decoration.
2. **Slug shortening** — `FR-514-dm-v2-delta-close-…` claimed without
   its `dm-v2-` segment.
3. **Slug paraphrase under duplicate heads** — two real FR-424 files
   exist; the claim `FR-424-wip-commit-subject-gate` spliced tokens
   from *both* real titles into a plausible blend that no format check
   could catch.

Each strike got a RED witness and a mechanical repair in
`assemble_candidates` — zero prompt patches. `two_strike_split`
confirmed for the third project running: instruction text never holds
against token fidelity; the model's output is a CLAIM reconciled
against the source of truth at the boundary.

## The trap I actually fell into

I set the similarity floor at 0.6 by feel. The true head-mate scored
0.59. The witness failed and forced me to *measure*: 0.59 vs 0.308 —
a chasm, but on the wrong side of my guessed line. The floor you guess
encodes your forecast; the floor you measure encodes the data. Same
shape as `threshold_encodes_forecast`, one level down: even a
two-line `SequenceMatcher` calibration beats intuition about string
similarity, because ratio scales are not intuitive.

## What the raw read bought (AC-02, read_raw_output_first)

Reading three chunks' raw themes before trusting the taxonomy found
things no aggregate could: a genuine resurrection pair
(`FR-409`/`FR-411-inquisitor-watcher2-reintegration`) correctly fused
into one theme; the run classifying its own FR-748 into a one-member
"Onboarding corpus map" theme (the atlas describing itself); and
per-map-slot house styles — every c8 arc begins "These FRs…" while
c1/c15 are imperative. Stylistic nonstationarity across parallel slots
is a real signature of map fan-out, invisible in any merged output.

## The silent degradation the judgement pre-caught

The ninchat run "worked" first try — and silently omitted that its
module axis had degraded to git paths (no CAP registry). The judgement
had demanded the degradation be *loudly declared*; the run satisfied
every mechanical assert while dropping exactly the provenance a reader
would need. `gate_checks_shape_not_substance`, live: rc=0 is a shape
check. The fix was one header line and two witnesses.

## Heuristic

Calibrate every similarity/threshold constant against the first real
strike-pair before committing it — the measured gap (0.59/0.308) tells
you where the floor belongs; the guessed one only tells you where you
hoped it was.

**Seed:** Three projects have now independently rebuilt id/claim
reconciliation at an LLM boundary (spans FR-722, codes FR-727/730, ids
here). Should `reconcile_claim(claim, population, floor)` graduate
into yamlgraph core — a standard boundary helper every map-over-corpus
pipeline gets for free — and would a shared helper have prevented all
three strikes, or does each boundary's repair grammar (brackets,
prefixes, slug blends) stay irreducibly local?
