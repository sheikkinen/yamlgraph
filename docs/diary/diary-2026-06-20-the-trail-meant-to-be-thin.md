# Diary -- 2026-06-20 -- The Trail That Was Meant to Be Thin

## What happened

FR-544 persists the FR-541 character overlay -- a derived projection folded at
intent time and then discarded -- into the continuity witness as an `overlay_trail`
block. The implementation was small and boring: walk the roster, reuse
`derive_overlay`, omit the empties, stamp `visibility-not-gate`. The interesting part
was the judgement that preceded it, not the code.

## The trap: emptiness read as failure

The reflex when a new measurement comes back near-empty is to assume the measurement
is broken. The overlay trail, on real 10031-BC data, carries essentially one
character (Arnulf -> missing) because `character_state_deltas` is itself thin -- most
chapters commit zero deltas. A naive implementer would "fix" the thinness by widening
the source, inventing deltas, or treating `{}` overlays as a bug to be filled.

But the thinness *is the signal*. The trail is honest precisely because it omits
characters with no committed delta: a sparse trail is a true measurement of sparse
deltas. The witness's value is making that sparsity visible per-run instead of
discovered by an ad-hoc Python probe. Folding the "sparse-is-truth" note into the
emitter docstring is the cheap guard against a future maintainer "repairing" the
honesty out of it.

## The deeper insight: derived state belongs in the witness, not the store

`the_one_law` says normalize/derive at the consumption boundary, never store the
fold. FR-544 respects that for the *generation* path (overlay stays out of
`story.json`) while still giving *review* an auditable record -- by recomputing the
derived trail into the witness artifact, not by persisting it as authored state. The
witness is the correct home for derived measurements: it travels with the run, it
cannot drift from its source (it is recomputed), and it never gates. Two postures --
"derived, never stored" for generation and "derived, emitted for review" for the
witness -- coexist without contradiction once you see they read the same source at
different boundaries.

## Heuristic

When a new witness reads near-empty, ask whether the emptiness is a defect in the
witness or a true report about a thin source. If the source is thin, the witness's
job is to *surface* that thinness, not to mask it -- and the docstring must say so,
or someone will later "fix" the honesty into a lie.

## Seed

The overlay trail and the seam-entrance/fact-reversal witnesses all recompute from
the same committed source at review time. Is there value in a single witness pass
that folds the source ONCE and feeds all three detectors, so they cannot diverge on
what "the committed chapter" was? Or does sharing the fold couple detectors that
should stay independently auditable?
