# 2026-06-25 — The stage that the gate would never have run

## What happened

FR-593 began as an elegant architecture: a **story-level vocabulary stage at Mode 4**
(gloss-extraction), the earliest boundary that still holds the synopsis, emitting
canonical glosses that every downstream mode would "inherit for free." The Judge
granted authority but made containment the PRIMARY correction: Mode 4's glosses feed
*every* layer (L4 classify, L6 causality at recall 0.96, L7, L8), yet the ACs measure
only L5 — rewriting the shared token in place is an unmeasured cross-layer regression
surface.

While enforcing, I read the harness and found the sharper fact: **the L5 evaluation
harness loads ground-truth glosses (`load_glosses_with_kinds`), bypassing Mode 4
entirely.** The beautiful upstream stage would never have been exercised by the gate
that judges the feature. The architecture diagram and the measured path were two
different things.

## The trap

`architecture_diagram_vs_measured_path` — I designed the change to live where the
*story* says the data is born (Mode 4, where the synopsis enters), not where the
*gate* actually reads it (the Mode-8 harness, which loads GT glosses for isolation).
An elegant placement that the acceptance measurement never touches is not elegant — it
is untested. The diagram is a story about the code; the harness is the code.

This is a cousin of `inventory_by_visibility`: I ranked the placement by narrative
legibility ("vocabulary is born at the synopsis, so put it there") instead of by where
the witness runs. The boundary that matters is the one the test crosses.

## The cure

The fix collapsed the two-node Mode-4 prologue into a single **additive field on the
measured path**: `canonicalize_glosses` writes `canonical_gloss` over the GT glosses
the Mode-8 harness already loads, leaving `gloss` byte-identical. Containment and
measurability became the *same* decision — the change is exactly as wide as the thing
the gate witnesses, and not one layer wider. The original-gloss-untouched assertion is
the containment proof; the bare-string-rejection test is the FR-592 regression proof;
both are deterministic, both ran in 0.04s, no LLM in the witness.

`the_one_law` still held — normalize at the boundary where external data enters — but
"the boundary" had to be re-read as *the boundary the measurement actually crosses*,
not the boundary the narrative prefers.

## Heuristic

Before placing a change, ask not "where is this data conceptually born?" but "where
does the acceptance gate actually read it?" If the harness isolates a layer with
ground-truth inputs, the upstream producer is bypassed — put the change on the
isolated path, additively, or the gate will score a feature it never ran.

## Seed

The harness loads GT glosses to isolate L5 from L3/L4 error. But FR-593's whole premise
— that naming drift is fixable upstream — is invisible under that isolation, because GT
glosses are already clean. **Is the isolation harness hiding the very defect the
feature targets?** Should there be a "drift-injection" eval mode that perturbs GT gloss
names before L5, so canonicalization has something real to repair and the gate measures
the repair rather than a no-op on already-canonical input?
