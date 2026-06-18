# The Pack the Cap Could Not Play

**FR-525 — DM v2 outliner split-gate**

## What happened

FR-523 fed committed `world_state` back into a just-in-time re-outline so the
state-blind planner could author the bridging beat a planned death required. That
closed the *discontinuity* loop. This bug is its sibling, one layer earlier: the
whole-book partitioner sometimes packs a death AND its reversing return into ONE
chapter — Arnulf is swept away, presumed drowned, AND reappears alive, all inside
chapter 3 of the Floodmark book. The play loop closes a chapter at
`CHAPTER_TURN_CAP` turns (FR-501); 16 turns can portray the loss or the return, but
not both with the reversal earned in between. So `close_chapter` commits the removal
half, the return beat becomes a promise no chapter will keep, and the
`beat_coverage_gap` witness fires on the committed artifact.

The fix normalizes at the partitioner boundary: after each outline,
`reversal_pack_gap` checks every authored chapter; on a pack the outline is
re-invoked with the violation named (bounded retry), then RAISES if it persists.

## The trap

**`plausible_wrong_answer` in the witness itself.** My first `reversal_pack_gap`
flagged any proper name present in a paragraph that contained BOTH a removal token
and a return token. The five fixture tests passed — and the witness was wrong. Run
on the real 10024-BC corpus it over-fired: chapter 2 was a pure false positive
("drowned out" as idiom + "stay alive"), and chapter 3 reported Hilde, Gunnar, and
Aschenwulf alongside Arnulf when only Arnulf is actually packed. Co-occurrence in a
paragraph is not attribution. The fixtures, authored to the same flawed mental model
as the code, could never expose it — only the real corpus could.

## The insight

A continuity witness must attribute a token to a grammatical subject, not to a
paragraph. `_subjects_near(text, tokens, window=40)` assigns each removal/return
token to the NEAREST proper name in the 40 characters BEFORE it: "Arnulf is swept"
→ Arnulf, but "presumed dead by the Aschenwulf" → nothing, because Aschenwulf
*follows* the token. With subject-proximity attribution the witness fires on
10024-BC chapter 3 = [Arnulf] alone and stays clean across all sixteen older books —
the same precision signature as `beat_coverage_gap`, its committed-artifact dual.

The structural read: **fixtures prove the shape you imagined; the corpus proves the
shape that exists.** A witness destined to gate real output must be corroborated
against real output before it is trusted, because a detector and its fixtures share
an author and therefore share blind spots.

## The method that paid off

Condemn before fix (RED witness + 5 fixtures, `b42ff067`), then GREEN the
`outline_chapters` retry loop with a stateful stub: a packed first roll re-rolled to
a clean split, plus a non-vacuous negative control (a removal-only outline passes
untouched, no spurious re-invoke) so the assertion cannot pass on plumbing alone,
plus an exhaustion test proving the gate RAISES rather than silently emitting a pack
(Commandment 6). The witness was hardened against the corpus *before* it became
load-bearing — the cheapest place to catch a false positive is before it gates.

**Seed:** The outliner gate (prevention) and `beat_coverage_gap` (detection at the
committed artifact) are duals reading the same reversal from opposite ends of the
pipeline. When two witnesses share a definition but read different boundaries, should
the definition live in one place they both import — and would a drift between them
itself be a defect worth a gate?
