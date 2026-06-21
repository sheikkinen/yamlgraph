# Plan: A Generative Plot Model for DM v3

**Status:** Target design. The architectural decision record the v3 model FR will cite.
**Created:** 2026-06-21, synthesizing the two independent research passes:
[`research-results-modeling-plot.md`](research-results-modeling-plot.md) (repo-integrated,
incident-weighted) and [`Generative Plot Model Research.md`](Generative%20Plot%20Model%20Research.md)
(independent deep-research, primary sources). Both reached the **same spine by independent
methods** — the reconciliations from their cross-check are folded in below.
**Companion docs:** [`v3-rewrite-guidance.md`](v3-rewrite-guidance.md) (the projection thesis),
[`refactoring-plan.md`](refactoring-plan.md) (the v2 contract program this builds on),
[`continuity-issues.md`](continuity-issues.md) (the incident record that ranked the lanes).
**Buildable companion:** [`design-v3-plot-model-implementation.md`](design-v3-plot-model-implementation.md)
— this ADR keeps options open; that draft closes them (locked decisions, concrete Pydantic
schema, drafted module tree, the validator in real Python, milestones).

> **Thesis (validated twice, independently).** Plot defects are the signature of
> *recognizing an open set* — parsing discrete plot state back out of generated prose. The
> escape is a small, **closed, generative vocabulary**: author a typed plot specification,
> prove it satisfiable **before any prose**, then demote the LLM to a constrained *realizer*
> of a validated plan. v2-class continuity breaks become *ungrammatical by construction*.

---

## Management summary

**The problem.** DM v2 writes prose, then tries to *read the plot back out of it* to check
consistency. That is an unsolvable inverse problem — prose is an open set — and it is the
root cause of every recurring continuity failure: characters revealed alive too early,
deaths that un-happen, dropped confrontations, epilogues the scene engine cannot reach. More
detectors will not close the gap; the corpus shows the defect simply moves one boundary
upstream each time we add one.

**The decision.** Invert the direction of truth. **Author the plot as a small, typed,
machine-checkable specification *before* any prose is written**, prove it logically
consistent with a deterministic check, and then use the language model only to *render* a
plan that is already guaranteed correct. Two independent research efforts — one grounded in
DM's own incident history, one a literature survey with primary sources — reached this same
conclusion and the same technical spine (a partial-order *causal plan* with a *belief* lane).
That independent agreement is our confidence signal.

**Why it works.** When the plot is authored rather than recognized, whole classes of bug
become *impossible to express*, not merely *easier to catch*:

- A character cannot "return" without an authored cause — the phantom-reversal class vanishes.
- "Presumed dead but actually alive" becomes a first-class concept (the world says *alive*,
  a character *believes* dead), so the single premise that has defeated v2 all month is
  represented correctly by design.
- An unresolved emotional thread or an unreachable scene **fails an automated check before a
  word of prose is generated**, costing nothing.

**What we keep.** v2's prose quality is genuinely good and is *retained* — the language model
stays as the writer. We are not rewriting the part that works; we are giving it a correct plan
to write from. The in-flight refactors ([`refactoring-plan.md`](refactoring-plan.md)) are the
on-ramp: the same typed-contract discipline, applied to the plot model.

**Cost, risk, and the ask.** This is a **representation decision, not yet a build commitment**.
The recommended first step is a low-cost, high-information prototype: add the **belief lane**
and one consistency check, prove on the existing failing premise that the historical breaks
become unrepresentable, and only then commit to the full spine. Risk is contained by building
the smallest lane first and gating each step on a falsification test against real past failures.
Prior art de-risks it: the proposed spine is implemented and benchmarked in **Sabre** (§9a),
usable as a prototype oracle. Decisions still open (validator parameters, who authors the plan,
fine-grain cost) are enumerated in §10 for the implementing FR.

**One-line ask.** Approve a scoped prototype of the belief lane + consistency check against the
floodmark premise; success there authorizes the v3 plot-model spine.

---

## 1. What this changes — the direction of truth

v2 **reconstructs** load-bearing plot facts from the prose it generates (lifecycle inferred
at chapter close; `source_chapter` = the chapter a fact was *extracted from*). v3 **projects**
them from a plan authored up front. The narratology framing (from the deep-research pass)
names the split precisely:

| Narratology | Computational primitive | Who owns it |
|---|---|---|
| **fabula** (objective chronology) | typed world-state fluents + causal-link timeline | **authored plan** (truth) |
| **focalization** (who perceives/believes) | per-observer belief state (theory-of-mind) | **authored plan** (truth) |
| **syuzhet** (presented discourse) | the LLM-realized prose | **realizer** (derived, never read back) |

