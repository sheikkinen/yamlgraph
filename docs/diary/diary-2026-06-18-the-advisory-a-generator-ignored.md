# The Advisory That a Generator Ignored

**Date:** 2026-06-18
**FR:** FR-521 (S1 falsified by witness)
**Arc:** DM v2 intra-chapter continuity hardening

## What happened

FR-521's prior diary ("The Record Already Existed") celebrated the cheap fix: the
director already flags the break every turn, so just *feed the flag forward* and the
next turn's intent map will stop re-proposing it. The unit tests proved the wiring.
Then the user asked the question the tests could not answer: *"can we rerun the last
offending chapter to see effects?"*

I built a single-chapter replay harness — re-play 10022-BC Ch3 ("Arnulf Lost to the
Water") with Ch1–Ch2 held constant, so the only changed variable is the
feed-forward — and counted the director's Arnulf continuity flags. Expected: a drop
below the 8/16 baseline. **Result: 13/16. It got worse.**

The replayed intents told the whole story in one column: **Arnulf is in the cast and
acting in all 16 turns** — "I haul myself onto the firmer bank", "I lunge up and
grab Reinmar's staff." The advisory block I had so carefully phrased ("when choosing
this turn's intents, do NOT let Arnulf repeat this break") was read and **ignored**.
The per-character intent map generates an intent for every roster member; a swept-
away brother is still a roster member, so it kept generating him climbing out of the
river he drowned in.

## The trap

**`advisory_to_generator_is_not_a_gate`.** I had written the previous diary entry
naming `detection_without_enforcement` — "lint without gate = advisory" — and then
committed exactly that sin one level deeper. I moved the detection signal to a new
place (forward into the scene) and called it a fix, but I added **no mechanism that
can prevent the break**. An instruction in a prompt is advice to a stochastic
generator, not a constraint on it. The only thing that stops the intent map from
animating Arnulf is removing Arnulf from the cast.

There was a second, quieter failure: **I contaminated my own metric.**
`running_scene` feeds one `scene` string to all three turn nodes (map → direct →
recap). My block, meant for the intent map, also lands in the *director's* input —
so the director's `continuity` count, the number I was measuring, can now echo the
warning I injected. I had built a thermometer and then held a match to it. The 8→13
rise is partly a real non-effect and partly measurement pollution; I cannot fully
separate them, which is itself the indictment.

## Why the tests passed anyway

The unit tests asserted the *wiring* (the block appears, windows correctly, is
intent-scoped) — never the *efficacy* (does the break rate drop?). Efficacy is not
unit-testable; it is a live-witness property. Commandment 2 — "code that has not been
run must not be trusted" — and the FR's own J5 witness clause are precisely the guard
for this gap. The witness was deferred in the FR as "corroboration, not a gate." It
turned out to be the only thing that could falsify the design, and it did.

## The cure

The witnessed root cause is **roster membership**, not missing advice. And the fix is
already half-built: J2 (this same FR) made `missing_presumed_dead` a chapter-scoped
death-point in `dead_character_names`. The next step is to feed that death-point into
`_filter_roster_for_lifecycle` so the swept-away actor is **dropped from the next
turn's cast** mid-chapter — turning J2's detection into enforcement. That is the
original S2, now unblocked by J2 (no structured J3 field needed). Recommendation
recorded in the FR: revert the inert S1 block, keep J2 and the harness, reopen as the
S2 roster-drop.

## Heuristic

When the fix is "tell the LLM not to," it is not a fix — it is a hope. For a
stochastic generator, the only enforcement is to change what it *can* produce
(remove the actor from the cast, constrain the schema, drop the tool), never what you
*ask* it to produce. And never measure a generator's output with a signal you have
just injected into that same generator's input.

**Seed:** Every gate in this codebase eventually reduces to "remove the option,"
not "discourage the choice" — the lifecycle roster filter, the finite beat ledger,
the Pydantic schema. Is "advisory text to an LLM" ever a legitimate enforcement
primitive, or should the FR template carry an explicit check: *"if your mechanism is
a prompt instruction, name the gate that backs it — or mark it as advisory and do not
claim it prevents anything"*?
