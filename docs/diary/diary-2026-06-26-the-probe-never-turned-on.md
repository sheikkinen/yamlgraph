# The Probe That Was Built and Never Turned On (FR-606 → FR-607)

*2026-06-26 — the autopsy that a refuted number could not give.*

## What happened

FR-607 refuted goal-anchoring with one damning number: referent-binding **0.143** — even
handed the exact ground-truth goal among leak-audited distractors, the model picks the
wrong sibling goal 86% of the time. The FR closed REFUTED, honestly, on a clean control
arm. But "check intent for 606, 607" forced me back to a thing the refutation had stepped
over: FR-606 had built a beat-quoted `rationale` probe *for exactly this moment*, and
FR-607 had run without it. The 0.143 told me **that** binding fails; nothing told me
**why**. I threaded `--explain` through the FR-607 harness, turned the FR-606 probe on,
and read the model's own reasons.

The answer was immediate and systematic: the errors are **not random goal-picking**. The
model binds each feeling to *the goal its chosen close-beat resolves*, then anchors the
close on the dramatic climax — so it names the **terminal** goal (coronation, justice,
daylight) where the annotator scoped the **proximate** one (retrieve the crown, deliver
the witness, reach the surface). The referent is *downstream* of the close-beat choice.
That single read explained the +0.000 lift mechanically: a flat goal list cannot move
placement, because the goal label is a consequence of where the model already decided the
arc ends.

## The trap I nearly walked past

A REFUTED verdict feels *finished*. The number was clean, the control was decisive, the FR
was committed — the gravitational pull was to call it done. But a refutation is a
measurement, not an explanation. I had a 0.143 and a shrug ("the model treats the goal
list as a labelling afterthought" — true, but shapeless). The FR-606 instrument was sitting
*right there*, already wired into the very prompt FR-607 forked (`{%- if state.explain %}`),
and I had not spent the one cheap draw it took to consume it. The trap is treating a
negative result as a closed book instead of a freshly-prepared microscope: the refutation
*built the apparatus* (enriched GT, referent scorer, forked prompt) under which the autopsy
becomes a one-flag run.

## The deeper pattern: latent instruments rot

FR-606's own judge predicted this exactly — the rationale field "risks being a default-off
field nothing ever turns on." It was right. The instrument shipped, the next spike ran
without it, and it sat latent for one full FR cycle. A diagnostic you build but never
*consume* is indistinguishable from one you never built. The value of a probe is realized
only at the moment some autopsy reads its output; until then it is speculative tooling
wearing a delivered badge. The cure is to bind the probe's delivery to its first
consumption — FR-606 should have landed *inside* the FR-607 autopsy, not beside it.

## Heuristic

**A refuted number is a microscope, not a tombstone — spend the cheap draw to read WHY
before you close the book.** When a spike refutes a hypothesis, the apparatus it built
(enriched fixtures, a sharper scorer, a forked prompt) is at its most powerful the moment
after the verdict. Turn on every legibility probe you own and read the model's own account
of the failure; the mechanism is almost always more specific — and more actionable — than
the aggregate that condemned it. Corollary: a diagnostic instrument is not "delivered"
until a real autopsy has consumed its output; bind its first use to its merge.

## Seed

The autopsy says the referent is entangled with the close-beat choice: the model names the
goal its terminal close serves. If that is the mechanism, then the disambiguator is not a
better goal *list* but the **L6 enables/threatens causal edge** — "this loss *threatens*
THAT goal at THAT beat" — which pins the close to the proximate goal's own beat rather than
the arc's climax. Would injecting the causal edge (not the flat goal menu) finally move
placement, because it constrains *where the arc ends*, not just *what to call it*? And is
the real lever upstream of L7 entirely — in whether L6 even distinguishes proximate from
terminal goal resolution?
