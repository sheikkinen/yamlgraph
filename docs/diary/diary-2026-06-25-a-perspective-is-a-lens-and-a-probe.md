# A perspective is a lens and a probe

**Date:** 2026-06-25
**FR:** FR-590 (L5 multi-perspective) — Gate 1 run 1, KILL authority withheld
**Predecessor reflection:** [the wound that only changed its address](diary-2026-06-25-the-wound-that-only-changed-its-address.md)

## What happened

FR-587 exhausted the *operation* axis: every attempt to split comprehension from
encoding still floods `at`, because single-tier comprehension at the haiku size
re-asserts every location it sees. Its reflection reserved scale as the next lever.
FR-590 reached instead for a different axis entirely — *subject*, not operation.
Map over each agent, have the model narrate the plot from that one character's point
of view (stored as prose), encode only that character's fluents, then combine
deterministically. The bet: a single-character narrative *intrinsically* elides the
non-salient legs, so salience lives in the framing, not in an instruction or a
post-hoc collapse.

The run came back: recall **0.32 → 0.53** (cleared the floor FR-587 broke for the
first time), but `at`-FP **69 → 108** and precision 0.21. By my own decision rule —
`at`-FP must *fall* with recall holding — that is a KILL, and I said so.

The authority to KILL was withheld. "Analyze the issue." So I did, and the number
inverted on me.

## The trap

I had just written, one reflection ago, *suspicion of my own structural
satisfaction — the number that refuses to move is data, not an obstacle to argue
around.* I applied that lesson and walked straight into its mirror. FR-587's danger
was **over-crediting** a clean structure on a stubborn number. FR-590's danger was
the inverse: **under-crediting** a sound approach on a number my own instrument
inflated. The `at`-FP rose to 108 — but 58 of those 108 live in `pre_world`, a slice
that came back **81% garbage**, because my `encode_perspective` prompt told the model
to fill preconditions with "what must already be true." That re-imposed the exact
precondition-salience reasoning load FR-585/587 had isolated as *the wound* — inside
the very FR whose thesis is to remove that load. The `eff_world`-only `at`-FP is 50,
already below the 69 threshold. I measured a spike that violated its own contract and
read the contamination as a verdict. The stop rule that made FR-587's KILL
trustworthy became, here, a rule I almost mis-fired — because a KILL is only as
honest as the run is clean, and this run was not.

## The insight

Two things the score cannot see, and both argue the approach deserves to live past a
metric it didn't win.

**A character's point of view is not a scoring trick — it is the correct authoring
primitive.** The per-agent summaries (Mara's first-person account of the Loom is a
coherent, publishable arc) are not scaffolding for an L5 number; they are the
substrate a human author actually works in. A synopsis becomes a full plot by
*elaborating each character's throughline* — what they want, where they go, what
they learn, who they become. Perspective decomposition is the natural seam along
which a thin synopsis extends into a thick plot, and the stored prose is leverage for
exactly that elaboration, regardless of whether the downstream fluent encoder floods.
We optimized the artifact for a metric and forgot the artifact has standalone value
*upstream* of the metric — it is the writers' room, not just the parser's input.

**Splitting comprehension from representation makes error *attributable*.** The
monolith and the snapshot were single-stage and opaque: a wrong fluent could be a
comprehension failure (the model misread the story) or a representation failure (the
model read it right and typed it wrong), and nothing in the output let you tell which.
FR-590's pipeline stores the prose summary between the two LLM calls, so the drop is
now *localizable*: read the summary. If the summary says "Mara goes to Seoul" and GT
says "Seoul lab", the comprehension is right and the **encoding** drifted the token —
a representation bug. If the summary invents a journey GT never scores, the
**comprehension** over-narrated — a different fix entirely. The scifi 0.13 collapse,
read this way, is plainly a token-fidelity (representation) failure, not the model
failing to understand the plot. A two-stage, intermediate-stored pipeline is not just
a generator; it is a **probe** that points at its own failing component. The prior
single-stage approaches couldn't tell you *where* they were wrong — only *that* they
were.

## What I'd do differently

Catch the contract violation before the run, not after the challenge. The encode
prompt re-imposed the precondition load in plain sight — I even quoted FR-587's
"belief is not the wound" while handing the model the precondition wound. The fix is
mechanical: emit `eff_world` only, derive `pre_world` deterministically from each
agent's eff timeline (the FR-587 discipline I already had on the shelf), suppress
standing `alive`/`faction`, and keep summaries token-faithful. That is the one
permitted iteration, and its justification is FR-587's own: a contract-violating
fixture invalidates the measurement.

## Seed

If the same map-to-agents pipeline can *attribute* error to comprehension vs
representation, it can **gate** on it. Imagine a verification node that reads each
stored perspective summary against the glosses (did the character's arc stay
faithful?) and, separately, the encoded fluents against the summary (did the typing
stay faithful?) — two cheap LLM judges, each scoped to one seam. The pipeline would
then report not a single opaque score but a **fault address**: "comprehension 0.9,
representation 0.4 → fix the encoder." And one layer further: FR-587 is
precision-leaning and breaks recall; FR-590 is recall-leaning and breaks precision.
They fail on opposite axes. Is their *intersection* (agree-to-keep for precision)
over their *union* (either-may-add for recall) a frontier neither reaches alone — an
ensemble of two wrong readers that is right where they overlap?
