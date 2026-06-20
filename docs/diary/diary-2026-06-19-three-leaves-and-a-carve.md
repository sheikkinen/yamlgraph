# Three Leaves and a Carve

*FR-540 / FR-541 / FR-542 — 2026-06-19*

## What happened

Enforced three judged FRs in one sitting, each a deterministic boundary defense for
the DM v2 cross-chapter continuity class observed in 10029-BC: entry/exit
composition contracts (FR-540), per-chapter character overlays (FR-541), and the
seam fact-reversal gate (FR-542, shipped as Part A interim + Part B novel). Twelve
new tests, all RED-before-GREEN; 364 DM tests green; every quality gate clean.

## The trap that actually bit

`framework_costume`'s humble cousin: the **module-size ceiling as a forcing
function**. FR-542 Part A added four small helpers to `chapter_ops` and one public
read to `chapter_open` — both already sitting at 449/450. The additive change
pushed each over, and the size gate failed *after* GREEN, not before. The reflex is
to shrink the new code; the correct move is to read the ceiling as a signal that the
concern seam is already there waiting. The cast-exit accrual didn't belong in
`chapter_open` at all — it belonged in `turn_state`, which already owned
`turn_direction` and `chapter_turns`, the exact dependencies. The reconciliation
helpers were a self-contained, no-LLM ledger transform — a leaf (`ledger_reconcile`)
the whole time. The ceiling didn't cost me a split; it *named* two splits I'd have
missed. `boring_enforcement` inverted: the surprise (size failure) revealed the spec
had under-specified where the code lived.

## The carve, repeated three times

Every new gap detector this session had a sibling it could be confused with
(`false_duplicate`). The discipline that held: **carve by the fields a detector
reads, not by its prose docstring.** `composition_gap` reads only the authored
`entry_state`/`exit_state` strings; `seam_precondition_gap` reads `beats` + committed
`world_state`. They are structurally incapable of overlapping because they consume
different inputs — and a test (`test_pure_lethal_seam_not_flagged_by_composition_gap`)
proves a lethal case fires the sibling and *not* the newcomer. The carve isn't a
comment; it's the input set.

## The smaller trap

FR-542 Part B's summary test asserted two reversals across three chapters; it got
one. My instinct was to widen the detector. Wrong: the middle card carried
"unclaimed" in its `open_threads`, so re-securing the bundle in Ch2→Ch3 was the
*resolution of an open thread*, not the reversal of a resolved event — semantically
correct to ignore. The fixture was wrong, not the detector. I rebuilt it to reverse
two *different* resolved facts across two pairs. Respect the RED — and respect the
GREEN-that-undercounts: it can be the detector telling you your fixture lied.

## Heuristic

- **ceiling_as_seam_finder**: when an additive change trips the module-size gate
  *after* GREEN, do not shrink the new code first — ask which existing module owns
  the dependencies (relocate) and whether the addition is a self-contained transform
  (extract a leaf). The ceiling names the FR-536 split you under-specified.
- **carve_by_inputs**: carve a new detector against its siblings by the fields it
  reads, not its docstring; prove non-overlap with a test that fires the sibling and
  not the newcomer. Structural carves can't drift; documented ones can.

**Seed:** Three of this session's modules are now sub-200-line leaves whose only
coupling is "reads the authored chapter card." If every continuity gate reads the
same card shape, is the card itself the missing typed boundary — a `ChapterCard`
Pydantic model — and would typing it surface the next non-composition as a schema
error instead of a 16-turn play?
