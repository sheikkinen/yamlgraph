# Grading the self-report

**Date:** 2026-06-30
**Arc:** plot_modeller round-trip skeleton — P0\u2192P3 built, K=6 gate read, P4 refuted
**FRs:** FR-613 (gate, read filled), FR-614 (refuted), FR-622 (re-scope)

## What happened

Built the walking skeleton P0\u2192P3 as authorised: a one-graph round-trip (premise \u2192 cast \u2192 chapter
briefs \u2192 prose map \u2192 deterministic assemble \u2192 coherence gate). The gate, under decision (a),
measures the **authored** affect arc — it walks the `eff_affect` open/close ops the brief-author
declared, split by `scene_type`. Stopped at the gate as instructed and ran K=6 across five genres.

The read demolished the plan. Not the code — the **premise**.

- The same premise gave **opposite numbers** on two draws (Loom 0.40 vs 0.00).
- The P4 hypothesis (reactive\u226bproactive dangling) had **no directional support** across five premises.
- The danglers' real causes were **positional** (threads opened in the final chapter) and
  **invalid** (closes of never-opened threads the pop-walk silently swallowed) — never the
  recognition-gap the whole arc was built to fix.
- `scene_type`, the load-bearing control axis, was **mislabelled** (horror tagged 4/4 proactive over
  grief/guilt/loss).
- And the gate was **blind to a worse defect**: in the detective sample the protagonist's gender
  flips between chapters (he\u2192she), because each map branch drafts in a fresh context with no bound
  cast identity.

## The trap

**`grading_the_self_report`.** Under decision (a) the author *declares* the arc and the gate *grades
the declaration*. That is a tautology wearing a metric's clothes: the number moves with the author's
caprice, not the story's coherence. I had folded a whole "tautology guard" into FR-614 to defend
against the rate falling *by fiat* — and still didn't see that the entire gate was the tautology, not
just P4's edit of it. The guard was bolted to the wrong plank.

The deeper trap underneath the user's challenge — *"is this futile? just use the biggest model and
ditch haiku"* — is **`model_size_as_validity`**: the belief that a stronger generator removes the
need for a grounded check. It does the opposite. A stronger author produces a *more plausible*
self-report, which is *harder to falsify* — a more convincing tautology. Model size is a quality
knob; it is orthogonal to whether the gate measures the artifact or the artifact's self-description.

## Why the skeleton still won

The instinct was to read "haiku produced garbage" as "the skeleton was a waste." It was the reverse.
The skeleton is an **instrument**, and in one day of scaffolding it returned a decisive, non-obvious
finding: the indicted lane (P4) is wrong, the defect is **upstream** (the author's structural
validity) and **lateral** (map continuity binding), and the gate itself measures the wrong thing. A
frontier one-pass model would have produced a prettier book and **hidden** the same defects behind
fluent prose — the gender flip would have shipped. The skeleton's value was never the book; it was
that it made the failure **legible and located** cheaply.

## The heuristic

> A gate that grades a generator's own declaration measures caprice, not coherence — at **any** model
> size. Ground the metric in the artifact (prose-vs-plan), validate the declaration deterministically
> (reject the impossible: phantom closes, final-chapter opens, label/op contradictions), or delete
> the gate. An ungrounded number is worse than no number, and a stronger author makes it worse, not
> better.

Corollary on model assignment: a node that *classifies and plans structure* is a judgement task, not
a "writer." The repo convention (writers=haiku, judges=strong) was right; the brief-author was just
filed in the wrong drawer. Promote structure to the strong model, keep prose cheap.

## Seed

If the only honest coherence check is prose-vs-plan, and the prose classifier is itself an LLM —
**what grounds the grounder?** Is there a deterministic floor (named-entity continuity, tense/POV
stability, beat-coverage) that can be checked without a second model's taste, so the LLM classifier
only adjudicates the genuinely semantic residue? The next instrument may need a **two-tier gate**:
mechanical invariants below, model-judged fidelity above — and a measured variance number so we know
which tier the noise lives in.
