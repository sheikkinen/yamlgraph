# Research Results: Best Practices for Modeling Plot

**Status:** Research results. Executed 2026-06-21 against
[`research-plan-modeling-plot.md`](research-plan-modeling-plot.md).
**Method:** Literature pass (Phase A) grounded with primary/encyclopedic sources;
lane analysis (B), spine selection (C), minimal schema (D), and a floodmark
falsification spike (E). Where a claim rests on a specific source it is cited
inline; uncited claims are synthesis from the surveyed corpus.
**One-line finding:** The thesis holds. The field's durable consensus is that
robust plot is **authored from a closed vocabulary and projected into prose**, not
recognized back out of prose -- and the single highest-leverage primitive DM v2
lacks is a **per-observer belief lane**, which more than half the surveyed
traditions treat as foundational.

---

## 0. Verdict on the thesis (plan §0)

> Plot defects are the signature of recognizing an **open set**; the escape is a
> small, **closed, generative** vocabulary, authored once, prose realized
> downstream.

**Supported, with one sharpening.** No mature plot-modeling tradition recognizes
plot from finished prose; every one of them *authors a structured artifact first*
and treats text as its realization (Propp's functions, planning's operators,
plot units' affect graph, story intention graphs, and even the LLM-era
outline-then-generate systems). The sharpening: the closed vocabulary is not one
list but a **small set of typed lanes** -- *function/role, causal link, world
fluent, belief, affect-debt, goal/intention* -- and the research question that
matters is **which lanes, at what grain**, not "recognize more carefully."

---

## 1. The five traditions (Phase A annotated comparison)

Each entry: representation -> what it makes *ungrammatical by construction* -> grain
-> generation coupling -> known failure mode.

