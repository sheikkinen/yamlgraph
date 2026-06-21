# Research Plan: Best Practices for Modeling Plot

**Status:** Research plan (not yet executed). Authored 2026-06-21.
**Motivation:** The DM v2 continuity program (FR-474 -> FR-558) modeled plot by
**recognition** -- generate prose, then extract and gate a plot model from it.
That approach is open-ended by construction ("there are always more plot elements
to capture"). This plan scopes the research needed to choose a **generative** plot
model for DM v3, where prose is realized *from* a closed vocabulary instead of
parsed back *into* one.
**Companion docs:** [`v3-rewrite-guidance.md`](v3-rewrite-guidance.md),
[`continuity-issues.md`](continuity-issues.md),
[`continuity-projection-plan.md`](continuity-projection-plan.md).

---

## 0. The thesis under test

> Plot defects in v2 are not a finite backlog of missing detectors; they are the
> signature of recognizing an **open set**. The escape is a small, **closed,
> generative** vocabulary of plot, authored once, from which prose is realized
> downstream -- so there is nothing load-bearing to recapture.

The research must either **support** this (and recommend a concrete vocabulary)
or **falsify** it (and justify continuing with recognition + richer lanes).

---

## 1. Research questions

**RQ1 -- Vocabulary.** What is the minimal *closed* set of plot primitives from
which the v2-class breaks (early reveal, phantom reversal/double-return,
unresolved affect thread, unplayable epilogue) become **ungrammatical by
construction** rather than caught downstream?

**RQ2 -- Lanes.** v2 modeled *ontology* (alive/dead, faction, relationships). The
10037-BC premise ("alive but believed dead") proves at least one missing lane:
**belief/epistemics**. Which lanes are load-bearing -- belief, causal link, affect
debt, world fluent, character goal/intention -- and which single lane, added
first, retires the most v2 gates?

**RQ3 -- Grain.** v2's ledger is chapter-grain; the revived-actors witness showed
an **intra-chapter, turn-grain** lifecycle break (Arnulf dies t7, on stage
t8-16). At what grain must each lane be carried (book / chapter / turn / beat)?

**RQ4 -- Generation coupling.** How do existing systems feed the plot model *into*
generation (so a protected character cannot die on the page) versus only *checking*
it afterward? This is the v2 gap (`plan-over-prose for bookkeeping only`, §2 of the
guidance).

**RQ5 -- Authoring boundary.** Where does the plot model get authored, and how is
its **internal consistency** checked before any prose exists? (The floodmark
synopsis promised both a death and a non-floor revival -- an unsatisfiable spec no
downstream gate caught.)

**RQ6 -- Fit to a capped-scene engine.** DM plays each chapter under a fixed turn
cap and closes on `scene_complete = (k == n)` over finite beats. Which models
compose with a bounded realizer, and which assume unbounded narration?

---

## 2. The survey map (bodies of work to review)

Grouped by the primitive each contributes. For each, capture: the core
representation, what it makes ungrammatical, its grain, how it couples to
generation, and its known failure mode.

### 2a. Finite function/role grammars
- **Propp, *Morphology of the Folktale* (1928).** 31 functions, 7 roles,
  constrained order. Contribution: a *closed alphabet*; `departure`/`return` are
  distinct authored functions, so "return before its floor" is ungrammatical.
- **Story grammars: Rumelhart (1975), Thorndyke (1977), Mandler & Johnson
  (1977).** CFG-style episode structure. Contribution: hierarchical episode/goal
  nesting. **Failure mode to heed:** Black & Wilensky (1979) falsified strong
  story-grammar claims -- context-freeness is too weak for inter-character
  causality. Keep the finite vocabulary; drop the context-free assumption.
- Modern descendants: **Dramatis / story-grammar planners**, the **Hero's Journey
  / Save the Cat beat sheets** as informal closed vocabularies used in practice.

### 2b. Plan- and causality-based models (the spine candidate)
- **Meehan, TALE-SPIN (1977).** Story as goal-directed planning over character
  goals + world operators. Contribution: characters *plan*; events have
  preconditions/effects.
- **Lebowitz, UNIVERSE (1985).** Plot fragments + author goals for long-running
  serial plot.
- **Riedl & Young, IPOCL (2010).** Partial-order causal-link planning **plus
  intentionality** -- every action motivated by a character goal; causal links are
  first-class objects. Contribution: the "load-bearing plot facts" *are* causal-link
  preconditions; **parallel-safety = the plan is a partial order** (directly
  formalizes the v3 litmus). Strong spine candidate.
- **Ware & Young, CPOCL / Glaive (2011-2014); conflict + intention partial-order
  planning.** Contribution: models *conflict* (thwarted intentions) as structure --
  relevant to the feud/truce core of DM premises.
- **Porteous & Cavazza, planning-based interactive narrative; constraint-based
  plot.** Contribution: authorial constraints as planning landmarks.

### 2c. Affect / reader-state models (the missing relational lane)
- **Lehnert, Plot Units (1981).** Per-character +/-/neutral affect states; four
  links (motivation, actualization, termination, equivalence); named units
  (retaliation, loss, hidden blessing, betrayal). Contribution: the **affect-debt
  lane** -- the Ch6->Ch7 unresolved confrontation is an *unterminated loss unit*.
- **Dramatic arc / tension models: Brewer & Lichtenstein (1982, structural
  affect); narrative tension curves.** Contribution: pacing as a first-class signal.
- **McIntyre & Lapata; suspense models (Cheong & Young, Suspenser).**
  Contribution: computational suspense as planned reader epistemic state.

### 2d. Epistemic / intention graphs (the lane the floodmark premise demands)
- **Elson, Story Intention Graphs (DramaBank, 2012).** Goals, plans, beliefs,
  affectual states, and **textual provenance** in one graph. Contribution: a
  unified schema that already carries **belief per agent** -- "believed dead" is
  representable. High-value target.
- **Doxastic/epistemic logics for narrative; theory-of-mind / nested belief
  (`believes(A, believes(B, x))`).** Contribution: the formal `believes(observer,
  fact, t)` lane; mistaken-identity, dramatic irony, "presumed dead" become native.
- **Herman, *Story Logic* (2002); narratology of worlds + perspectives.**
  Contribution: the humanities account of storyworld + focalization to cross-check
  the formal lanes.

### 2e. Modern LLM-era story planning (closest prior art)
- **Hierarchical / outline-then-generate: Yao et al. Plan-and-Write (2019);
  Fan et al. hierarchical story generation (2018-2019).** Contribution: plan as
  a control signal for neural generation -- but plans are usually *flat keyword
  outlines*, not typed state (the same reconstruction risk DM hit).
- **DOC / Re3 (Yang et al. 2022-2023): recursive reprompting, detailed outline
  control, plot-coherence via a learned controller.** Contribution: long-form
  consistency techniques; what they track vs. what they drop.
- **Dramatron (Mirowski et al. 2023): hierarchical co-writing (log line ->
  characters -> beats -> dialogue).** Contribution: a working closed hierarchy for
  LLM playwriting; evaluate its consistency lanes.
- **Simulation / agent approaches: Generative Agents (Park et al. 2023);
  character-driven emergent plot.** Contribution: emergent vs. authored plot --
  the opposite pole from Propp; useful as a contrast and a possible hybrid (author
  the function skeleton, simulate the beat interior).
- **Surveys: automated story generation surveys (Alhussain & Azmi 2021; Hou et al.
  2023).** Contribution: taxonomy + benchmark/eval landscape; entry points to the
  citation graph.

---

## 3. Evaluation rubric (how each model is scored for DM v3)

For each surveyed model, score against criteria derived directly from v2's failures:

| Criterion | Question | Why (v2 evidence) |
|---|---|---|
| **Closure** | Is the vocabulary finite and closed? | Recognition over an open set is the root trap. |
| **Belief lane** | Can it represent "X is true but Y believes not-X"? | 10037-BC "presumed dead" is unrepresentable in v2. |
| **Causal lane** | Are causal links first-class (not inferred from prose)? | Phantom reversal/double-return = missing `because`. |
| **Affect lane** | Are unresolved/owed emotional threads tracked? | Ch6->Ch7 unterminated loss unit. |
| **Generation coupling** | Does the model feed generation, or only check it? | v2 enforced plan-over-prose for bookkeeping only. |
| **Authoring-consistency** | Can the plot spec be checked unsatisfiable *before* prose? | Floodmark synopsis promised death + revival. |
| **Grain** | Does it support sub-chapter (turn/beat) state where needed? | Intra-chapter revival (t7 death, t8-16 onstage). |
| **Capped-scene fit** | Does it compose with a bounded realizer? | DM plays finite beats under a turn cap. |
| **Parallel-safety** | Can two chapters realize without reading each other's prose? | The v3 reconstruction litmus (guidance §8). |
| **Determinism** | Can the model be a CI gate (deterministic), vs. an instrument? | Witness/reviewer split (guidance §5). |

A model "wins a lane" if it makes that lane's defect class **ungrammatical by
construction**, not merely detectable.

---

## 4. Working synthesis hypothesis (to confirm or kill)

A candidate DM-v3 plot model, assembled from the lanes above, for the rubric to
test (not a commitment):

```
PLOT = partial-order plan of FUNCTIONS (Propp-like, closed alphabet)
  each FUNCTION carries:
    - preconditions / effects over a typed WORLD-STATE  (fluents; FR-513..518 lane)
    - preconditions / effects over a per-observer BELIEF-STATE  (epistemic lane)  <-- new
    - a causal link to the function(s) it enables  (IPOCL partial order)
    - an AFFECT-DEBT effect: opens / pays a per-character emotional thread  (Lehnert)
    - a role binding (7-ish roles) and an authored chapter/turn grain
  authored ONCE, write-once, monotonic; checked SATISFIABLE before any prose;
  prose REALIZED strictly downstream (v2 turn engine, demoted to realizer);
  the close proposes only a DELTA validated against plan + prose.
```

The hypothesis predicts: belief is the highest-leverage lane (retires the
most v2 gates), and a partial-order plan supplies parallel-safety for free.
**The research exists to confirm the lane ranking and the spine choice, or to
show a simpler closed model suffices.**

---

## 5. Method and phases

1. **Phase A -- Literature pass (read-only).** Walk the survey map (\u00a72). For each
   work, fill one row of a comparison table using the \u00a73 rubric. Prefer primary
   sources for the four foundational primitives (Propp, IPOCL, Plot Units, Story
   Intention Graphs); use surveys to widen the citation graph. Deliverable: an
   annotated comparison table + a one-paragraph "what it contributes / what it
   cannot do" per model.
2. **Phase B -- Lane analysis.** Map each v2 break class (from
   `continuity-issues.md` + the 10037-BC review) to the lane that would make it
   ungrammatical. Rank lanes by **gates-retired** (incident-density weighting).
   Deliverable: a lane-ranking with the evidence trail.
3. **Phase C -- Spine selection.** Choose the structural backbone (partial-order
   plan vs. function grammar vs. intention graph vs. hybrid) against \u00a73, with the
   capped-scene and parallel-safety criteria as tie-breakers. Deliverable: a
   decision record with the rejected alternatives and why.
4. **Phase D -- Minimal generative-vocabulary spec.** Write the smallest typed
   schema (lanes + grain + authoring/consistency rules) that the chosen spine
   needs. Deliverable: a draft schema + the satisfiability check it implies.
5. **Phase E -- Falsification spike.** Hand-author ONE plot spec for the floodmark
   premise in the candidate vocabulary; verify by inspection that the four v2
   break classes are unrepresentable, and that the synopsis-level contradiction is
   caught by the satisfiability check. Deliverable: the worked example + a
   go/no-go on the thesis (\u00a70).

---

## 6. Deliverables

- A comparison table of plot models scored on the \u00a73 rubric.
- A ranked list of plot **lanes** with the v2 break class each retires.
- A spine-selection decision record (chosen model + rejected alternatives).
- A minimal generative-vocabulary schema draft for DM v3 (the input to a v3 FR).
- A worked floodmark-premise example proving (or falsifying) \u00a70.

## 7. Scope guards (what this plan is NOT)

- Not a commitment to build v3 -- it produces the *model decision* a v3 FR needs.
- Not an LLM-prompt-engineering study -- the question is the *representation*, not
  the wording (FR-553 already showed salience/constraint beats prompt mass).
- Not a re-survey of v2's recognition gates -- those are the **incident record**
  that motivates the lanes, not candidates to extend.

## 8. Risks and biases to watch

- **Generator's bias toward the elegant model.** Propp and IPOCL are beautiful;
  beauty is not fit. Score against the rubric, not aesthetics
  (`framework_costume`: do not put an FSM in a DAG costume or vice versa).
- **Over-modeling.** A closed vocabulary that is too large reintroduces the open-set
  problem. Prefer the smallest lane set that kills the *observed* break classes;
  declare the rest explicitly out of scope (guidance \u00a74).
- **Emergent-vs-authored false binary.** Generative-agent simulation and authored
  plans are poles; a hybrid (authored function skeleton, simulated beat interior)
  may dominate -- keep it on the table.
- **Humanities/CS translation loss.** Narratology terms (focalization, fabula vs.
  syuzhet, diegesis) and CS terms (fluent, landmark, causal link) name overlapping
  ideas; build a small glossary to avoid double-counting lanes.
