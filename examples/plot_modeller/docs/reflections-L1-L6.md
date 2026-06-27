# What L1–L6 Taught Us: A Reflection on the Plot Modeller Pipeline

**Date:** 2026-06-27
**Scope note:** The *live recognition pipeline is now L1–L6.* L7 (affect detection) is **concluded** —
refuted as an LLM layer and folded out of the forward path; it survives here as the lesson that
reshaped the pipeline and as a deterministic *validator* (affect closure), not as a layer to fix.
This document therefore reflects on L1–L6 as the things still to build, and on L7 as the thing that
taught us how.
**Companions:** [status-L1-L7.md](status-L1-L7.md) (the numbers and full L7 autopsy),
[plan-next-phase.md](plan-next-phase.md) (what we do about all this),
[emotions-and-the-llm.md](emotions-and-the-llm.md) (the L7 appraisal-theory post-mortem),
[`../../dungeon_master/docs/research-results-modeling-plot.md`](../../dungeon_master/docs/research-results-modeling-plot.md)
(the 2026-06-21 plot-modeling research), [plan-implementation-phases.md](plan-implementation-phases.md).

---

## The one thing the seven layers taught

We built the pipeline as a **recogniser**: feed it a finished synopsis, recover the typed plot
structure back out of the prose, one layer per dimension. Seven layers later, the result is not a
list of prompt-quality outcomes — it is a single, clean finding the research had already written
down before we started:

> **Plot structure is authored and projected into prose, never recognised back out of it.**
> The layers that worked recover what is *on the page*. The layers that failed tried to recover what
> was *authored off the page* — and they failed in exact proportion to how far off the page their
> target lives.

Every other reflection below is a face of this one.

---

## The pipeline sorts itself into two halves

Not by difficulty, not by prompt effort, not by model scale — by **where the signal lives.**

**The surface half — recognition is legitimate, and it works.**
Events, the finite function alphabet, and local causal adjacency are all *present in the text*. A
reader can point at them. So can the model. These layers (beats, kinds, per-edge causality) passed
cleanly and stayed passed. They are classification over a closed vocabulary, and that is a task LLMs
are good at. The lesson is quiet but worth stating: **when the target is on the page and the
vocabulary is closed, the pipeline simply works** — no heroics, no arc of revisions.

**The deep half — recognition is a category error, and it shows.**
Goals, world-state, belief, and affect are not *in* the prose; they are the **authored scaffolding
the prose was projected from.** A synopsis is what survives after that scaffolding is removed. Asking
the model to recover them is asking it to reverse a lossy projection — to reconstruct the mould from
the casting. Every deep layer struggled, escalated, or was refuted, and no amount of prompt revision
moved them, because the gap was never lexical. It was structural to the act of recognising at all.

The deepest irony: the research ranked these same deep lanes as the *highest leverage* — the most
valuable things to **author**. The pipeline ranks them as the *least recoverable* — the hardest
things to **recognise**. Those two rankings are inverses of each other, and that is not a
contradiction. It is the thesis, proven twice.

---

## L7 is not a failure — it is the experiment's cleanest result

It is tempting to read L7 (affect) as the layer that "didn't work." That undersells it. L7 is the
**limit case that made the whole pattern legible**, because affect is the lane that lives *entirely*
off the page.

We confirmed this at the input itself: across thirteen beats of the science-fiction fixture, **not
one gloss contains a single emotion or interiority word.** The affect was authored — as an explicit
`open loss` / `close loss` delta beside the event — and then *not projected into the synopsis at
all*. So "find where the character feels grief" is not a hard question; it is an **unanswerable**
one. There is nothing in the input to find. Any reader's answer is a projection, two readers cannot
converge, and a recall score against one annotator's projection measures only how guessable that
annotator was.