### 1a. Finite function/role grammars -- *the closure primitive*
- **Propp, Morphology of the Folktale (1928).** A wonder-tale is a selection from
  **31 functions** (absentation, interdiction, violation, villainy, departure,
  struggle, victory, return, unrecognized arrival, recognition, exposure,
  punishment, wedding...) over **7 roles** (villain, dispatcher, helper,
  princess/prize, donor, hero, false hero), in a **fixed ascending ("syntagmatic")
  order**; one actor may fill several roles and one role may be split across actors
  (verified: Wikipedia/Morphology). *Ungrammatical:* "return before departure,"
  "recognition before the branding that grounds it" -- ordering violations are not
  detected downstream, they are unspellable. *Grain:* tale-level. *Coupling:*
  generative (the Proppian generators, OPIATE's Proppian drama manager). *Failure
  mode:* domain-narrow (wonder tales); says nothing about *why* a function fires
  (no causality) or *who believes what* (no epistemics).
- **Story grammars (Rumelhart 1975; Thorndyke 1977; Mandler & Johnson 1977).**
  CFG-style Setting + Theme + Plot + Resolution with recursive episodes.
  *Contribution:* hierarchical goal/episode nesting. *Failure mode (load-bearing):*
  **Black & Wilensky (1979)** showed story grammars cannot capture
  inter-character causality and goal interaction -- context-free rules are too weak.
  **Lesson for DM: keep the finite alphabet; reject context-freeness.** The thing
  that replaced grammars is planning (1b).
- **Practitioner beat-sheets (Hero's Journey/Campbell; Save the Cat; Freytag).**
  Informal closed vocabularies used daily by working writers; evidence that a small
  function set is *productive*, not merely descriptive. Dramatron (1e) operationalizes
  this for LLMs.

### 1b. Plan- and causality-based models -- *the spine primitive*
- **Meehan, TALE-SPIN (1977).** Story as goal-directed character planning over a
  world with operators (preconditions/effects). *Contribution:* characters *plan*;
  events have causes. *Famous failure mode:* "mis-spun tales" -- without authorial
  constraints the plan produces causally-valid but dramatically-dead stories. Lesson:
  causality is necessary, not sufficient; you also need *author* goals (UNIVERSE) or
  *dramatic* constraints (drama manager).
- **Lebowitz, UNIVERSE (1985).** Plot fragments + **author-level goals** for
  open-ended serial plot. *Contribution:* separates character goals from authorial
  goals -- the first explicit "the author wants X to remain true" lane (DM's
  plan-protected character is exactly an author goal).
- **Riedl & Young, IPOCL (2010) -- strongest spine candidate.** Partial-order
  causal-link planning **plus intentionality**: every action is justified by a
  causal link to an effect AND motivated by a character's goal frame. *Ungrammatical:*
  an event with no causal antecedent (the "phantom" reversal), an action no character
  is motivated to take. *Grain:* event/partial-order. *Coupling:* fully generative.
  *Why it matters for DM:* the "load-bearing plot facts" the v2 guidance worries
  about **are causal-link preconditions** -- they are authored, never re-derived from
  prose; and **parallel-safety (the v3 litmus) = "the plan is a partial order"**:
  two events unordered by a causal link can be realized in any order. IPOCL
  *formalizes* the guidance's §8 acceptance test.
- **Ware & Young, CPOCL / Glaive (2011-2014).** Adds **conflict** as first-class
  structure (intentions that are formed but thwarted). *Contribution:* directly
  models feud/truce/betrayal -- the spine of every DM premise -- as planned thwarted
  intention rather than emergent accident.
- **Drama-manager / experience-management line (Oz Project; Mateas & Stern Facade;
  Automated Story Director; PaSSAGE).** A supervisory process selects/sequences
  "beats" to satisfy authorial dramatic goals and repair plot holes at runtime
  (verified: Interactive-storytelling survey -- drama manager + agent model + user
  model; planning-based repair via ASD/PAST). *Contribution:* the **gate-vs-author
  inversion** DM needs -- the manager *prevents* incoherence by construction instead
  of detecting it after.

### 1c. Affect / reader-state models -- *the relational lane*
- **Lehnert, Plot Units (1981).** Plot as a graph of per-character **affect states**
  (+ / - / mental-neutral) connected by four links -- **motivation, actualization,
  termination, equivalence** -- composing into named units: *retaliation, loss,
  fleeting success, hidden blessing, betrayal, enablement*. *Ungrammatical (the DM
  gap):* an **opened affect unit with no termination link** -- exactly the Ch6->Ch7
  break (Arnulf's accusation is an opened *loss/retaliation* unit that Ch7 never
  *terminates*). *Grain:* event-to-event across the whole story. *Coupling:*
  originally analytic, but the unit set is a closed generative vocabulary for arcs.
- **Structural-affect / tension (Brewer & Lichtenstein 1982); suspense (Cheong &
  Young, Suspenser).** Model the *reader's* expected affect (surprise, suspense,
  curiosity) as a planned quantity. *Contribution:* suspense is literally **planned
  reader epistemic state** -- it presupposes a belief model (1d), tying the affect
  and belief lanes together.

### 1d. Epistemic / intention graphs -- *the lane the floodmark premise demands*
- **Elson, Story Intention Graphs / DramaBank (2012) -- highest-value target.** A
  single graph unifying **goals, plans, beliefs, affectual states, and the textual
  span** that realizes each. *Contribution:* it already carries **belief per agent**
  and provenance -- "X is true but Y believes not-X" is a native edge, and the link
  to text is the projection DM wants. This is the closest existing artifact to the
  full lane set.
- **Doxastic/epistemic narrative logic; theory-of-mind / nested belief
  (`B_a(x)`, `B_a(B_b(x))`).** *Contribution:* the formal
  `believes(observer, fact, t)` lane. Mistaken identity, dramatic irony, "presumed
  dead," the secret, the reveal -- *all* are gaps between truth and belief, or
  between two agents' beliefs. A model without this lane **cannot represent a large
  fraction of plots**, DM's floodmark premise among them.
- **Herman, Story Logic (2002); narratology of storyworlds + focalization.**
  *Contribution:* the humanities cross-check -- "who knows / perceives what, from
  whose vantage" (focalization) is the same belief lane named from the literary side.

### 1e. Modern LLM-era story planning -- *closest engineering prior art*
- **Plan-and-Write (Yao et al. 2019); hierarchical neural story gen (Fan et al.
  2018-19).** Outline (often a flat keyword/storyline) then generate. *Contribution:*
  proves plan-as-control helps coherence. *Failure mode = DM's exact bug:* the plan
  is usually **untyped keywords, not typed state**, so consistency still leaks --
  recognition by another name.
- **Re3 / DOC (Yang et al. 2022-2023).** Recursive reprompting with a **detailed
  outline** and a learned **coherence/relevance controller** + entity/plot tracking
  over long generations. *Contribution:* engineering for long-range consistency;
  *limitation:* tracks entities/attributes (closer to v2's ontology ledger) more
  than belief/causality.
- **Dramatron (Mirowski et al. 2023).** Hierarchical co-writing: log line ->
  characters -> plot beats -> location descriptions -> dialogue, each conditioned on
  the level above. *Contribution:* a **working closed hierarchy** for LLM playwriting
  with human-rated coherence; *limitation:* hierarchy gives *structural* consistency
  but no explicit belief/causal lanes -- so the same arc-level breaks recur (authors
  reported logical gaps between beats).
- **Simulationist / agent approaches (Generative Agents, Park et al. 2023; FAtiMA;
  character HTNs).** Plot **emerges** from characters with goals, memory, and an
  appraisal/emotion model (verified: FAtiMA "character goals and emergence";
  I-Storytelling "character HTNs"). *Contribution:* rich, reactive characters and a
  built-in affect/appraisal model; *limitation:* emergent plot has **no authorial
  guarantee** -- it is the opposite pole from Propp, strong on character truth, weak
  on arc shape. A **hybrid** (authored function skeleton + simulated beat interior)
  is the recurring synthesis recommendation.
- **Surveys (Alhussain & Azmi 2021; Hou et al. 2023).** Confirm the taxonomy above
  (symbolic-planning vs. neural vs. hybrid) and the open problem: **long-range
  coherence and controllability remain unsolved by pure neural generation** -- the
  field's own statement of DM's pain.

---

## 2. Phase B -- Lane analysis: which lane retires which v2 break

Mapping each observed DM v2 break class to the lane that makes it *ungrammatical*,
ranked by gates-retired (incident weighting from the continuity corpus + 10037-BC).

| v2 break class (evidence) | Root: missing lane | Tradition that supplies it | Gates it retires |
|---|---|---|---|
| **Early reveal / presumed-dead alive** (10037-BC: Arnulf alive Ch3, "believed dead") | **Belief** `believes(obs, fact, t)` | Story Intention Graphs, epistemic logic (1d) | The entire "reveal timing" class; makes secrets/irony *authorable* not accidental |
| **Phantom reversal / double-return** (FR-525/555; 10036-BC Arnulf) | **Causal link + partial order** | IPOCL/CPOCL (1b) | `reversal_pack_gap`, much of `reoutline` gating -- a return with no authored causal antecedent is unspellable |
| **Non-composing adjacent chapters** (FR-540; fired live in 10037-BC) | **World fluent + causal link** (effects compose by construction) | Planning (1b) | `composition_gap` becomes a plan-validity check, not a post-hoc antonym scan |
| **Unresolved confrontation** (Ch6->Ch7 dropped accusation) | **Affect-debt** (open unit must terminate) | Plot Units (1c) | The "dropped thread" class v2 had *no* lane for at all |
| **Unplayable time-skip epilogue** (FR-528) | **Goal/precondition under a capped realizer** | Planning + capped-scene constraint (1b + guidance §6) | `unplayable_beat_gap` becomes "beat precondition unreachable in n turns" |
| **Intra-chapter revival** (10037-BC: die t7, on stage t8-16) | **Grain**: belief/lifecycle at **turn** grain, not chapter | any lane, carried at turn grain | the revived-actors witness becomes a *gate*, not just an instrument |

**Lane ranking (answer to RQ2).** Highest leverage first:
1. **Belief** -- unlocks the largest *unrepresentable* class (every secret/reveal/
   irony plot) and is the lane the current premise corpus is actively hitting.
2. **Causal link + partial order** -- retires the most *existing* gates
   (reversal, reoutline, composition collapse into plan validity) and delivers
   parallel-safety for free.
3. **Affect-debt** -- the only lane for the "dropped emotional thread" class, which
   v2 cannot even name today.
4. **World fluent** (DM already has a partial version: the FR-513..518 ledger).
5. **Goal/intention** -- needed for IPOCL-style motivation and for the capped-scene
   reachability test.

---

## 3. Phase C -- Spine selection

**Decision: a partial-order causal plan (IPOCL/CPOCL family) as the structural
spine, carrying a Propp-like function vocabulary as its action library, with a
drama-manager-style satisfiability/authoring check, and Plot-Unit affect-debt +
per-observer belief as typed effect lanes.**

Scored against the plan's §3 rubric (winner per criterion):

| Criterion | Winner | Why |
|---|---|---|
| Closure | Propp / planning operator library | finite action alphabet |
| Belief lane | Story Intention Graphs / epistemic logic | native per-agent belief |
| Causal lane | IPOCL/CPOCL | causal links are first-class |
| Affect lane | Plot Units | open/close affect units |
| Generation coupling | Drama manager + IPOCL | author *into* generation, prevent not detect |
| Authoring-consistency | Planning (plan exists <=> satisfiable) | unsatisfiable spec = no plan found, **before** prose |
| Grain | (none off-the-shelf) -- **DM must add turn-grain** | the 10037-BC intra-chapter gap |
| Capped-scene fit | Planning with bounded-cost actions | beat precondition reachable in <= n turns |
| Parallel-safety | IPOCL partial order | unordered events realize independently |
| Determinism (gateable) | Planning + typed lanes | plan validity is a deterministic check |

**Rejected alternatives (and why):**
- **Pure story grammar / beat sheet** -- falsified for inter-character causality
  (Black & Wilensky 1979); DM premises are *all* inter-character (feud/truce).
- **Pure neural outline-then-generate (Re3/Dramatron)** -- the strongest *engineering*
  prior art, but its plan is structural/untyped; it is what v2 already is, one
  abstraction up. Keep its **hierarchical realization technique**, reject its
  **untyped plan**.
- **Pure simulation (Generative Agents)** -- no authorial arc guarantee; excellent
  for the *beat interior*, unsafe for the *arc*. Adopt as the **realizer of a beat**,
  not the author of the plot (the hybrid).

**The synthesis in one line:** *author an IPOCL-style partial-order plan whose
actions are Propp-like functions with preconditions/effects over typed world +
belief state and affect-debt effects; check it is satisfiable (a plan exists)
before any prose; then realize each beat with the v2 turn engine (optionally
agent-simulated interior), demoted to a pure realizer.*

---

## 4. Phase D -- Minimal generative vocabulary (draft schema)

The smallest lane set that kills the *observed* break classes (over-modeling is a
named risk -- everything below is justified by a row in §2; nothing speculative).

```
STORY
  characters: [CharacterId]
  roles: {RoleId -> CharacterId}            # Propp-style, may be many-to-one
  plan: PartialOrder[FUNCTION]              # IPOCL spine; edges = causal links
  invariants: [AuthorGoal]                  # UNIVERSE-style: "Arnulf alive through ch6"

FUNCTION                                    # one authored plot beat (closed alphabet)
  id: FunctionId
  kind: enum(...)                           # finite: departure, villainy, struggle,
                                            #   reveal, return, reconciliation, ...
  actors: [CharacterId] (>=1, grounded)
  grain: enum(book | chapter | turn)        # RQ3: turn grain allowed
  preconditions:
    world:  [WorldPredicate]                # fluents (extends FR-513..518 ledger)
    belief: [BeliefPredicate]               # believes(obs, fact) / not-believes      <-- NEW lane
  effects:
    world:  [WorldDelta]                    # add/invalidate fluents (monotonic where lifecycle)
    belief: [BeliefDelta]                   # set/clear belief(obs, fact)              <-- NEW lane
    affect: [AffectDelta]                   # open/close unit(char, kind)              <-- NEW lane (Plot Units)
  causal_links: [FunctionId]                # this function establishes a precond of those
  cost_turns: int                           # capped-scene reachability bound (guidance 6)

WorldPredicate  = alive(c) | at(c, place) | faction(c, f) | rel(a, b, kind) | ...
BeliefPredicate = believes(observer, WorldPredicate) | mistaken(observer, WorldPredicate)
AffectKind      = loss | retaliation | betrayal | reconciliation | fleeting_success | hidden_blessing
```

**Authoring-consistency check (answer to RQ5), run before any prose:**
1. **Plan exists** -- a topological order of `plan` satisfies every function's
   world+belief preconditions from the initial state (this is just "the partial-order
   plan is valid"). An unsatisfiable spec yields **no plan** -- caught at authoring.
2. **Monotonic lifecycle** -- once `not alive(c)`, no later function asserts
   `alive(c)` *as world truth*; it may only assert `believes(obs, alive(c))`
   (this is precisely the floodmark distinction).
3. **Affect closure** -- every opened affect unit has a terminating function before
   THE END, or is explicitly marked an intentional open ending.
4. **Capped reachability** -- every function's preconditions are establishable within
   `cost_turns` of its chapter's budget.
5. **Belief grounding** -- a `reveal` function requires a prior `mistaken(obs, p)`
   it resolves (no reveal of a thing no one was wrong about).

**Projection (replaces reconstruction):** chapter cast = `actors of functions at
ch`; prose-exclusion set = characters `not believes(onstage_observers, alive)` AND
not yet at their reveal; protected set = `invariants`. All three are **read from
the plan**, never parsed from prose. The chapter close proposes only a **belief/
affect delta**, validated against the plan -- the world-truth lane is authored, not
re-derived.

---

## 5. Phase E -- Floodmark falsification spike

Hand-authoring the floodmark premise in the §4 vocabulary, and checking the four v2
break classes become unrepresentable.

Initial state: `alive(Arnulf)`, `believes(everyone, alive(Arnulf))`.
Author goal / invariant: `alive(Arnulf)` holds through the finale (he returns).

```
F1 villainy/flood     effects.world:  swept_away(Arnulf)            cost 2
                      effects.belief: believes(clan, not alive(Arnulf))   # PRESUMED dead
                      effects.affect: open loss(Hilde)
                      # NOTE: world truth stays alive(Arnulf); only BELIEF changes
F2 truce              pre.world: stranded(Hilde, Gunnar)
                      effects.affect: open reconciliation(Hilde, Gunnar)
F3..Fk migration      causal_links: F1 (the flood forced the move)
Fr reveal/return      pre.belief: mistaken(clan, alive(Arnulf))     # REQUIRED antecedent
                      effects.belief: believes(clan, alive(Arnulf))  # belief re-aligns to truth
                      effects.affect: close loss(Hilde) -> open guilt(Hilde)
Ff reconciliation     pre.affect: open guilt(Hilde), open reconciliation(Hilde, Gunnar)
                      effects.affect: close guilt(Hilde) [or mark intentional-open]
```

Check the four break classes:
1. **Early reveal (Ch3)** -- `Fr` has precondition `mistaken(clan, alive(Arnulf))`,
   established only by `F1`. An "Arnulf alive onstage" beat before `Fr` would need
   `believes(onstage, alive(Arnulf))`, which is **false** between F1 and Fr -> the
   beat is **unspellable**. The projection's prose-exclusion set excludes him from
   onstage cast in that interval. **Retired by construction.**
2. **Synopsis contradiction (death AND revival)** -- if the author writes
   `not alive(Arnulf)` as **world truth** in F1, then invariant `alive(Arnulf)` at
   the finale has **no valid plan** (monotonic-lifecycle rule 2) -> **authoring check
   fails before any prose**. The only satisfiable encoding is "believed dead, is
   alive" -- which is the actual premise. **The unsatisfiable spec is caught at the
   boundary**, exactly the gap the live run exposed.
3. **Unresolved confrontation (Ch6->Ch7)** -- `Fr` opens `guilt(Hilde)`; affect-closure
   (rule 3) **requires** a terminating function (`Ff`) before THE END or an explicit
   open-ending mark. A plan that drops it **fails the check**. **Retired.**
4. **Intra-chapter revival (die t7, onstage t8-16)** -- `F1.grain = turn`,
   `swept_away` effective at its turn; the turn-grain projection removes Arnulf from
   onstage cast for the remaining turns of that chapter. **Retired by grain.**

**Go/no-go:** **GO.** All four observed break classes are unrepresentable or
caught pre-prose in the candidate vocabulary, and the belief lane is load-bearing
in three of the four -- confirming the §2 lane ranking and the §0 thesis on the
worked example that originally motivated the research.

---

## 6. Best-practice summary (the answer, distilled)

1. **Author plot; do not recognize it.** Every durable tradition authors a typed
   structure and treats prose as its realization. Recognition over prose is an open
   set; authoring over a vocabulary is closed. (All traditions; the field's surveys
   state long-range coherence is unsolved by pure neural generation.)
2. **Model belief, not just ontology.** Per-observer `believes(obs, fact, t)` is the
   single highest-leverage primitive; without it, secrets, reveals, dramatic irony,
   and "presumed dead" are unrepresentable. (Story Intention Graphs; epistemic logic.)
3. **Make causality first-class and the plan a partial order.** Causal links author
   the load-bearing facts so they are never re-derived; the partial order *is*
   parallel-safety. (IPOCL/CPOCL; formalizes the v3 §8 litmus.)
4. **Carry a closed function/role alphabet.** Finite action kinds + role bindings give
   closure and orderability; reject context-free story grammars for causality.
   (Propp; Black & Wilensky 1979.)
5. **Track affect-debt as open/close units.** The only principled model of the
   "dropped emotional thread" break. (Lehnert Plot Units.)
6. **Prevent, don't detect: author into generation.** A drama-manager-style
   satisfiability check makes incoherence unspellable instead of caught downstream;
   feed protected/belief/exclusion sets into the realizer. (Drama-manager line;
   the v2 "plan-over-prose for bookkeeping only" gap.)
7. **Pick grain per lane.** Lifecycle/belief need **turn grain** inside the chapter
   where they change; the chapter-grain ledger is the proven v2 ceiling.
8. **Keep the neural realizer; demote it.** Hierarchical LLM realization (Dramatron/
   Re3) and agent simulation (Generative Agents) are excellent **beat realizers**;
   they are unsafe **plot authors**. The hybrid -- authored plan, simulated/realized
   interior -- is the field's recurring recommendation and matches DM's strength
   (v2's prose engine is good; its plot model is the gap).

---

## 7. Recommended next step (input to a v3 FR)

This research produces the **model decision** a v3 FR needs (plan §6 deliverable):

- **Spine:** IPOCL-style partial-order causal plan with a Propp-like function
  library (§3).
- **Lanes, in build order:** belief -> causal/partial-order -> affect-debt ->
  (reuse) world fluent -> goal (§2 ranking).
- **The one new primitive to prototype first:** the **belief lane**
  (`believes(observer, fact, t)`) plus the **monotonic-lifecycle authoring check** --
  together they retire the reveal-timing class and turn the floodmark
  death-and-revival contradiction into a pre-prose failure (§5 proves it on the
  motivating example).
- **Falsification harness:** the §5 spike, mechanized -- hand-authored plans for the
  existing premise corpus, asserting each historical break is unrepresentable.

**Scope guard honored (plan §7):** this is the representation decision, not a build
commitment, not prompt engineering, and not an extension of v2's recognition gates
(those are the incident record that ranked the lanes).

> **Carried forward.** The target design synthesizing this pass with the independent
> deep-research pass (`Generative Plot Model Research.md`) — including the Sabre belief
> engine, the unified SAT protocol, and the narratology fabula/syuzhet bridge — lives in
> [`plan-generative-plot-model.md`](plan-generative-plot-model.md).

---

## 8. Sources

Primary/encyclopedic, consulted this pass:
- Propp, *Morphology of the Folktale* (1928; Eng. 1958/1968) -- 31 functions, 7
  roles, fixed syntagmatic order (verified via Wikipedia, *Vladimir Propp*).
- Interactive-storytelling landscape -- drama manager / agent model / user model;
  TALE-SPIN (Meehan 1977), UNIVERSE (Lebowitz 1985), Facade (Mateas & Stern 2003),
  Automated Story Director / PAST repair, OPIATE (Proppian), FAtiMA (character goals
  + emergence), character HTNs (verified via Wikipedia, *Interactive storytelling*).

Synthesis from the established corpus (not re-fetched this pass; standard citations
for the claims made):
- Rumelhart 1975; Thorndyke 1977; Mandler & Johnson 1977 (story grammars);
  **Black & Wilensky 1979** (their falsification for causality).
- Riedl & Young 2010 (IPOCL); Ware & Young 2011-2014 (CPOCL/Glaive).
- Lehnert 1981 (Plot Units); Brewer & Lichtenstein 1982 (structural affect);
  Cheong & Young (Suspenser).
- Elson 2012 (Story Intention Graphs / DramaBank); Herman 2002 (*Story Logic*);
  doxastic/epistemic narrative logics.
- Yao et al. 2019 (Plan-and-Write); Fan et al. 2018-2019 (hierarchical neural
  story gen); Yang et al. 2022-2023 (Re3 / DOC); Mirowski et al. 2023 (Dramatron);
  Park et al. 2023 (Generative Agents); Alhussain & Azmi 2021; Hou et al. 2023
  (surveys).
