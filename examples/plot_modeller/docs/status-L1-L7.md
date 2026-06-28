# Status Report: L1–L7 Pipeline Layers

**Date:** 2026-06-27
**Scope:** Per-layer spike results for the Plot Modeller formalization pipeline.
**Companions:** [plan-implementation-phases.md](plan-implementation-phases.md) (the gated build plan),
[emotions-and-the-llm.md](emotions-and-the-llm.md) (the L7 appraisal-theory post-mortem),
[architecture.md](architecture.md) (the L1–L7 layer stack).

---

## Summary

| Layer | Name | Verdict | Measured | Gate | FR(s) | Date |
|-------|------|---------|----------|------|-------|------|
| **L1** | Extract agents/world/beliefs | GRANTED — not measured | — | recall ≥ 0.90 | FR-573 | 2026-06-24 |
| **L2** | Extract goals | **REVISE** | recall 0.72 / prec 0.52 | recall ≥ 0.80 | FR-574 → FR-581 | 2026-06-24 |
| **L3** | Extract glosses (beats) | **GO** | recall 0.88 / prec 0.87 | recall ≥ 0.80 | FR-575 | 2026-06-24 |
| **L4** | Classify kinds | **GO** | 0.80 self / 0.90 blind | recall ≥ 0.75 | FR-570 → FR-572 | 2026-06-23/24 |
| **L5** | Assign pre/eff (world state) | **REVISE → architectural** | recall 0.55 flat | recall ≥ 0.70 | FR-576 → FR-582 | 2026-06-24 |
| **L6** | Assign causality | **GO** | enables recall 0.96 | recall ≥ 0.75 | FR-577 | 2026-06-24 |
| **L7** | Assign affects (emotion) | **REFUTED — input ill-posed** | ceiling ~0.25 | recall ≥ 0.50 | FR-578 → FR-609 | 2026-06-24/26 |

**Headline:** 3 layers green (L3, L4, L6), 2 in prompt-revision purgatory (L2 authorized, L5
escalated to architectural), 1 unmeasured (L1), and 1 closed as ill-posed (L7). The pipeline is
**gated GO** — the Phase 1b blind-corpus KILL gate passed at L4 (0.90). The remaining work is
concentrated in the *world-state* and *goal* layers, not the *structural* ones.

---

## Per-layer detail

### L1 — Extract agents/world/beliefs — GRANTED, not measured
- **Authority granted** (FR-573, 2026-06-24); enforcement/spike not yet run.
- Lowest-risk layer — named-entity extraction is a solved NLP task. Gate is agent recall ≥ 0.90.
- **Blocker:** none; awaiting a build slot. It is the only layer with *no measured number*.

### L2 — Extract goals — REVISE (0.72), revision authorized, re-spike pending
- **FR-574 spike:** goal recall 13/18 = **0.72**, precision 13/25 = **0.52**. Gate ≥ 0.80 → REVISE.
- **Failure modes:** `rel(...)` relational goals never extracted (scifi `rel(Mara, Jonas, lovers)`
  = 0); secondary-protagonist survival dropped (horror `alive(Fen)`); over-generation (12 spurious
  goals → 0.52 precision floor). Root cause: prompt example set shows only `alive`/`holds`/`at`.
- **FR-581:** revision **authority GRANTED** (name-anchoring, `rel` example, goal ceiling 2–5 → 3–6,
  underscore normalization). **Re-spike result not yet recorded** — this is the open action.

### L3 — Extract glosses (beats) — GO (0.88)
- **FR-575:** beat recall 42/48 = **0.88**, precision **0.87**. Gate ≥ 0.80 → GO.
- The "creative pivot" (where one beat ends and the next begins is subjective) nonetheless recovers
  cleanly. L4–L7 consume L3 output, so its quality is load-bearing — and it holds.

### L4 — Classify kinds — GO (0.80 self / 0.90 blind) — KILL gate PASSED
- **FR-570 spike:** 28/35 = **0.80** across 4 genres, all 16 kinds exercised.
- **FR-572 blind corpus:** **0.90** on a synopsis authored without sight of the kind list; 39/48 =
  0.81 on the retrofitted 4-genre set. Gate ≥ 0.75 → **GO**.