The fourteen-FR arc that led here (FR-578 → 609) was not wasted, but it was the long way round. The
research had already said it in a single clause: Plot Units are *authored* open/close affect deltas,
and Lehnert's recognition use of them was "originally analytic." We rediscovered, through metric
archaeology, what was written in the source material — and the cheap probe that would have ended it
on day one was to **read the input and notice the emotion words were not there.** That probe now has
a name: *check that the input carries the signal before you score a model for finding it.*

---

## The metric made the model's own mistake, one level up

The most uncomfortable reflection. Throughout the affect arc, the model failed by treating an emotion
as a **label on a beat** and discarding its **referent** (the goal the emotion is about). Our metric
failed the same way: it scored the model by **beat-id equality** and discarded the same referent —
counting a different-but-text-valid reading as a placement error.

Both substituted an *identifier* for the *thing it refers to*. The model used the emotion word as a
proxy for the appraisal; we used the beat id as a proxy for the appraisal. Neither proxy carries the
goal, so both collapsed distinct meanings into one and called the survivors wrong. The cure was the
same at both levels and embarrassingly cheap: **read the prose.** The diagnosis that finally moved
the problem came from reading two beat files against the gold goal — not from any aggregate number.

The general law, sharper than "read the raw output first": *a metric computed over identifiers cannot
tell a referent disagreement from an error, so it will always misreport the first as the second.*

---

## We measured the projection before the thing it projects from

Affect is an appraisal of an event **relative to a goal**, and relational emotions (guilt, betrayal)
are gaps **between agents' beliefs**. So affect sits downstream of both the goal lane and the belief
lane. Yet we spent fourteen FRs on affect while:

- the goal lane (L2) was still below its gate, and
- the belief lane (L1) — which the research ranks as the **single highest-leverage lane in the whole
  design** — *has no measurement at all.*

We polished the roof of a house whose foundation was never poured. The honest sequencing was always
the reverse: belief, then goals, then — only if affect is still wanted — affect computed *from* them
rather than detected *beside* them. The phase plan's dependency arrows showed layer *existence*; they
did not show that L7 depends on the *correctness* of L2 and L6. That hidden semantic dependency is
where the effort leaked.

---

## Complexity was a symptom, not a cause

The prompts sort the same way the layers do, and reading them is diagnostic. The two prompts that
work (kinds, causality) are not short — but every line is a closed-list definition or one local rule:
one output, classification not invention, beats-only context. The prompts that failed grew four
mutually-constrained outputs, asked the model to *invent* predicates or *infer* over an injected goal
graph, and sprouted conditional output-shape branches. The most overloaded prompt in the whole
example — four outputs bound to an injected causal graph plus a skeleton plus four per-emotion rules —
sits on the deadest layer. **That is not a coincidence; it is the same fact viewed through the
prompt.**

The reflection: we kept adding prompt complexity to compensate for a signal that was not in the
input. Every rule we added was an attempt to *reason our way to* an answer the text did not contain.
The eleven affect-prompt variants are the fossil record of that effort — a layer that needs eleven
rewrites was telling us, each time, that the problem was not the wording. Complexity accreted exactly
where authoring was being mistaken for recognition.

---

## What each layer actually taught (one line each)

- **L1 — belief.** The keystone we never laid. The research's highest-leverage lane is the only one
  with no number; everything epistemic (secrets, reveals, dramatic irony) and every relational
  emotion waits on it.
- **L2 — goals.** Goals are *implied*, not stated; recognition gets most of them and invents a few.
  The residual is not a wording bug — it is the gap between what a synopsis says and what its author
  knew.
- **L3 — beats.** The honest success. Events are on the page; segmenting them is subjective but
  recoverable. This is the floor the rest stands on, and it holds.
- **L4 — kinds.** The proof that closure works. A finite, closed alphabet over surface events is the
  one thing recognition does cleanly — and the project's go/no-go gate rightly lived here.
- **L5 — world-state.** Where "invent, don't classify" hit its wall. World fluents are authored
  state, not narrated state; a single free-text call under-determines its own labels, and no prompt
  pass closed the gap. The escalation to architecture is the correct verdict, not a defeat.