The v3 litmus from [`v3-rewrite-guidance.md`](v3-rewrite-guidance.md) §8 — *two chapters'
prose are generable without one reading the other's prose* — **is** the statement "the plan
is a partial order." The research formalizes the litmus rather than restating it.

---

## 2. The spine decision

**Decision:** an **IPOCL/CPOCL-style partial-order causal-link plan** as the structural
spine, carrying a **Propp-like finite function alphabet** as its action library, validated by
a **drama-manager-style satisfiability check** before prose, with **per-observer belief**
(Sabre-style) and **affect-debt** (Plot Units) as typed effect lanes, and the **v2 turn
engine demoted to the beat realizer**.

Both research passes selected IPOCL independently. The decisive properties:

- **Causal links author the load-bearing facts** so they are never re-derived — a return
  with no authored causal antecedent (the phantom reversal) is unspellable.
- **Partial order = parallel-safety for free** — structurally independent chapters realize
  concurrently without cross-contamination; this *is* the reconstruction litmus.
- **A plan exists ⟺ the spec is satisfiable** — an unsatisfiable premise yields *no plan*,
  caught at the authoring boundary before the LLM is ever invoked.

**Rejected (both passes agree):** pure function grammars / story grammars (context-freeness
falsified for inter-character causality, Black & Wilensky 1979 — and DM premises are *all*
inter-character feud/truce); pure neural outline-then-generate (Re3/Dramatron/DOC — strongest
realization technique, but an *untyped* plan, which is what v2 already is); pure simulation
(Generative Agents — no authorial arc guarantee). The neural and simulation lines are adopted
as **beat realizers**, never as plot authors — the hybrid both passes converge on.

---

## 3. The lanes, in build order

Ranked by the two complementary metrics the research surfaced — *unrepresentable-class size*
(repo pass) and *existing-gates-retired* (deep-research pass). They do not conflict; build
**belief and causal first**, in this order for DM's active premise corpus:

| # | Lane | Retires | Source / engine |
|---|------|---------|-----------------|
| 1 | **Belief** `believes(obs, fact, t)` | the entire reveal-timing class; makes secrets/irony/"presumed dead" *authorable*, not accidental | **Sabre** (deterministic nested belief planner) primary; Story Intention Graphs for schema/provenance |
| 2 | **Causal link + partial order** | `reversal_pack_gap`, most of reoutline gating, physical-impossibility/teleportation detectors — they collapse into plan validity | IPOCL/CPOCL |
| 3 | **Intention / goal** (frame of commitment) | unmotivated character shifts; models feud/truce as planned *thwarted* intention | CPOCL/Glaive |
| 4 | **Affect-debt** (open/close units) | the "dropped emotional thread" class v2 cannot even name today | Lehnert Plot Units |
| 5 | **World fluent** | (v2 already has a partial version) | the FR-513–518 ledger, extended |

> **Belief is the keystone lane.** It is load-bearing in three of the four motivating break
> classes, and it is the lane the current floodmark corpus is actively hitting. The single
> primitive to prototype first is `believes(observer, fact, t)` + the monotonic-lifecycle
> authoring check. **Use Sabre as the belief engine, not SIG** — SIG is post-hoc annotation
> and lacks the operational mechanics to solve open-condition flaws during generation.

---

## 4. The minimal generative vocabulary

The smallest lane set that kills the *observed* break classes. Nothing speculative — every
field is justified by a continuity incident. Over-modeling is a named risk.

```
PLOT_MODEL := ⟨ I, A, G, F, E ⟩
  I  initial state   : world fluents + per-observer belief + active affect debts
  A  agents          : [CharacterId]
  G  author goals     : invariants ("alive(Arnulf) holds through ch6")   # UNIVERSE-style
  F  functions       : the closed action library (below)
  E  causal links     : partial order; edge = "this function establishes that precondition"

FUNCTION <kind>                          # one authored beat; finite alphabet of kinds
  roles:
    subject   : CharacterId (grounded)
    target?   : CharacterId | Object | Location
    observers : [CharacterId]            # who witnesses → whose belief updates
  grain        : book | chapter | turn    # turn grain REQUIRED (intra-chapter lifecycle)
  preconditions:
    world   : [WorldPredicate]            # extends the FR-513..518 fluent ledger
    belief  : [BeliefPredicate]           # believes(subject, p) — act only on known facts
    intent  : [Goal]                      # the goal this function serves (frame of commitment)
  effects:
    world   : [WorldDelta]                # add/invalidate fluents (monotonic for lifecycle)
    belief  : [BeliefDelta]               # set/clear believes(observer, p)
    affect  : [AffectDelta]               # open/close unit(char, kind)
  cost_turns   : int                      # capped-scene reachability bound (guidance §6)

WorldPredicate  = alive(c) | at(c, place) | faction(c, f) | rel(a, b, kind) | holds(c, obj)
BeliefPredicate = believes(observer, WorldPredicate) | mistaken(observer, WorldPredicate)
AffectKind      = loss | retaliation | betrayal | reconciliation | guilt
                | fleeting_success | hidden_blessing
```

