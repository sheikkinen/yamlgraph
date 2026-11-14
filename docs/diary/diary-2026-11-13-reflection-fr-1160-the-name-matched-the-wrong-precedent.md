# Reflection: FR-1158/FR-1159/FR-1160 — the name matched the wrong precedent

**Date:** 2026-11-13
**FR:** FR-1158 (rejected), FR-1159 (merged as PR #771, now rejected), FR-1160 (removal)

## What happened

The operator asked for a "cached map" as a new node, standalone first, because its implementation differs from
the base map. The day before, the same conversation had produced that use case in writing: the FR-1155
follow-up "warm-first map dispatch". A cold parallel map with a `cache: true` prompt segment pays one Anthropic
cache write per concurrent branch (8 writes, 4 reads at W = 8, 0.87× the uncached cost). Sending one item first
and then fanning out gives 1 write and N − 1 reads (0.20× on Haiku). The first consumer was game-engine's
library describe map.

I never read that follow-up. "Cached map" matched the FR-1116 map *memo* by vocabulary — a cross-run, per-item
result store — and every step after that was faithful to the wrong problem. FR-1158 planned a memo node; the
judge rejected it as contrib material; FR-1159 moved the memo into `yamlgraph/contrib` with a demo. The judge,
the outsider and the CI all passed it, because each read the artifact against its own text, and the artifact
was internally consistent. None of them held the operator's intent; only I did, and I had replaced it.

Two things were lost, not one. The use case (prompt-cache cost of a map fan-out) and the requested solution
shape (a standalone node whose dispatch differs from `map`) both disappeared. The judge's rejection of FR-1158
even looked like a correction, which made the drift feel earned.

## Trap

`continuation_bias` with a precise trigger: **a request phrase that matches an existing artifact by name is
resolved to that artifact, skipping the conversation's own recent record.** The nearest written precedent was
one day old and in the same session; the code precedent was older and won because grep finds code, not intent.

## Heuristic

**Before planning from a short request, search the session's own recent FRs and follow-ups for the phrase's
nouns, and restate the use case in one sentence with its numbers.** If the restatement cannot cite where the
use case came from, ask. A gate chain — judge, outsider, CI — validates the artifact against itself; it cannot
recover an intent the author dropped before writing it.

**Seed:** Should the FR template's **First consumer / first event** line require a link to the message or
follow-up section where the operator stated the need, so that an FR whose consumer was inferred rather than
quoted is visible as such at judgement?
