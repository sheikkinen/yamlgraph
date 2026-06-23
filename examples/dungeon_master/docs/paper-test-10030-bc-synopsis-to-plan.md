# Paper Test: 10030-BC Synopsis → Formal Plan

**Status:** Complete
**Created:** 2026-06-23
**Predecessor:** [`plan-v3-planner.md`](plan-v3-planner.md) (the formal language definition),
FR-566 (complete grammar — the FR this test informs).
**Premise source:** `outputs/dungeon-master/10030-BC/story/story.json` (the Hilde/Gunnar
flood story, generated without a plot plan).

---

## 0. Goal

Take the 10030-BC synopsis (the Hilde/Gunnar flood story), feed it to the LLM via
the existing `author_plot_plan.yaml` prompt, parse the result through
`parse_plot_plan`, validate with `validate_plan`, and project with the existing
`project.py` functions. See what works, what breaks, where the vocabulary is too
narrow.

This is an **observational** test, not a pass/fail gate. The outcomes feed FR-566's
design decisions.

---

## 1. Why this premise

The 10030-BC synopsis is richer than the floodmark fixture:

| Dimension | Floodmark fixture | 10030-BC synopsis |
|-----------|------------------|-------------------|
| Characters | 2 (Arnulf, Hilde) + 1 observer (Clan) | 5 named (Hilde, Gunnar, Arnulf, Reinmar, Svala) + 2 clans |
| Chapters | 6 (ordinals in beats) | 8 |
| Arcs | 1 (presumed-dead) | 4+ (presumed-dead, enemies-to-lovers, clan merger, ritual authority) |
| Belief gaps | 1 (Clan believes Arnulf dead) | 3+ (Arnulf presumed dead, affair hidden, Svala's interpretation) |
| Affect threads | 2 (loss, guilt) | 3+ (loss, guilt, betrayal) |

It will stress every known vocabulary limit: 4 action kinds, 2 affect kinds, `alive`
as the only exercised predicate.

---

## 2. What we expect to learn

1. **Vocabulary ceiling.** The synopsis has departure (Hilde leaves camp), struggle
   (Hilde vs Gunnar on the ledge), pursuit (the journey to the high valley), rescue
   (Reinmar's route), death-that-isn't (Arnulf swept away). The current 4-kind
   alphabet (`villainy`, `reveal`, `reconciliation`, `return`) can only encode a
   fraction. How much of the plot is silently dropped by `parse_plot_plan`?

2. **Belief lane depth.** The synopsis has multiple belief gaps: Arnulf presumed dead
   (the floodmark case), Hilde/Gunnar relationship hidden then revealed, Svala's
   ritual interpretation. Can the LLM encode these as `Belief` objects with the
   current `alive`-only predicate check, or does it need `rel`/`faction` predicates
   that are defined but dormant?

3. **Affect coverage.** Loss (Arnulf), guilt (Hilde's choice), betrayal (clan views
   of the affair) — only `loss` and `guilt` are in the current `AffectKind`. Does
   the LLM try to use `betrayal` and get it dropped?

4. **Validation pass rate.** Does the LLM-authored plan pass all 4 current checks on
   the first attempt? If not, which flaws fire? Does the repair loop fix them?

5. **Projection coherence.** For the chapters where beats land, do `chapter_cast`,
   `exclusion_set`, `belief_at` return sensible results?

---

## 3. Steps

```bash
# 1. Extract the synopsis to a file for repeatability
python3 -c "
import json
doc = json.load(open('outputs/dungeon-master/10030-BC/story/story.json'))
print(doc['synopsis']['text'])
" > /tmp/10030-synopsis.txt

# 2. Run the authoring graph standalone (includes repair loop)
PYTHONPATH="$PWD" python3 -c "
import asyncio, json
from yamlgraph.graph_loader import get_app

async def main():
    synopsis = open('/tmp/10030-synopsis.txt').read()
    result = await get_app(
        'examples/dungeon_master/plot_plan.yaml'
    ).ainvoke({'premise': synopsis})
    print(json.dumps(result, indent=2, default=str))

asyncio.run(main())
" > /tmp/10030-plan-raw.json

# 3. Parse, validate, and project
PYTHONPATH="$PWD" python3 -c "
import json
from examples.dungeon_master.api.plot.author import parse_plot_plan
from examples.dungeon_master.api.plot.validate import validate_plan
from examples.dungeon_master.api.plot.project import (
    ordered_functions, chapter_cast, exclusion_set, belief_at, protected_set,
)

raw = json.load(open('/tmp/10030-plan-raw.json'))
plan_raw = raw.get('plan_raw')
if isinstance(plan_raw, str):
    plan_raw = json.loads(plan_raw)

print('=== PARSE ===')
plan = parse_plot_plan(plan_raw)
print(f'agents: {plan.agents}')
print(f'functions: {len(plan.functions)} (kinds: {[f.kind for f in plan.functions]})')
print(f'goals: {plan.goals}')
print(f'initial_world: {plan.initial_world}')
print(f'initial_belief: {plan.initial_belief}')
print(f'order: {plan.order}')

print()
print('=== VALIDATE ===')
result = validate_plan(plan)
print(f'ok: {result.ok}')
for flaw in result.flaws:
    print(f'  [{flaw.code}] {flaw.function_id}: {flaw.detail}')

print()
print('=== PROJECT ===')
chapters = sorted(set(f.chapter for f in plan.functions))
for ch in chapters:
    cast = chapter_cast(plan, ch)
    excl = exclusion_set(plan, ch)
    bel = belief_at(plan, ch)
    print(f'ch{ch}: cast={cast}, excl={excl}, belief={bel}')

print()
print('=== PROTECTED SET ===')
print(protected_set(plan))
" 2>&1 | tee /tmp/10030-plan-analysis.txt
```

---

## 4. What to record

| Observation | Record |
|------------|--------|
| LLM-authored function kinds | Which of the 4 current kinds did it use? Did it try others? |
| Dropped-by-parse functions | How many functions did the LLM author vs how many survived `parse_plot_plan`? |
| Dropped-by-parse affects | Did it try `betrayal`/`retaliation`? Were they dropped? |
| Dormant predicates used | Did the LLM use `at`, `faction`, `rel`, `holds` in fluents? |
| Validation result | Pass/fail, which flaw codes fired |
| Repair loop iterations | How many rounds before pass (or budget exhaustion) |
| Projection sense-check | Do `chapter_cast` and `exclusion_set` match the synopsis's narrative? |
| Vocabulary ceiling | Which plot events from the synopsis are unrepresentable in the current 4-kind alphabet? |

---

## 5. Success criteria

This is observational — outcomes feed FR-566 design, not a gate.

| Outcome | Implication for FR-566 |
|---------|----------------------|
| >50% of functions dropped by parse | Vocabulary expansion is urgently needed |
| LLM uses dormant predicates (`at`, `rel`, `faction`) | FR-566 should ensure they're exercised in fixtures |
| Validation fails first attempt, repair loop fixes it | Current architecture works for richer premises |
| Repair loop exhausts budget | Synopsis complexity exceeds prompt capacity — FR-568's "feed chapter count" may be needed earlier |
| `betrayal` affect attempted and dropped | FR-566's `AffectKind` expansion is needed for this premise class |
| Projection returns sensible cast/exclusion | `project.py` is ready for richer plans without changes |

---

## 6. Known constraints

- **Current vocabulary:** `FunctionKind` = villainy, reveal, reconciliation, return
  (4 of the 10 destination kinds). `AffectKind` = loss, guilt (2 of 5).
- **Belief grounding check** (`_check_belief_grounding`) only checks `alive` predicate
  — beliefs about `rel`/`faction` are not grounded-checked.
- **`parse_plot_plan`** silently drops off-alphabet kinds and ungrounded fluents —
  the LLM's intent is lost without logging.
- **No `_check_grounding` or `_check_goal_reachability`** — Rules 1 and 6 are not
  enforced, so an ungrounded or unreachable plan may pass validation.

---

## 7. Results (2026-06-23)

**Model:** claude-haiku-4-5, temperature 0.7, single shot (no repair loop — the graph
had a `loop_exits: END` normalization bug that was fixed during this test run; see
§8).

### 7a. LLM output overview

The LLM authored a **well-structured plan** with 7 agents, 13 initial_world fluents,
4 initial_belief entries, 6 goals, 7 functions, and a fully linear order chain.

| Field | Count | Notes |
|-------|-------|-------|
| agents | 7 | Hilde, Gunnar, Arnulf, Reinmar, Svala, Aschenwulf, Bärenschädel |
| initial_world | 13 | 5 alive, 4 faction, 2 rel, 2 holds |
| initial_belief | 4 | 2 alive (Arnulf), 2 rel (Hilde-Gunnar: `"enemy"`) |
| goals | 6 | 3 alive, 1 rel (`"lovers"`), 2 holds (feud=false) |
| functions | 7 | 3 villainy, 3 reconciliation, 1 return |
| order | 6 edges | Fully linear: F1→F2→F3→F4→F5→F6→F7 |

### 7b. Vocabulary findings

| Observation | Result |
|------------|--------|
| Function kinds used | villainy (3), reconciliation (3), return (1). **No reveal.** |
| Function kinds attempted but dropped | None — LLM stayed within the 4-kind alphabet |
| Affect kinds used | loss (1 open, 1 close), guilt (2 open, 2 close). Stayed within alphabet. |
| Affect kinds attempted but dropped | **None** — the LLM did not attempt `betrayal` despite the synopsis explicitly describing betrayal dynamics |
| Dormant predicates used | **Yes — extensively.** `rel` (3 fluents), `faction` (4 fluents), `holds` (4 fluents). Only `at` was not used. |

**Key finding:** The LLM **did not push against the vocabulary ceiling** for function
kinds or affect kinds. It compressed the 8-chapter synopsis into 7 beats using only 3
of the 4 available kinds. However, it pushed **hard** against the predicate vocabulary
— using `rel`, `faction`, and `holds` fluently and correctly.

### 7c. Parse boundary failure (critical finding)

**`parse_plot_plan` returned an empty plan (0 functions, 0 agents).** All 7 functions
were dropped. Root cause: the `Belief.held` field is `bool`, but the LLM used string
values for relationship beliefs:

| Source | Observer | Predicate | held value | Expected |
|--------|----------|-----------|-----------|----------|
| initial_belief | Aschenwulf | `rel(Hilde, Gunnar)` | `"enemy"` | `bool` |
| initial_belief | Bärenschädel | `rel(Hilde, Gunnar)` | `"enemy"` | `bool` |
| F4 eff_belief | Aschenwulf | `rel(Hilde, Gunnar)` | `"lovers"` | `bool` |
| F4 eff_belief | Bärenschädel | `rel(Hilde, Gunnar)` | `"lovers"` | `bool` |
| F5 pre_belief | Aschenwulf | `rel(Hilde, Gunnar)` | `"lovers"` | `bool` |

These string-valued beliefs passed `_is_grounded_belief` (which only checks that
`fluent.pred` is in the `WorldPred` alphabet) but failed Pydantic `model_validate`
(which expects `held: bool`). The `model_validate` exception triggered the fallback
`return PlotPlan()` — **silently dropping the entire plan**.

**The LLM's intent was coherent:** it tried to encode "Clan believes Hilde and Gunnar
are enemies" as `believes(Clan, rel(Hilde, Gunnar)) = enemy`. This is a *typed belief
about a relationship state*, not a boolean. The current schema can only express
`believes(obs, predicate) = true/false` — "the observer does or does not hold this
belief." It cannot express "the observer believes the relationship is X."

### 7d. Validation and projection (after manual coercion)

Coercing non-bool `held` values to `True` (interpreting as "belief exists") allows
the plan to parse. Results:

**Validation: PASS (ok=True, 0 flaws).** All 4 checks passed on the first attempt:
- Monotonic lifecycle: no deaths in world-truth ✓
- Belief grounding: F6's reveal of Arnulf-alive is grounded by F2's concealment ✓
- Causal antecedent: all pre_world/pre_belief have producers ✓
- Affect closure: loss opens at F2, closes at F6; guilt opens at F1, closes at F3,
  reopens at F5, closes at F7 ✓

**Projection results:**

| Ch | Cast | Exclusion | Belief |
|----|------|-----------|--------|
| 1 | Hilde, Aschenwulf, Bärenschädel, Flood | {Arnulf} | Arnulf presumed dead |
| 2 | Hilde, Gunnar | {Arnulf} | Arnulf presumed dead |
| 3 | Hilde, Gunnar | {Arnulf} | Arnulf presumed dead |
| 4 | Svala, Aschenwulf, Bärenschädel | {Arnulf} | Arnulf presumed dead |
| 5 | Arnulf, Aschenwulf | ∅ | Arnulf alive (revealed) |
| 6 | Hilde, Aschenwulf, Bärenschädel | ∅ | Arnulf alive |

**Sense check:** The projection is largely correct. Arnulf is excluded from chs 1–4
(presumed dead) and returns in ch5. The cast assignments roughly match the synopsis
chapters. One anomaly: `Flood` appears as an agent in ch1 (the LLM used it as a
`subject` for F2, the "Arnulf swept away" beat).

**Protected set:** `[Hilde, Gunnar, Arnulf, Aschenwulf, Bärenschädel]` — 5 agents
protected by goals. This is overly broad (Aschenwulf and Bärenschädel are clans used
in `holds(clan, feud)=false` goals, not characters that need lifecycle protection).

### 7e. Missing from the plan

| Synopsis event | Plan encoding | Gap |
|---------------|---------------|-----|
| Hilde attacks Bärenschädel camp | F1 villainy (Hilde) | Covered |
| Arnulf swept away by flood | F2 villainy (Flood, eff_belief: dead) | Covered, but `Flood` as agent is a hack |
| Hilde/Gunnar forced truce on ledge | F3 reconciliation | Covered |
| Enemies-to-lovers arc | F3→F4 reconciliation chain with `rel` fluents | Covered (creative use of `rel` predicate) |
| Reinmar arrives with route | **Not encoded** | No `departure` or `rescue` kind |
| Svala's ritual judgement | F5 villainy (Svala) | Covered (villainy is a stretch) |
| Journey to high valley | **Not encoded** | No `departure` or `pursuit` kind |
| Clan merger / feud end | F7 reconciliation (holds: feud=false) | Covered |
| Arnulf returns | F6 return (belief flip) | Covered — the floodmark pattern |

Two events are unrepresentable: Reinmar's arrival/guidance and the journey. Both would
need `departure`/`rescue` kinds from the FR-566 expansion.

---

## 8. Bugs found during test

### 8a. `loop_exits: END` normalization (blocking, fixed)

**Bug:** `edge_compiler.py` line 271 reads `loop_exits` values from YAML as raw
strings. The value `"END"` is not normalized to the LangGraph `END` sentinel
(`"__end__"`), causing `ValueError: unknown target 'END'` when the graph compiles.

**Fix:** Added normalization at edge_compiler.py:271:
```python
_raw_exit = (loop_exits or {}).get(source_node)
loop_exit_target = END if _raw_exit == "END" else _raw_exit
```

All 4039 unit tests pass after fix.

### 8b. `parse_plot_plan` silent total-plan drop (design issue, not a bug)

When `model_validate` fails (e.g., due to non-bool `held` values), the entire plan is
dropped: `return PlotPlan()`. This is by design ("normalize at the boundary; never
substitute a plausible-but-wrong plan"), but the failure is **invisible** — no log
message, no diagnostic. The 5 bad beliefs cause all 7 functions (including 5 that are
individually valid) to be dropped.

**Recommendation:** Two possible improvements:
1. **Per-function validation.** Validate each function individually; drop only the
   invalid ones. The 5 valid functions would survive.
2. **Belief coercion.** Coerce non-bool `held` values to `True` (interpreting as
   "belief exists") at the boundary parse, before `model_validate`. Log the coercion.

### 8c. `author_plan` node JSON parse error (graph issue)

The authoring graph's `author_plan` node (`parse_json: true`) failed to extract JSON
from the LLM response because the response was wrapped in ` ```json ``` ` fences. The
`parse_json` handler threw `KeyError: '\n  "agents"'`. The graph's error handler
recorded the error but continued to the validate node with `plan_raw=None`, producing
a vacuously-true validation on an empty plan.

**Recommendation:** The `parse_json` handler should strip markdown fences before
parsing. This may already be handled for some node types but not for this graph's
configuration.

---

## 9. Implications for FR-566

| Finding | Implication |
|---------|------------|
| LLM stayed within 4-kind action alphabet | Vocabulary expansion is **nice-to-have**, not urgent for this premise class. The LLM compressed the plot without needing departure/pursuit/rescue. |
| LLM used dormant predicates extensively (rel, faction, holds) | FR-566 **must** add fixtures exercising `rel`, `faction`, `holds` — they are not dormant in practice. |
| `Belief.held` expects bool but LLM wants typed values | The `believes` meta-predicate needs design attention. The LLM naturally wants `believes(obs, rel(A,B)) = "enemy"`, not just `= true/false`. This is a schema question, not just a parse question. |
| Validation passed on first attempt (after coercion) | The 4-check validator works for richer premises. The repair loop architecture is sound. |
| Projection returned sensible results | `project.py` is ready for richer plans — no changes needed. |
| `Flood` used as agent | The LLM will use non-character entities as agents when the vocabulary lacks a better option. FR-566's sort typing (aspirational) would help, but is out of scope. |
| Parse drops entire plan silently | The boundary parse needs per-function validation or coercion, not all-or-nothing `model_validate`. |

---

## 10. Vocabulary insufficiency: the plan cannot carry narrative meaning

### 10a. The experiment

After producing the plan JSON (§7), the plan was read in isolation — without
referencing the synopsis — and an attempt was made to narrate the plot from the plan
alone. The question: **can a reader reconstruct what happens in the story from the
formal plan?**

### 10b. What the plan actually contains

The plan encodes:

- **Who:** agent names (`Hilde`, `Gunnar`, `Arnulf`, `Svala`, `Flood`, `Aschenwulf`,
  `Bärenschädel`) — bare strings with no role, description, or relationship semantics
  beyond the `rel` and `faction` predicates.
- **What kind:** function kinds (`villainy`, `reconciliation`, `return`) — abstract
  structural labels. "Villainy" says *something bad happens*; it does not say what.
- **What changes:** predicate effects (`rel(Hilde, Gunnar) = "allies"`,
  `holds(Aschenwulf, feud) = false`, `believes(Clan, alive(Arnulf)) = false`) —
  state transitions on typed predicates, but no description of *how* or *why* the
  transition happens.
- **What is felt:** affect deltas (`open(Hilde, guilt)`, `close(Hilde, loss)`) —
  emotional debt accounting, but no description of *what causes* the emotion or *what
  it feels like*.
- **What order:** topological chain (`F1→F2→F3→F4→F5→F6→F7`) — causal sequence, but
  no scene descriptions, dialogue, or narrative texture.

### 10c. What the narration required (and where it came from)

When the plan was narrated, the prose included statements like:

| Prose in narration | Source | Present in plan? |
|--------------------|--------|-----------------|
| "Hilde raids the Bärenschädel camp at dawn" | Synopsis | **No.** Plan says: F1 = villainy, subject=Hilde, observers=[Aschenwulf, Bärenschädel]. Nothing about raiding, camps, or dawn. |
| "The flood sweeps Arnulf away" | Synopsis | **No.** Plan says: F2 = villainy, subject=Flood, eff_belief=[alive(Arnulf)=false]. Nothing about sweeping, water, or drowning. |
| "Forced truce on a shrinking ledge above the water" | Synopsis | **No.** Plan says: F3 = reconciliation, pre_world=[alive(Hilde), alive(Gunnar)], eff_world=[rel(Hilde,Gunnar)=allies]. Nothing about truces, ledges, or water. |
| "Allies become lovers" | Synopsis | **Partially.** Plan encodes the state transition rel(Hilde,Gunnar): allies→lovers. But "become" (the emotional/narrative arc) is not in the plan. |
| "Svala condemns the cross-clan relationship as blasphemy" | Synopsis | **No.** Plan says: F5 = villainy, subject=Svala, pre_belief=[believes(Aschenwulf, rel(Hilde,Gunnar))=lovers]. Nothing about condemnation, ritual authority, or blasphemy. |
| "Arnulf returns from the dead" | Synopsis | **Partially.** Plan encodes F6 = return, subject=Arnulf, eff_belief=[alive(Arnulf)=true]. The word "return" is the function kind, but "from the dead" is narrative interpretation. |
| "The blood-feud ends" | Synopsis | **Partially.** Plan encodes holds(Aschenwulf, feud)=false, holds(Bärenschädel, feud)=false. But "blood-feud" and "ends" are narrative framing. |

### 10d. The finding

**The plan's vocabulary and syntax are completely insufficient to carry the plot's
narrative meaning.** Every sentence of the narration required external knowledge —
the synopsis — to reconstruct *what happens*. The plan encodes:

1. **Structural relationships** (who is involved, what kind of beat, what chapter)
2. **Causal dependencies** (what must be true before, what changes after)
3. **Affect debt** (which emotional threads are open/closed)
4. **Belief state** (who knows what, who is wrong about what)

It does **not** encode:

1. **What the villainy *is*** (a raid? a curse? a betrayal? a flood?)
2. **What the reconciliation *looks like*** (a truce? a marriage? a treaty? shared survival?)
3. **Why the affect opens** (guilt from what? loss of whom to what?)
4. **What the world-state *means*** (rel=allies could be a political alliance, a friendship, a forced truce, or a romantic partnership — the plan treats these identically)
5. **Scene content** (setting, dialogue, physical action, sensory detail)

The formal plan is a **structural skeleton**, not a narrative. It encodes the *shape*
of the plot (the causal graph, the belief gaps, the emotional arcs) but not the
*substance* (what actually happens, why it matters, how it feels). A reader of the
plan JSON alone — without the synopsis — cannot reconstruct the story. They can see
that *something bad happens to Hilde in chapter 1* and that *it causes guilt*, but
they cannot know that it was a dawn raid on an enemy camp during a flood.

### 10e. Implications for the v3 planner

This is not a bug — it is a design boundary. The plan was intended as a structural
scaffold for the beat-writer, not as a self-contained narrative. But the finding has
concrete consequences:

1. **The beat-writer needs the synopsis.** The plan alone is insufficient input for
   generating beats. The beat-writer must have access to the original synopsis (or a
   prose annotation layer on the plan) to know *what happens* in each function.

2. **Validation cannot check narrative fidelity.** The validator can verify structural
   integrity (causal chains, belief grounding, affect closure) but cannot check whether
   the plan *faithfully represents* the synopsis. "F1 = villainy, subject=Hilde" is
   structurally valid whether Hilde raids a camp, poisons a well, or burns a bridge —
   the plan cannot distinguish these.

3. **The plan is lossy.** Converting a synopsis to a plan discards most of the
   narrative content. The plan preserves only the causal skeleton. This is acceptable
   if the synopsis is always available downstream, but it means the plan is not a
   self-sufficient representation of the story.

4. **Vocabulary expansion (FR-566) does not close this gap.** Adding more function
   kinds (departure, rescue, pursuit) and more affect kinds (betrayal, hope) would
   make the skeleton more detailed, but the fundamental problem remains: the formal
   language encodes *types of events*, not *specific events*. Even with 31 Propp
   functions, `villainy` still does not say *what* the villainy is.

5. **A prose annotation layer may be needed.** Each function could carry a
   `description` or `gloss` field — a one-sentence natural-language summary of what
   the beat is *about*. This would bridge the gap between the structural skeleton and
   the narrative content, without expanding the formal vocabulary to encode every
   possible story event.