- This is the **project KILL gate** (Phase 1b): the 0.80 was not authorial leakage. Pipeline
  construction authorized. The 17-kind Propp-derived vocabulary generalizes.

### L5 — Assign pre/eff (world state) — REVISE → escalated to architectural
- **FR-576 spike:** combined world recall 47/85 = **0.55**, predicate precision 48/170 = **0.28**.
- **FR-582 re-spike (after one prompt revision):** **0.55 Haiku flat; 0.51 Sonnet regressed.** The
  stop rule ("one revise, then escalate") fired → **the next step is architectural, not wording.**
- **Failure modes:** 100% of `at(X)=false` departure effects dropped (only arrivals emitted);
  multi-word object-token paraphrase (`firmware_channel` → `firmware update`); open free-text
  value-label divergence on `rel`/`faction`. Per-genre: scifi 0.35, detective 0.50, quest 0.58,
  historical 0.67, horror 0.76.
- **Interpretation:** predicate *invention* (not classification) is the hard part; a single-call,
  free-text world model under-determines its own labels. Candidate architecture: two-step
  (enumerate state variables, then assign values from a closed set) or move-decomposition as a
  deterministic post-pass.

### L6 — Assign causality — GO (0.96)
- **FR-577:** `enables` recall **0.96**. Gate ≥ 0.75 → GO.
- Causal links are constrained by beat order (forward-only); the whole-beat-list single call gives
  the model the cross-beat context it needs. The strongest layer in the stack.
