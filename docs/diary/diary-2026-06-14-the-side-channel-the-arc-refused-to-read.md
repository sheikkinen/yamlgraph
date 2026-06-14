# The Side-Channel That the Arc Refused to Read

*Diary — 2026-06-14 — FR-486 DM v2 wider per-turn character performance*

## What happened

The DM v2 turn already asked each character, privately, what they *think* and
what they *intend*. The next two passes wanted full-text walkthroughs with
spoken lines and visible action. The temptation was obvious: let FR-487 invent
the dialogue and gestures at render time, from the cut text. I split it instead.
FR-486 *captures* a wider performance per turn — `dialogue` and `expression`
alongside the existing `thinking`/`intent` — and FR-487 will merely *render*
what was authored. The render pass should converge authored layers, not
hallucinate them.

## The trap I was watching for

`plausible_wrong_answer`. Widening one LLM call from two fields to four is the
classic way to silently degrade the field you already depended on. `intent` is
load-bearing for FR-481/482/483 — the whole arc steers on it. A model told to
also produce a line and a tell can quietly turn its single decisive `intent`
into a hedge ("Kara considers her options and may move…") while every
shape-checking test stays green. A degraded intent passes the schema. It passes
the seam-freeze test. It passes the persistence test. It only fails the *story*.

So the Judge added a binding the FR hadn't named: the prompt must keep `intent`
first and explicitly singular, and the live witness must show `intent` is
**undegraded** — not merely *present*. That is the difference between validating
shape and validating substance.

## The cure that worked

Two-layer defence at two different boundaries:

1. **Deterministic seam-freeze** (code, unit-testable): a sentinel test asserts
   `dialogue`/`expression` appear in neither `turn_direct.yaml` nor
   `turn_recap.yaml`. This is mechanical proof that the new fields are a
   side-channel — the arc *cannot* read them, so they cannot drift the story even
   if they're wrong. It was green from RED, and it is load-bearing precisely
   because it never needed to change.

2. **Generative witness** (prompt, live-run): the neutral-arc vertex run showed
   `intent` at 11 words, single-action check True, while `thinking` (24),
   `dialogue` (7), and `expression` (13) filled out around it. The interior is
   wide; the decision stayed sharp.

The asymmetry against FR-485 is the keystone: FR-485's alignment validator
**raises** on a missing segment (an arc post-condition — silence there is a bug);
FR-486's `turn_intents` **defaults to `""`** on a missing performance key (an
additive side-channel — silence there is benign). Same word ("missing"), opposite
correct behaviour, because they sit on opposite sides of the read/ignore line.
Confusing them would have been the real defect.

## Entropy note

Found and removed a dead `_turn_intents` on `session.py` — a stale two-field
duplicate of `turn_ops.turn_intents`, confirmed unused. Widening the live one
would have left the corpse carrying the old shape, a future false-duplicate trap.
Kill it at the widening, not later.

## Seed

If a captured side-channel is *defined* by a test proving the arc cannot read it,
could that freeze test be generated mechanically from the graph — diff the set of
state keys each downstream node references against the set a node *produces*, and
assert the new keys are in the produced-but-never-referenced complement? A
"side-channel" would then be a provable graph property, not a hand-written
sentinel I have to remember to write for FR-487, FR-488, and every widening after.
