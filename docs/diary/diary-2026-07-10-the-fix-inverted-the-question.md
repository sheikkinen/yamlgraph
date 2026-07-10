# The Fix Inverted the Question It Came From (FR-712)

**Date:** 2026-07-10
**Context:** FR-712 enforce — uncaching loop-affine google clients; the correctness fix that rewrote FR-711's latency arithmetic.

## What happened

The fix was one frozenset. The instructive part came from the judged
interplay criterion (re-run the FR-711 instrument post-fix):

1. First re-run: google Arm B STILL errored 10/20 — because the witness
   itself was reusing one pre-created client across loops, the exact
   topology the fix had just retired. The instrument was now measuring a
   world production no longer inhabits. Instruments rot the moment the
   system under measurement changes; a witness must state WHICH topology
   it exercises and be re-derived when that topology moves.
2. Production-faithful re-run (create_llm per call): google clean, and its
   fresh-loop delta collapsed to **+0.067 s** — while azure sits at
   **+0.628 s**. The fleet arithmetic that motivated the whole pooling
   question inverted: the reconnect burden is the azure candidate's, not
   gemini's. The correctness fix didn't just close a bug; it changed which
   provider the latency FR should be about.

## The chain, for the record

FR-711 (measure latency) → found correctness bug (FR-712) → fixing it
required updating FR-711's own instrument → which produced better latency
data → which redirects FR-711's eventual condemn target. Investigation and
fix FRs form a loop, not a line — each enforce should re-run its parent's
instrument, and the judged "interplay" criterion is what forced that here.

## Heuristic

When a fix changes call topology, every witness that encodes the OLD
topology silently becomes a historical reenactment. After such a fix,
grep for instruments touching the changed seam and re-derive them before
trusting any of their numbers again. (Corollary of pattern-freeze: a
frozen measurement procedure has a freshness contract with the code it
measures.)

**Seed:** instruments could declare their topology assumptions as
executable preconditions (e.g. assert google not in _llm_cache after two
create_llm calls) so a topology change FAILS the instrument loudly instead
of letting it measure a retired world.
