# Remove the Option, Don't Discourage the Choice

**Date:** 2026-06-18
**FR:** FR-521 (S1 reverted → S2 enforced)
**Arc:** DM v2 intra-chapter continuity hardening

## What happened

This is the third diary entry in the FR-521 arc, and the one where the fix finally
landed. The chain:

1. *The Record Already Existed* — the director already flags the break every turn,
   so feed the flag forward (S1). Felt cheap and right.
2. *The Advisory a Generator Ignored* — the Ch3 witness raised the Arnulf re-flag
   count **8/16 → 13/16**. The advisory "do NOT let Arnulf repeat this break" was
   read and ignored; the intent map kept him in the cast and kept animating him. I
   had also contaminated my own metric (the block reached the director I was
   measuring).
3. This entry — revert S1, build S2: a structured `cast_exits` field on the
   director, and a roster filter that **drops** the exited actor from the cast.
   The same witness now reads **8/16 → 0/16**, non-degenerate: Arnulf acts through
   t1–t3 (grabs for Hilde, is swept), the director names his exit on t3, and from
   t4 he is gone from the cast and never flagged again.

## The trap, named and beaten

`advisory_to_generator_is_not_a_gate`. The previous entry *named* it; this entry
*measured the cure*. The number is the whole argument:

| Mechanism | Ch3 Arnulf re-flags |
|---|---|
| Baseline (nothing) | 8/16 |
| S1 — advisory text in the scene | **13/16** (worse) |
| S2 — drop the actor from the cast | **0/16** |

Same chapter, same inherited state, same model. The only variable is *where* the
intervention sits: in the prompt (a request) or in the cast list (a capability). A
stochastic generator does what it *can* do; the only enforcement is to change what
it can produce. S1 asked. S2 removed the option.

## What made S2 work where S1 failed

- **A structured channel, not prose.** S1 re-fed the director's free-text
  `continuity` string — the exact prose→structured boundary the judgement's J3 had
  warned about. S2 added `cast_exits: list[str]`, a typed field the director fills
  by *naming* the exited actor. Deterministic code reads names, not sentences.
- **Enforcement at the cast boundary.** The roster filter
  (`_filter_roster_for_lifecycle`) already existed for cross-chapter lifecycle
  gating at turn 1. S2 added a within-chapter layer that runs every turn: union the
  chapter's prior `cast_exits`, drop those ids. The character is not *told* to stop;
  it is *not asked to act* at all.
- **Agency up to the exit.** The design lets a character act through the turn it
  exits (its final struggle is legitimate drama), and benches it only *afterwards* —
  so the death scene still happens. The witness confirmed exactly this shape.
- **Never empty the cast.** If everyone has exited, keep the roster and let the
  chapter's turn cap close it — no empty-cast crash, no special-case raise.

## The witness was the experiment, not the corroboration

The FR had filed the witness under "corroboration, not a gate." Across this arc the
witness was the *only* instrument that could distinguish a real fix from a plausible
one: it killed S1 (which had passing unit tests) and confirmed S2. Unit tests prove
wiring; only the single-chapter replay — one changed variable, inherited state held
constant — proves efficacy. That replay harness is now itself an FR (FR-522),
because an experiment this load-bearing should not be a throwaway script.

## Heuristic

When the candidate fix is a string addressed to an LLM, it is a hope, not a gate.
Find the boundary where the model's *options* are constructed — the cast list, the
tool set, the schema's enum, the retrieved context — and remove the option there.
Then prove it with a controlled replay, because the difference between "asked not to"
and "cannot" is invisible in a unit test and decisive in production (8/16 vs 0/16).

**Seed:** S2 routes a death through `cast_exits`, and J2 routes it through
`dead_character_names`, and the seam packet routes it through `character_lifecycle`
— three structured death channels now, each chapter-scoped or cross-chapter by its
own rule. Is there one canonical "this character has exited" event these should all
derive from, or does each boundary legitimately need its own death-point with its
own scope, and what breaks the first time they disagree about whether Arnulf is gone?
