# The loser I let win

**Date:** 2026-06-27
**Context:** Making the interiority A/B experiment conclusive — replacing an
N=1 haiku tie with a multi-draw preference rate under a stronger judge.

## What happened

The earlier single observation was untrustworthy for two reasons I had already
fixed (contaminated surface control, a haiku judge that misread a faithful
affect arc as a contradiction). To make it conclusive I did two cheap things:
pinned the two judge nodes to a stronger tier (`claude-sonnet-4-6`) while
keeping the writers on haiku, and ran 8 independent draws with seed parity
counterbalancing blind slot position. Honest contrast B vs A1: 6/8 = 75% = GO.

## The trap I almost fell into

When the batch came back 6/8 for my hypothesis, the pull was to report the rate
and stop — the number agreed with me. The discipline that saved the result was
reading the **loss** first, not the wins. Run 4 was the single A1 win. Had it
been a judge misread (the exact failure that poisoned the N=1), the whole
"stronger judge" premise would be a costume, not a cure. It wasn't: the judge
dinged arm B with two verbatim-quoted opened-but-unclosed threads — the
technique's *own* failure mode, honestly applied. A judge that only ever
confirms B is a rubber stamp; a judge that will convict B on quoted evidence is
an instrument. I could only tell which one I had by reading the case it made
*against* my hypothesis.

## Heuristic

**To trust a judge, read the verdict that goes against you, not the one that
agrees.** A preference rate is only as trustworthy as the judge's willingness
to rule the other way — and the only proof of that willingness is a
quote-grounded loss in your own favored arm. Aggregate agreement is cheap;
adversarial agreement is the signal.

A corollary surfaced in the data: B beat the *surface* control (A1, 75%) far
more decisively than the *bare* writer (A0, 50% / mostly ties). The realistic
alternative to authored interiority is a character bible with looks and voice —
and that bible actively *hurts*, anchoring attention on appearance while
leaving affect threads open. The unguided writer was the harder baseline to
beat. Choosing the wrong control would have understated the effect.

## Seed

If a quote-grounded loss is the proof a judge is honest, could the harness
*require* one before reporting a GO — refusing to emit an aggregate until the
judge has convicted the favored arm at least once across the draws, the way TDD
refuses GREEN before a RED? An experiment that has never seen its hypothesis
lose has not yet been tested.
