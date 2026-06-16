# The Capability We Pruned With the Duplication

*Diary — 2026-06-16 — FR-491 retrospective, prompted by a reviewer's reflection*

## What happened

A day after FR-491 retired the three single-scene finishes (`final_cut`,
`final_cut_turns`, `walkthrough`) and replaced them with one whole-book compose,
a reviewer named what the −1611-line deletion had quietly swept up:

> final_cut and the replaced process worked for a single chapter with the key
> value of following the prescripted plot in detail. It also provided the final
> text of the chapter. First book generation must be a composition of these
> results.

That is exactly right, and it exposes a mistake hiding inside a clean refactor.

## The trap: N→1 collapse is only safe when each of the N was redundant

The Slice 4 deletion *looked* like textbook entropy-killing (Commandment 8):
three graphs rendering one scene, collapsed to one. And `final_cut`,
`final_cut_turns`, and `walkthrough` genuinely *were* redundant **with each
other** — three renderings of the same played arc, a real `false_duplicate`
cluster worth burning.

But the collapse smuggled in a second, false claim: that the three were also
redundant **with the new book compose**. They were not. `final_cut` carried two
values the book pass does not replace:

1. **Fidelity** — it followed the prescripted plot *in detail*, consuming the
   canonical `beats`, the phase-tagged `arc`, and an explicit `climax` marker,
   under the rule "preserve every canonical BEAT — each must be recognisable."
2. **Final text** — it produced the chapter's actual polished prose.

The new `close_chapter` keeps neither. Look at what it stores: `text: recaps` —
the chapter's "final text" is now the concatenated *turn recaps*, a summary
register, with no beat-fidelity check. So `book.yaml` was handed two jobs in one
pass: elevate recap-summary into rendered prose **and** stitch chapters into one
arc. The most overloaded node in the graph — and, not by coincidence, the exact
node that hit the empty-book token bug (see yesterday's entry). The overload was
visible in the token budget before it was visible in the design.

The heuristic, sharpened: **collapsing N components into 1 is safe only when each
of the N was redundant with the survivor — not merely with each other.** Audit
every victim for a *distinct* value before deleting. Surface similarity (three
"finish" graphs) is not capability equivalence.

## The deeper inversion: subtraction can overshoot

Yesterday's entry celebrated this arc as `growth_as_default` inverted — pruning
over planting, six subtractive commits, the one addition carrying the only bug.
That was true and also incomplete. Pruning has its own failure mode: it can cut
past the duplication into the capability the duplication was *wrapped around*.
The three finishes were a redundant *packaging* of a non-redundant *function*
(faithful per-chapter final text). I threw out the function with the packaging.

So the corrected lesson sits between the two traps. `growth_as_default` says
don't add by reflex. This entry says don't *subtract* by reflex either: when the
dominant motion is deletion, the scrutiny belongs on the survivors —
*"what did each deleted thing do that nothing remaining now does?"* — exactly the
question the reviewer asked and the refactor did not.

## What the corrected architecture wants

Fidelity is cheapest to enforce *locally*, at the chapter, against that chapter's
own summary and beats, where context is small and the check is falsifiable
("every beat present"). The book compose is the wrong place to verify plot
fidelity — it must hold the whole arc and invent detail at once. The reviewer's
pipeline restores the missing layer and orders the passes by *verifiability*:

- **faithful per-chapter final text** (restored final-cut value, chapter scope) →
- **book = composition of those final texts** (deterministic first pass, no LLM —
  the seam where the empty-book bug lived should not be a generative seam at
  all) →
- **multiple LLM passes** for continuity-unification and voice (gate-able early,
  taste-driven late).

`book.yaml` already accepts `draft` + `instruction` and returns a full revision —
the revision machinery exists; only a verification-driven driver is missing
(`verification_checkpoint_primitive`, already a Scripture seed). This is its
first concrete use case. Captured as FR-492.

## Seed

We have a heuristic for adding (`growth_as_default`: don't plant by reflex) but
none for cutting. What would a **`prune_overshoot`** guard look like — a
mechanical check, at the moment of an N→1 collapse, that forces the author to
record for each deleted component the surviving thing that now covers its
distinct value, and fails the collapse when any cell is "nothing"? Could the
diff that deletes a graph + its prompt require, in the same commit, a line
naming where its capability went — turning "I deleted three finishes" into "each
of these three values now lives here," and making capability-loss a visible
omission instead of a silent one?