- **Caveat:** the L7 arc found that the *derived goal graph* built from these edges
  (`derive_goal_graph`) produced some backwards/antagonist edges (`expose_ARIA enables
  trace_anomaly`; `protect_traders enabled_by` the antagonist's goal). The per-edge `enables` recall
  is high, but the *assembled goal topology* is not yet validated as a graph. See L7 dependency.

### L7 — Assign affects (emotion) — REFUTED, input ill-posed
- **FR-578 spike:** affect recall **0.09** (haiku) / **0.09** (sonnet) — model-invariant; scaling
  *hurt*. Gate ≥ 0.50.
- **Arc FR-596 → FR-609** (decomposition, regenerability ruler, per-kind/per-budget sweeps, two-pass
  what-then-where, goal-anchored referent, goal-graph referent): every prompt, model-scale,
  decomposition, and metric-relaxation lever was spent. **Ceiling ~0.25** even with ground-truth goal
  injection at the referent (FR-607). Chain-adjacency metric relaxation recovered nothing (0.059 flat
  at k=0,1,2 — picks are 5+ hops away or in disconnected goal-graph components).
- **Root cause (2026-06-26, the deepest floor):** the fixtures are **synopsis**, not scene. The
  scifi fixture has 13 beats, mean 35.8 words/gloss, and **0/13 glosses contain any emotion or
  interiority word.** Affect lives only in the *authored* `eff_affect` annotation, never in the
  source text. So "locate the emotion in the beat" asks the model to read a signal the input was
  never written to carry — any interpretation is text-valid, inter-annotator agreement is impossible
  *by construction*, and no metric sophistication can rescue a score over emotion-free text.
- **Two findings, one above the other:**
  1. *Appraisal theory* (emotions-and-the-llm.md): an emotion is an appraisal of an event relative
     to a **goal**; the model has a strong emotion-lexicon prior over a weak goal-appraisal model, so
     affect should be **derived from L2/L6**, not detected in parallel.
  2. *Input adequacy* (the gold diary): even a perfect goal model cannot locate affect in text that
     contains none. The construct is ill-posed at the **input**, one level below the metric.
- **Disposition:** L7-as-LLM-detection is **closed**. Two viable paths remain (see next steps).

---

## Cross-layer reading

The green layers are the **structural** ones (L3 beats, L4 kinds, L6 causal links) — classification
over text that *contains* the target. The troubled layers are the **world-model** ones (L2 goals,
L5 world state, L7 affect) — they require *inventing* or *projecting* structure the synopsis only
implies. The plan ranked L7 the lowest-risk of Phase 3 ("classify, don't invent"); it was the
hardest, because emotion is the most goal-dependent — and most input-absent — quantity in the stack.

A semantic dependency the phase DAG does not show: **L7 depends on the *correctness*, not merely the
*existence*, of L2 and L6.** Affect is a projection of the goal layer, so chasing L7 while L2 sits at
0.72 and the assembled goal topology is partly backwards was premature by construction.

---

## Recommended next steps (priority order)

1. **Re-measure L2 (FR-581).** It is the only "REVISE" with an authorized-but-unrun revision, and it
   gates L5 reachability, L6 causality scoping, and any future L7 projection. Run the re-spike and
   record the verdict. *Cheapest high-value action.*

2. **Escalate L5 to an architectural FR.** The prompt-only path is exhausted (0.55 flat, stop rule
   fired). Write the two-step world-model FR: (a) enumerate state variables, (b) assign values from a
   closed selection set, with deterministic move-decomposition for `at(X)=false` departures (the
   single largest miss cluster — 100% dropped).

3. **Validate the assembled goal topology (L6 follow-up).** `enables` recall is 0.96 per-edge, but
   `derive_goal_graph` yields backwards/antagonist edges. Add a graph-level validator (no antagonist
   goal as `enabled_by` a protagonist goal; edge direction follows beat order) before any consumer
   (reachability, L7 projection) trusts the topology.

4. **Decide L7's disposition explicitly.** Two text-valid options:
   - **(a) Projection:** replace L7 detection with a deterministic reader —
     `affect = sign(Δ goal_congruence)` per beat, computed from validated L2/L6 transitions; the LLM
     only names goals and their congruence flips. Moves emotion from a thing to *detect* to a thing
     to *compute*, so the gate measures goal-tracking (the capability actually in question). **Blocked
     on steps 1 and 3.**
   - **(b) Rewrite the input:** convert the fixtures from synopsis to *scene* with committed
     interiority, then re-run detection. Only worth it if a downstream consumer needs reader-facing
     affect rather than computed affect.
   Until one is chosen, **the L7 gate should be removed from the pipeline**, not left red — scoring a
   layer over an input that cannot carry its signal is theatre.

5. **Adopt an input-adequacy pre-gate for every extraction layer.** Before authoring a recall gate,
   grep the source for the target signal (the L7 lesson:
   `check_the_input_carries_the_signal_before_scoring_for_it`). ~0 hits means the construct is
   ill-posed at the input — revise the input or drop the layer before spending FRs measuring the model.

6. **Schedule L1 enforcement.** It is the last unmeasured layer (authority granted, gate ≥ 0.90).
   Low-risk, but the pipeline cannot run end-to-end (Phase 4 merge) until it produces validated output.

---

## Phase status (against plan-implementation-phases.md)

| Phase | What | State |
|-------|------|-------|
| 0 | Schema + validators | Complete |
| 1 | Vocabulary + blind KILL gate | **GO** (L4 blind 0.90) |
| 2 | Extraction L1–L3 | L1 unmeasured, L2 REVISE (re-spike pending), L3 GO |
| 3 | Formalization L5–L7 | L5 REVISE→architectural, L6 GO, L7 REFUTED (closed) |
| 4 | Merge + full pipeline | **Blocked** on L1 (measure), L2 (≥0.80), L5 (architectural) |
| 5 | Plan contract + docs | Not started |

**Phase 4 is the bottleneck.** It needs L1 measured, L2 ≥ 0.80, and L5 ≥ 0.70 (or a deliberate
descope of the world-state slice). L7 no longer blocks it — it has been removed from the critical
path by the REFUTED verdict; the merge node should either consume computed affect (step 4a) or omit
the affect slice entirely.

---

## Results in the light of the research

The original plot-modeling research lives in the DM:
[`examples/dungeon_master/docs/research-results-modeling-plot.md`](../../dungeon_master/docs/research-results-modeling-plot.md)
(executed 2026-06-21). Read against it, the L1–L7 numbers stop looking like a scatter of
prompt-quality outcomes and resolve into **one prediction the research already made.**

### The research's one-line thesis

> Robust plot is **authored from a closed vocabulary and projected into prose**, not
> **recognized back out of prose.** Plot defects are the signature of recognizing an open set.

And its mechanism for *every* deep lane (Phase D, "Projection replaces reconstruction"):

> chapter cast, prose-exclusion set, protected set are all **read from the plan, never parsed
> from prose**… the world-truth lane is **authored, not re-derived.**

The Plot Modeller pipeline is the *exact inverse* of this: it takes a finished synopsis (realized
prose) and tries to **recover the typed lanes back out of it.** It is a recognizer. The research's
§0 names recognition of an open set as *the pathology itself.*

### Each layer is a research lane, and the results rank the lanes by recognizability

The research ranked the lanes by **generative leverage** (what authoring them lets you forbid).
The pipeline results rank the same lanes by **recognizability from prose**. The two orders are
**inverted** — and that inversion is the thesis confirmed, not contradicted.

| Layer | Research lane | Research leverage rank | Measured | Recoverable from prose? |
|-------|---------------|------------------------|----------|--------------------------|
| L4 kinds | Propp function vocabulary (the **closure primitive**) | alphabet | **0.90** GO | Yes — closed alphabet, surface-classifiable |
| L3 beats | (event segmentation, pre-lane) | — | **0.88** GO | Yes — events are on the page |
| L6 causality | Causal link + partial order (IPOCL spine) | **#2** | **0.96** GO* | Partly — local adjacency yes, *order* no |
| L2 goals | Goal/intention | **#5** | 0.72 REVISE | Weakly — goals are implied, not stated |
| L5 world fluent | World fluent (the FR-513 ledger lane) | **#4** | 0.55 → architectural | Weakly — state is authored, not narrated |
| L1 belief | **Belief** `believes(obs, fact, t)` | **#1** | **unmeasured** | No — belief is the gap between truth and text |
| L7 affect | Affect-debt (Plot Units) | **#3** | ~0.25 REFUTED | **No — affect was authored elsewhere, never projected** |

The three green layers are exactly the lanes whose target is **on the surface of the prose**:
the finite function alphabet (L4), the events themselves (L3), and local causal adjacency (L6
per-edge). The troubled and closed layers are exactly the lanes the research calls **authored and
deep** — goals, world fluents, belief, affect-debt. *The pipeline succeeds where recognition is
legitimate and fails where the research said only authoring works.*

### The four sharp consequences

1. **L7's REFUTED verdict was pre-written in the research (1c).** Plot Units are an *open/close
   affect graph* connected by motivation/termination links — "an opened affect unit with no
   **termination link**" is the ungrammatical object. Affect is **relational and goal-referential
   by definition**, never a label on a beat — and Lehnert's units were "originally **analytic**"
   (a recognition device) whose value is only as "a **closed generative vocabulary** for arcs."
   The L7 arc (FR-578→609) spent fourteen FRs rediscovering, the hard way, what the research stated
   in one clause: you cannot recognize affect out of prose; it is opened and closed by **authored
   deltas** (the §5 floodmark spike literally writes `effects.affect: open loss(Hilde)` as an
   *authored* effect). The 0/13-emotion-words finding is the same fact from the input side: the
   synopsis carries no affect because affect lives in the **affect-debt delta**, authored alongside
   the function and never projected into the prose.

2. **Affect presupposes belief — and belief (L1) is unmeasured.** The research ties the affect lane
   to the belief lane (suspense = *planned reader epistemic state*; relational emotions like
   `guilt`/`betrayal` are gaps between agents' beliefs). L7 was chased while its prerequisite lane —
   the research's **#1 highest-leverage lane** — has *no number at all*. We measured the projection
   before the thing it projects from. The appraisal-theory post-mortem in
   [`emotions-and-the-llm.md`](emotions-and-the-llm.md) reaches the same conclusion from the theory
   side; the research reached it from the architecture side three days earlier.

3. **L6's GO is on the easy half of its lane.** The research's causal lane is valuable for the
   **partial order** ("two events unordered by a causal link realize in any order" = parallel-safety;
   "plan exists ⇔ satisfiable" is the authoring-consistency check). The 0.96 is *per-edge `enables`
   recall* — the local, surface-recoverable half. The **assembled order** is unvalidated, and the
   L7 arc already caught it producing backwards/antagonist edges (`expose_ARIA enables
   trace_anomaly`). By the research's own rubric, the causal lane is not green until the
   *partial-order plan-validity check* passes, not just the edge classifier.

4. **L5 and L2 are hard for the same reason, not for prompt reasons.** World fluents (L5, lane #4)
   and goals (L2, lane #5) are **authored state**, not narrated state — the research locates the
   world-truth lane explicitly on the *authored* side ("authored, not re-derived"). Trying to
   *extract* them from a synopsis is recognition of a lane the research says is never recoverable.
   L5's escalation-to-architectural (0.55 flat) is the empirical confirmation: prompt wording cannot
   close a gap that is **structural to the recognition framing**, not lexical.

### What this means for the pipeline's premise

The honest reframing: **Plot Modeller is a *bootstrapper*, not a *recognizer*.** Its legitimate job
is to recover the **surface lanes** (function-kind, beats, local causality) from a synopsis and to
*propose* drafts of the **deep lanes** (goals, world, belief, affect) for a human to author and
correct — never to be **gated as if the deep lanes were recoverable to a recall threshold.** The
research is unambiguous that the deep lanes are authored. So:

- **Gate the surface lanes on recall** (L3, L4, L6-edges): legitimate, and they pass.
- **Do not gate the deep lanes on recall against a single authored gold** (L1 belief, L2 goals,
  L5 world, L7 affect): the gold *is* the authored artifact; scoring recognition against it measures
  how guessable the authoring was, which the research says is low by design. Treat these layers as
  **draft-and-confirm**, with a human authoring pass, or compute them from already-authored upstream
  lanes (the L7 projection in step 4a, the §4 effect-delta model).
- **Add the research's authoring-consistency checks** (Phase D RQ5) as the real validators, replacing
  recall gates for the deep lanes: plan-exists (partial-order satisfiability), monotonic lifecycle,
  **affect closure** (every opened unit terminates — this is L7's *correct* gate, and it is a
  deterministic graph check, not an LLM recall score), capped reachability, belief grounding.

In one line: **the green layers recognize what is on the page; the red layers tried to recognize
what the research already proved is authored off the page — and L7 is simply the lane where "off the
page" is total.**

---

## Prompt and graph complexity analysis

Raw size is a weak signal. The dimension that actually predicts a layer's verdict is **task shape**,
scored on four axes:

1. **Interacting outputs** — how many fields must be produced *and kept consistent with each other*
   (1 independent label = easy; 4 cross-constrained fields = hard).
2. **Classification vs invention/inference** — picking from a closed list (easy) vs inventing
   predicates or doing multi-hop reasoning over an injected structure (hard).
3. **Injected cross-referenced context** — does the model have to hold a goal graph + a skeleton +
   the beats in mind *simultaneously* and cross-reference them (hard), or just read the beats (easy).
4. **Interacting rules / branches** — additive disambiguation (easy) vs rules that condition on each
   other plus Jinja `{% if %}` output-shape forks (hard).

| Prompt | Lines | Outputs | Task | Injected ctx | Flag | Layer verdict |
|--------|------:|---------|------|--------------|------|---------------|
| `classify_kinds` | 65 | 1 (kind+subject) | classify from 17-list | beats only | **GREEN** | L4 GO 0.90 |
| `assign_causality` | 61 | 3 local | classify + 1 order rule | beats + agents | **GREEN** | L6 GO 0.96 |
| `extract_glosses` | 58 | 1 (beat) | segment | synopsis | **GREEN** | L3 GO 0.88 |
| `extract_goals` | 61 | 1 list | extract (implied) | synopsis + agents | **AMBER** | L2 REVISE 0.72 |
| `extract_agents` | 66 | 3 lists | extract (named) | synopsis | GREEN-ish | L1 unmeasured |
| `encode_perspective` | 93 | 2 slices/char | invent per viewpoint | per-agent account | **AMBER** | L5 (provisional) |
| `assign_pre_eff` | 96 | **4 slices** | **invent** predicates | beats + agents + 7 kind-priors | **RED** | L5 0.55 → arch |
| `assign_pre_eff_snapshot` | 98 | 4 slices | invent | + snapshot state | **RED** | L5 variant |
| `affect_throughline` | 89 | 1/beat + close-map | per-beat + cross-beat close-inference | beats + 6×resolution table | **AMBER-RED** | L7 |
| `affect_locate_goal` | 90 | **3 (open/close/ref)** | **inference** + goal binding | beats + goal **list** + skeleton | **RED** | L7 REFUTED |
| `affect_locate_graph` | 107 | **4 (open/close/ref/toward)** | **multi-hop graph reasoning** | beats + goal **graph** (3 rel/goal) + skeleton + 4 referent rules + 2 forks | **RED (worst)** | L7 REFUTED ~0.25 |

### The flagged prompts

- **`affect_locate_graph` (107L) — the single most overloaded prompt in the example.** It asks for
  four cross-constrained outputs (open, close, referent, toward) while injecting a *causal goal
  graph* (every goal carrying `enables`/`enabled_by`/`threatened_by`), a phase skeleton, **four
  distinct per-emotion referent rules** (hope → sub-goal it enables; loss → threatened goal; guilt →
  goal whose pursuit harmed; betrayal → goal an ally's turn obstructs), and two Jinja output-shape
  branches. The model must cross-reference graph × beats × skeleton to pick one of several *sibling*
  goals by structural inference. This is not classification — it is structured reasoning over an
  injected knowledge graph, on an input (synopsis) that does not even carry affect. **It is both the
  most complex prompt and the deadest layer — those are the same fact.** Its own header concedes
  FR-607's flat-list parent gave "honest lift +0.000."

- **`assign_pre_eff` / `assign_pre_eff_snapshot` (96/98L) — predicate invention across four slices.**
  Four slices (pre_world, eff_world, pre_belief, eff_belief), each a list of typed predicates the
  model must *invent* (not select), with free-text label values, plus a movement-decomposition rule,
  a verbatim-naming rule, and seven kind-conditioned effect priors. L5's escalation to architectural
  (0.55 flat) is this complexity hitting its ceiling: you cannot prompt-engineer your way out of
  asking one call to invent four interacting predicate slices over an under-determined vocabulary.

- **`affect_locate_goal` (90L) — same overload, one notch down** (flat goal list instead of graph);
  FR-607 measured it at the +0.000 lift that motivated the even-heavier graph fork. Both are sunk.

- **`encode_perspective` (93L) — AMBER, and honestly self-labeled.** Its header says "PROVISIONAL…
  do NOT treat this contract as settled or clean." Two slices per character viewpoint, transition-
  pair rule, and a known low-precision `pre_world`. Reasonable for what it attempts, but it is doing
  belief/world work (the deep lanes) and inherits their recognition difficulty.

- **`affect_throughline` (89L) — AMBER-RED.** Single output per beat (good), but the **close-op kind
  table** (six kinds × resolution-signature mapping) smuggles *cross-beat inference* into a
  nominally per-beat classifier: deciding which earlier feeling a beat resolves requires holding the
  whole arc in mind. That hidden cross-beat dependency is the same structure that sinks the locate
  prompts.

### The green prompts confirm the rule

`classify_kinds` (0.90) and `assign_causality` (0.96) are *not short* — 65 and 61 lines — but every
line is **a closed-list definition or one local rule**. One output (or three independent local
ones), classification not invention, beats-only context, additive disambiguation. **Size is spent on
the vocabulary, not on interacting constraints.** That is the shape that works.

### Entropy flag: the affect-prompt graveyard

Eleven prompts exist for the single REFUTED L7 layer: `affect_detect_kind`, `affect_goals`,
`affect_licensing`, `affect_locate`, `affect_locate_goal`, `affect_locate_graph`, `affect_set`,
`affect_throughline`, `assign_affects`, `regenerate_affect_arc`, `judge_affect_fidelity` — plus the
`assign_affects`, `l7_measure` graphs. This proliferation of near-duplicate variants is itself the
smell (Scripture 8: *kill entropy and false idols; burn duplicates*): a layer that needed eleven
prompt rewrites was never workable by prompting. With L7 REFUTED, all but the one frozen-gate path
(`affect_locate`, the FR-605 baseline) and any kept for the historical record should be **pruned**,
or moved to an `archive/` subfolder, so the live prompt set reflects the live pipeline.

### The rule, stated for reuse

> **A prompt's failure risk tracks the number of mutually-constrained outputs it must invent or
> infer over injected context — not its line count.** One closed-list classification with a long
> vocabulary is safe at 100 lines; four interacting invented slices, or a multi-output inference
> bound to an injected graph, is unsafe at any length. When a prompt crosses ~3 interacting outputs
> **or** asks for predicate invention **or** requires cross-referencing two injected structures,
> split it into single-output passes (the L4/L6 shape) — or, if the signal is authored off-page
> (L1/L5/L7), stop prompting and author/compute it instead.
