# The rationale that quotes

**Date:** 2026-06-26
**FR:** FR-606 (optional affect rationale field, default-off)
**Arc:** L7 affect legibility (FR-596 -> FR-607)

## What I did

Added an optional, default-off `rationale` to the affect prompts so each delta can
carry a one-line, beat-quoted reason. The hard part was not the field — it was proving
the field changes *nothing* when off, and that the model cannot lie its way past the
quote constraint.

## The trap I avoided: gate_checks_shape_not_substance, two ways

1. **Parity by assertion vs parity by snapshot.** I could have "proven" default-off
   safety with a test that checks `"rationale" not in rendered`. That checks shape, not
   substance — it would pass even if the explain block had perturbed whitespace
   elsewhere. Instead I captured **golden snapshots of the pre-change render** before
   touching the templates, then asserted byte-equality after. The proof is now anchored
   to the artifact as it existed, not to my belief about it. Whitespace control (`{%-`)
   was the whole game: a naive `{% if %}` block leaves newlines that silently break
   byte-parity.

2. **Quote-check in code, not in the prompt (J: correction).** The one job a stateless
   worker cannot be trusted to do is validate its own grounding. FR-598 already proved
   it: asked to "explain yourself", haiku returned a 658-token novel. So the
   `>=3 consecutive words` check lives in the harness as `_rationale_quotes_beat`, and
   the demo confirmed it bites the right way — 9/9 rationales quoted a real beat span,
   zero novels. The constraint, not the instruction, did the work.

## The insight worth keeping

The judge named the rationale a **probe that perturbs**: asking the model to justify a
placement changes the placement (the observer effect / rationalization effect). So an
explain-mode draw explains the explain-mode draw — it must never be folded into a scored
recall number. I encoded this structurally: `--explain` runs one draw and **returns
before** the scored verdict, writing to a separate dump dir. The discipline is not "be
careful not to mix them"; it is "make mixing impossible by construction."

And the field paid off immediately as legibility: the quest `hope` reason quoted *"the
lack is liquidated"* — the FR-605 referent mismatch (kingdom goal vs crown goal), which
took hours of prose archaeology to find, now readable in one emitted line. The autopsy
FR-607 needs is now free.

## Heuristic

> To prove an addition is inert when off, diff against a snapshot of the artifact taken
> *before* the addition — not against an assertion about the artifact's shape. And when a
> diagnostic field perturbs the thing it measures, separate it from the measurement by
> construction (a different code path that returns early), not by convention.

## Seed

The rationale is grounded (it quotes a beat) but its grounding is checked against the
*cited* beat only. Could a stronger lint check the rationale against the **goal** the
emotion is about — i.e., does the quoted span actually describe a goal opening/closing —
turning the quote-check from "is this text real?" into "is this *appraisal* real?" That
is the L7-as-projection-of-goals question FR-607 opens.