This schema is independently near-isomorphic across both research passes — the strongest
signal that it is the right minimal shape.

---

## 5. The authoring-boundary SAT check (the heart of v3)

Before any prose, the plan undergoes a deterministic satisfiability check. Fail ⇒ abort; the
LLM realizer is never invoked. This is the **union** of both passes' checks:

1. **Causal coherence** — a topological order satisfies every function's world+belief
   preconditions from `I` or a causal antecedent's effect; an unmet precondition is an *open
   condition flaw* (no plan).
2. **Monotonic lifecycle** — once `not alive(c)` is world-truth, no later function asserts
   `alive(c)` as world-truth; it may only assert `believes(obs, alive(c))`. *This is the
   floodmark distinction, mechanized.*
3. **Belief grounding** — a `reveal` function requires a prior `mistaken(obs, p)` it resolves
   (no reveal of a thing no one was wrong about).
4. **Affect closure** — every opened affect unit has a terminating function before THE END,
   or is explicitly flagged an intentional open ending.
5. **Capped reachability** — every function's preconditions are establishable within
   `cost_turns` of its chapter's budget (retires `unplayable_beat_gap`).
6. **Causal-threat resolution** — if B (scheduled between A and C) has an effect destroying a
   precondition A establishes for C, enforce temporal separation (POCL promotion/demotion);
   unresolvable ⇒ no plan.

The existing v2 detectors (`reversal_pack_gap`, `composition_gap`, `unplayable_beat_gap`)
**collapse into checks 1, 5, and 6** — recognition gates become plan-validity checks.

---

## 6. Projection replaces reconstruction

Everything v2 *reconstructed from prose* is **read from the plan**:

| Derived set | v2 (reconstructed) | v3 (projected from plan) |
|---|---|---|
| chapter cast | parsed from prose / roster filters | `actors of functions scheduled at ch` |
| prose-exclusion set | inferred lifecycle ledger | chars `not believes(onstage_observers, alive)` AND not yet at their reveal |
| protected set | bookkeeping-only precedence | `G` (author invariants), fed to **both** director and final cut |

The chapter close proposes **only a belief/affect delta**, validated against the plan — the
**world-truth lane is authored, never re-derived from the recap**. This closes the
plan-over-prose gap v2 enforced for bookkeeping but never pushed to *generation*
(the root cause behind FR-525/540/555 and the 10036/10037-BC reveals).

---

## 7. The realizer (keep v2's strength, demote it)

v2's prose engine is *good*; its plot model is the gap. So v3 keeps the turn engine as the
**syuzhet realizer**, constrained by the validated fabula:

- Each beat is realized by the v2 turn loop (optionally with an agent-simulated interior),
  prompted with the function's authored effects + the focalized belief state of its observers.
- The realizer **cannot author world-truth** — it renders what the plan already decided.
  Arnulf's grief in chapters 1–5 is rendered *because* the protagonist's belief state says
  `believes(not alive(Arnulf))`, while world-truth stays `alive`.
- This is where the v2 **turn-engine extraction** (refactoring-plan Contract B / FR-557) pays
  off: a doc-free `TurnRequest`/`TurnResult` engine is exactly the constrained realizer v3
  plugs the plan into.

---

## 8. Worked falsification — floodmark (the GO proof)

Initial: `alive(Arnulf)`, `believes(everyone, alive(Arnulf))`. Invariant `G`: `alive(Arnulf)`
through the finale.

```
F1  flood/villainy   world:  swept_away(Arnulf)           # world-truth stays alive
                     belief: believes(clan, not alive(Arnulf))   # PRESUMED, not feigned
                     affect: open loss(Hilde)
                     grain:  turn                          # effective at its turn
Fr  reveal/return    pre.belief: mistaken(clan, alive(Arnulf))   # REQUIRED antecedent (F1)
                     belief: believes(clan, alive(Arnulf))
                     affect: close loss(Hilde) → open guilt(Hilde)
Ff  reconciliation   pre.affect: open guilt(Hilde)
                     affect: close guilt(Hilde)
```

The four motivating break classes:

1. **Early reveal (Ch3)** — an "Arnulf alive onstage" beat before `Fr` needs
   `believes(onstage, alive(Arnulf))`, false between F1 and Fr → **unspellable**; the
   projection excludes him from onstage cast in that interval. *(The exact 10037-BC defect.)*
2. **Death-AND-revival synopsis contradiction** — encoding F1 as world-truth `not alive`
   makes `G` unsatisfiable (check 2) → **caught pre-prose**. The only satisfiable encoding is
   "believed dead, is alive" — the actual premise.
3. **Dropped confrontation (Ch6→Ch7)** — `Fr` opens `guilt(Hilde)`; affect closure (check 4)
   **requires** `Ff` → a plan that drops it **fails the check**.
4. **Intra-chapter revival (die t7, onstage t8–16)** — `F1.grain = turn` removes Arnulf from
   onstage cast for the chapter's remaining turns → **retired by grain**.

> **Fidelity note.** The flood is an **accident** (presumed drowned), *not* a feigned death.
> F1's false belief is a side-effect of the flood function, not a deception Arnulf intends —
> use the accidental encoding above, not a `Feigned_Death`.

**Go/no-go: GO.** All four classes are unrepresentable or caught pre-prose, and belief is
load-bearing in three of four.

---

## 9. Scope, sequencing, and what this is *not*

**Build order (prototype-first, falsification-gated):**
1. **Belief lane + monotonic-lifecycle check** (Sabre-style), proven on the floodmark spike
   mechanized — hand-authored plans for the existing premise corpus, asserting each historical
   break is unrepresentable.
2. **Causal/partial-order spine** (IPOCL) — collapses the existing reversal/composition gates
   into plan validity.
3. **Affect-debt + intention** lanes.
4. **Realizer integration** — plug the demoted turn engine (FR-557) in behind the plan.

**Depends on / reuses:**
- refactoring-plan **Contract B (FR-557)** — the doc-free turn engine *is* the realizer.
- refactoring-plan **Contract A (FR-556)** — the typed `StoryDoc` is where the projected
  cast/exclusion/protected sets land.
- The FR-513–518 ledger — the world-fluent lane already exists; v3 *extends*, not replaces it.

**This plan is NOT:**
- **Not a build commitment** — it is the representation decision a v3 model FR will cite.
- **Not prompt engineering** — the lever is the typed plan + SAT check, not bigger prompts
  (FR-553 already falsified the mass hypothesis).
- **Not an extension of v2's recognition gates** — those gates are the *incident record* that
  ranked the lanes; v3 *retires* them into plan validity rather than adding more.
- **Not a guarantee for the untyped physical/positional lane** (`continuity-issues.md` §4) —
  that remains a separate "give it a typed lane or declare it out of scope" decision; this
  plan makes it *addable* behind the same SAT boundary, not solved.

---

## 9a. Prior art and the build path

The spine is **not a research bet**. The exact composition this plan proposes — intention +
nested belief + conflict over a fluent state — is implemented, benchmarked, and citable in
**[Sabre](https://github.com/sgware/sabre)** (Stephen G. Ware, Univ. of Kentucky; AAAI AIIDE
2021). Sabre composes the three models §2–§3 name separately:

- **Riedl & Young intentionality** (characters act only on their own goals) → the intention lane.
- **Shirvani/Ware/Farrell deep theory of mind** (arbitrarily nested `believes(a, believes(b, x))`,
  with an `-el` epistemic-limit knob) → the **belief lane**, the keystone of §3.
- **Ware & Young conflict** (thwarted plans as first-class structure) → the CPOCL/feud lane.

Its problem DSL is almost line-for-line the §4 schema:

```
property alive(character): boolean;
believes(Clan, alive(Arnulf)): boolean;        // per-observer belief — the floodmark primitive
action return(...) { precondition: ...; effect: ...; consenting: Arnulf;  // intention
                     observing(c): at(c)==here; }                          // who sees → belief update
trigger see_alive(...) { ... }                 // forced belief reconciliation
utility(): alive(Arnulf);                       // author invariant G
```

Sabre's canonical example *is* the floodmark mechanic: an action is blocked "because the
character does not know" a fact — action gated on belief, the exact lever that kills the
early-reveal class (§8 class 1).

**The landscape, ranked by relevance:**

