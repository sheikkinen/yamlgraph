# The cap was real arithmetic and the wrong lever

**FR-604 — per-kind affect detection with protagonist focus (arm B REFUTED, arm A kept)**

## What happened

FR-603 closed by naming the next lever "structural, not textual" and the user named it
precisely: *feelings are abstract and hard for an LLM — analyze one at a time*. The quest
0/4 read isolated two structural causes: the one-op-per-beat cap forfeits 25% of the recall
ceiling (7/28 deltas are the 2nd+ on a multi-affect beat), and the merged GT-roster sprays
supporting-character deltas the protagonist-only gate scores as false positives. The judged
FR split the fix into two arms so the gain would be attributable. Both arms ran clean. The
verdict surprised me twice.

## The cap was real arithmetic — and not the binding constraint

I had the 25% number cold: 7 of 28 GT deltas live on beats the single-pass cap can never
fully serve. It is correct arithmetic, and it *felt* like a recall lever. The per-kind sweep
removes the cap — each kind gets its own pass, its own budget — so the quest F6
`loss`+`hope` double-close should finally land. It did not. `multi-recovered = []` on every
draw. The loss detector skipped F6 entirely; the hope detector closed at F8 (the crown
placement) instead of F6. Giving each kind a budget did nothing, because the model never
disagreed about *how many* deltas a beat carried — it disagreed about *which beat* carries
the close. The 25% was a ceiling, not a floor: removing the constraint that bounded recall
from above does not raise recall from below when the real loss is beat-localization.

This is the trap worth naming. A correct, precise, mechanically-derived number
(`cap_forfeit = 0.25`) presented itself as a lever simply because it was a number about the
metric. It measured *headroom*, not *reachability*. The arithmetic was honest and the
inference from it was wrong: "the cap forbids 25%" silently became "removing the cap recovers
25%." Headroom is what you could win if every other thing were perfect; the other things were
not perfect, and they were the whole game.

## The guard fired exactly where the Judge aimed it

The Judge's correction 2 was that removing the cap AND the six-way kind competition together
is the *maximal over-emission configuration* — both suppressors that held the FR-598
invention engine down, gone at once. That is precisely what happened, and the per-kind
precision table named the culprits without ambiguity: retaliation 0/18 and hidden_blessing
0/27, two detectors whose GT support is one delta each, flooding the corpus with confident
invention. The four high-support kinds behaved (hope 0.60, betrayal 0.33). 100% of the
precision violation lived in the two rarest kinds. A detector asked "where does this
character feel hidden_blessing?" will always find a setback to call a gift — the leading
question manufactures the answer, exactly as FR-596→598 found for the prose engine.

## What survives a refutation

Two findings outlived the verdict. First, char-pinning is a free, clean precision win
(0.12→0.375) — the 0.12 was a merged-roster artifact, and the Judge was right to forbid
benchmarking against it. Second, the wrong-feeler bug is *fixed*: quest now binds `F4 open
hope` to Eira, not to Ossa the ferryman who gives her the charm — char-pinning plus a single
exemplar clause ("the hope is the RECEIVER's, not the giver's") did it. The architecture
under test failed its precision gate, but the experiment paid for itself in two durable
corrections that no aggregate score would have surfaced.

And the refutation came with its own next lever, measured for free from the same draws:
dropping the two zero-support detectors recomputes to precision 0.409 > the 0.375 floor with
the +0.107 recall intact. That is an FR-605 candidate, not a thing to ship under this grant —
because "which kinds to sweep" is a new scope that needs its own judgement, and because it
does not touch the larger remaining lever, beat-localization.

## Heuristic

**A metric's headroom is not a lever.** When a deterministic decomposition tells you a
constraint forbids X% of the target, that is a ceiling on what you *could* gain, not a
promise of what you *will* gain by lifting the constraint. Before treating "the cap forbids
25%" as a recall lever, ask the cheaper question: if I remove the cap, does the model
actually place the freed-up deltas on the right beats? Here it did not — the loss was never
in the budget, it was in the reading. Lift the constraint in a throwaway arm and check that
the freed capacity is *used correctly*, before believing the headroom number is yours.

## Seed

The two findings that survived (char-pinning, receiver-anchored exemplar) were *components*
of a refuted bundle. The Judge's arm-split made them legible — arm A isolated char-pinning,
the per-kind table isolated the floods, the multi-recovered counter isolated the cap
failure. Could a refuted FR mechanically emit its surviving components as typed
"keeper-findings" — a structured residue (here: `char_pin: +0.255 precision`,
`receiver_exemplar: F4 fixed`, `cap_removal: null`) — so the next FR inherits the dissection
instead of re-deriving it from prose? The diary records it; nothing enforces that FR-605
reads it.
