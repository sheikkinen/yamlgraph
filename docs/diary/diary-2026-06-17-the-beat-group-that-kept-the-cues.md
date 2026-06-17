# Diary — 2026-06-17 — The Beat Group That Kept The Cues

## Context

FR-505 enforcement changed the Final Cut composition seam from a flat turn-grid recap into beat-grouped input with explicit performance cards (`intent`, `dialogue`, `expression`). The failure mode under correction was structural: prose mirrored the same cast-order loop because inputs were shaped as repeated turn slices.

## Trap observed

I almost treated prompt strengthening as sufficient leverage. The code path showed the real pressure lived in the payload shape: turn recaps were preserved, but expressive cues were dropped before composition.

## What worked

- Build deterministic seam functions first (`beat_turn_groups`, cue/round-robin metrics) and pin them with pure tests.
- Keep connective turns attached to the most-recent advanced beat so no recap is orphaned.
- Keep performance-card schema stable even for empty fields; truncate values instead of deleting keys.
- Record baseline metrics before declaring witness improvements.

## What remains open

The live post-fix witness run (`10007-BC`) ended before chapter close (`stage: turn:1:14`), so A3/A6/A7 evidence remains pending even though code/tests are green.

## Heuristic

When a quality bug is described as "style," inspect the composition seam first: repeated output patterns often come from repeated input topology, not weak wording.

**Seed:** Should Final Cut emit a machine-readable composition trace (beat -> source-turn ids -> consumed cue ids) so A3/A7 witness collection can run automatically without manual log archaeology?