- **L6 — causality.** A real success on the *local* question (which beat enables which) and an
  unexamined assumption on the *global* one (is the assembled order a valid partial-order plan). The
  edges are green; the graph is not yet checked — and the affect arc already caught it pointing
  backwards.
- **L7 — affect (concluded).** The limit case, and the teacher. Affect is authored entirely off the
  page, so recognising it is not hard but impossible — the attempt taught us more about the
  *pipeline's premise* than about emotion. It leaves the live pipeline as an LLM layer and re-enters
  it as a **validator**: affect closure over authored deltas. It is no longer a layer to fix; it is a
  lesson already learned and a check still worth running.

---

## What changes

The reframing is not a retreat; it is a correction of category. **Plot Modeller is a bootstrapper,
not a recogniser.** Its legitimate job is to recover the surface lanes outright and to *propose
drafts* of the deep lanes for a human to author — never to be graded as if the deep lanes were
recoverable to a recall threshold against a single authored gold.

So the verdict shape itself should change:

- **Keep recall gates on the surface lanes** (beats, kinds, causal edges). They earn their gate.
- **Stop gating the deep lanes on recall against the authored gold.** That number measures how
  guessable the authoring was — low by design — and dressing it as "capability" is the theatre the
  affect arc exposed. Treat these layers as *draft-and-confirm*, or compute them from upstream lanes.
- **Adopt the research's authoring-consistency checks as the real validators** — plan-exists,
  monotonic lifecycle, **affect closure** (every opened feeling must terminate), capped reachability,
  belief grounding. Note especially that *affect closure is L7's correct gate*: a deterministic graph
  check over authored deltas, not an LLM recall score over emotion-free prose. The layer we refuted
  as a detector is valid as a **validator**.
- **Sequence by dependency, not by layer number.** Belief and goals are upstream of affect; lay the
  foundation before the roof.

The pipeline did not fail. It ran an honest experiment and returned an honest result: it discovered,
layer by layer, the boundary between what prose carries and what its author kept — and it found that
boundary exactly where a forty-year-old research literature said it would be.

The concrete next moves — measure the belief keystone, re-level goals and world-state, validate the
causal topology, and turn L7 from a refuted detector into a kept validator — are sequenced in
[plan-next-phase.md](plan-next-phase.md).

---

## The next phase, in brief

The plan re-levels the deep lanes onto the right kind of gate and sequences the work by dependency
(belief and goals are upstream of everything; affect leaves the critical path). In order:

1. **Re-measure L2 (goals)** — run the already-built revision; cheapest action, gates everything
   downstream. If it lands below 0.80, re-level to draft-and-confirm rather than tune a third time.
2. **Measure L1 (belief)** — the highest-leverage lane, still unmeasured. Gate it on *grounding*
   (every reveal resolves a prior mistaken belief), not bare recall; expect to find belief is
   authored, not extractable.
3. **L5 (world-state) architectural FR** — replace the single invent-four-slices call with two steps
   (enumerate state variables, then assign values from a closed set) plus a deterministic
   move-decomposition for the dropped departures.
4. **L6 partial-order validity** — validate the *assembled* causal graph (forward-only, DAG,
   plan-exists), not just per-edge recall; the edges are green, the topology is not yet checked.
5. **Retire L7 as a detector, keep it as a validator** — delete the recall gate, archive the eleven
   affect prompts, install *affect closure* as a deterministic check.
6. **Phase 4 merge** — run L1→L6 end-to-end and gate the assembled plan on **coherence (the
   validator suite)**, not per-layer recall.

The through-line: **the authored gold is the target to draft toward, not the answer key.** Surface
lanes keep their recall gates; deep lanes trade recall for coherence validators; nothing on the deep
lanes gets more prompt complexity, because complexity there was the symptom, not the cure.
