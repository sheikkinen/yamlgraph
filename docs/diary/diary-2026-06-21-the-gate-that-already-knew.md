# The Gate That Already Knew

**Date:** 2026-06-21
**FR:** FR-555 — reversal-gate the state-aware re-outline boundary

## What happened

The dominant continuity sink on 10036-BC was Arnulf "presumed dead" in the frozen
Ch3 summary, then narrated "still alive downstream" in a beat of the same chapter —
a removal-and-return reversal the partition gate (`outline_chapters`, FR-525) exists
to refuse. The fix was not a new detector, a new witness, or a new graph. The
detector already existed; it simply was never wired into the *second* authoring
boundary the FR-523 state-aware re-outline introduced. `reoutline_chapter_beats`
re-authored beats from the full synopsis and committed them validating only
`_require_beats` (non-empty). One `for` loop and a candidate-card build closed it.

## The trap: detection_without_enforcement at a *second* boundary

The first boundary was gated; everyone assumed the artifact was therefore safe. But
a *second* function authored the same artifact, and the gate did not travel with the
write. This is the same shape as the Knowledge Graph's `gate_checks_shape_not_substance`
and FR-556's "no typed setter" — a guard bound to *one call site* instead of to the
*artifact*. The cure is `the_one_law`: normalize where the data is born. Here the
contradiction is born at re-outline, so the gate belongs at re-outline, not downstream
in the director or final cut.

## What made it boring (and that was the point)

Judgement reproduced the root cause against the *live* committed cards before any
code: running the existing `reversal_pack_gap` over the fresh 10036-BC story returned
exactly one hit — Ch3, Arnulf. No reproduction step in enforce was needed; the RED
test was the incident transcribed. The enforce diff mirrored `outline_chapters` line
for line (same `_reversal_feedback`, same `_OUTLINE_MAX_ATTEMPTS`, same raise). Boring
enforcement = the Judgement was good.

## The one bug was in the test, not the gate

The RED retry test failed under GREEN because my stub rebuilt its queue on every
`get_app` call — and the gate calls `get_app` once *per attempt*. The production code
was correct; the test's sequencing assumption was not. A reminder that a per-call
factory monkeypatch must return a *shared* instance when the code under test invokes
it in a loop.

## Seed

The partition gate and the re-outline gate now apply the *same* detector at *two*
boundaries by copy. FR-556's typed setter would let a single `write_chapter_card`
funnel bind the whole gate battery *once*, by construction — so no third authoring
boundary can ever be added ungated. **When a detector must be applied at every write,
is the right home the writer, or the artifact's one setter? And how would a test prove
that a *future* writer cannot bypass it?**