| System | What it is | Lang / License | Fit |
|---|---|---|---|
| **[Sabre](https://github.com/sgware/sabre)** | Full spine: intention + deep-ToM belief + conflict; forward heuristic search | Java 14, **GPL-3.0** | **Reference implementation / prototype oracle** |
| **[sabre-benchmarks](https://github.com/sgware/sabre-benchmarks)** | 14 problems / 27 versions (Raiders, Gramma, Western…) + PDDL originals + tech report | Java/PDDL, GPL-3.0 | **Ready-made falsification corpus** — mechanizes §8 |
| **[Glaive](https://cs.uky.edu/~sgware/projects/glaive/)** | Sabre's predecessor: intention + conflict, **PDDL 3 in/out**, no belief | Java 1.7, JAR | Superseded; its PDDL interface bridges to classical planners |
| IPOCL / Fabulist (Riedl & Young 2010) | The original algorithm | — | **No maintained public code** — Sabre/Glaive are the living descendants |
| Propp generators (Gervás; OPIATE) | Proppian function libraries | academic, unmaintained | The function alphabet is a **schema to author**, not import |
| Plot Units → AESOP (Goyal 2010) | Automatic plot-unit (affect) extraction | academic, unmaintained | The affect-debt lane has **no off-the-shelf engine** — build minimal |
| CoDi (AIIDE 2025), Dramatron, Re3/DOC | LLM director-actor / hierarchical realizers | Python, released | **Realizer-layer** prior art — confirms the §7 "demote the LLM" stance |
| unified-planning, pyperplan, Fast Downward | Classical PDDL planners in Python | Python, permissive | Causal/partial-order only — **no belief/intention/conflict** |

**The reframe this forces: DM needs a *validator*, not a *planner*.** Sabre is a *solver* — it
*searches* the multi-agent space to *find* a utility-improving story (expensive; the benchmark
harness runs 60 GB heaps). But v3 **authors** the plan with an LLM (synopsis → typed `F`/`G`)
and only needs the §5 checks to confirm the authored plan is *satisfiable*. Validation is
dramatically cheaper than search. That distinction reshapes the build path into three concrete
moves (see §10 Q1).

**License note.** Sabre is GPL-3.0 (v0.8.0; earlier releases CC BY-NC). Fine as a separate-process
research oracle (subprocess invocation is not a derivative work); a **Python reimplementation of
the §5 validator subset** is the clean production path — the model is publishable prior art, only
the code is licensed.

---

## 10. Open questions for the v3 model FR

1. **Validator, not solver — embed `unified-planning`, hand-write only the narrative checks**
   (resolved by §9a + the implementation draft; parameters open). The build path is settled:
   - **(a) Embed [`unified-planning`](https://github.com/aiplan4eu/unified-planning)** (Apache-2.0,
     pip, maintained) as the causal solver. `OneshotPlanner.solve()` *is* checks 1/5/6 — a
     returned plan proves every precondition is establishable; `UNSOLVABLE` *is* the
     open-condition flaw. Engine `aries` (MIT, partial-order/temporal) preferred; `fast-downward`
     fallback — both as separate-wheel extras, no license bleed.
   - **(b) Belief-as-fluent encoding.** Each `believes(obs, fact)` is reified as an ordinary
     boolean fluent independent of the world fluent, so a *classical* planner carries the
     epistemic lane with no native belief support. `F1` sets `bel_clan_alive_arnulf := false`
     while `alive_arnulf := true`; an early "Arnulf onstage" beat is then **unsolvable** because
     its precondition is false until `Fr` — the early-reveal class is proven unspellable by a
     real solver, not asserted. No belief-native Java planner (Sabre) needed in production.
   - **(c) Hand-write only the narrative checks** 2 (monotonic lifecycle), 3 (belief grounding),
     4 (affect closure) — invariants the planner won't enforce because belief and world are
     independent fluents by design. ~80 lines of glue, not a from-scratch POCL solver.
   - **Sabre** remains an optional separate-process *oracle* for an M0 cross-check, never a
     production dependency. Propp function libraries do not exist publicly (the GitHub `propp`
     topic has zero repos) — the function alphabet is authored, not imported.
   Open parameter: whether the Sabre cross-check is a one-off M0 confirmation or a standing CI
   oracle. **Tracked as FR-559** (the runnable floodmark spike).
2. **Authoring UX.** Who authors `F` and `G` — an LLM up-front pass (synopsis → typed plan,
   then SAT-validated with bounded retry, mirroring the v2 outline gate), or a human? Likely
   the former, with the SAT check as the deterministic gate on the LLM's plan.
3. **Grain economics.** Turn-grain belief/lifecycle for *every* character is expensive; retain
   the FR-516 top-K retrieval idea — carry fine grain only for characters with an open
   belief-gap or affect-debt.
4. **Migration path.** Can the belief lane ship as an *additive* lane on the v2 ledger (strangler-fig)
   before the full IPOCL spine, retiring the reveal-timing class first while the rest of v2 stands?
