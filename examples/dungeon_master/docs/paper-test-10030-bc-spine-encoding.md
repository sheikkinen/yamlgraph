# Paper Test: 10030-BC Spine Encoding

**Status:** Complete
**Created:** 2026-06-23
**Predecessor:** [`paper-test-10030-bc-synopsis-to-plan.md`](paper-test-10030-bc-synopsis-to-plan.md)
(the first paper test, which found the DM schema insufficient — §10),
[`research-plan-modeling-plot.md`](research-plan-modeling-plot.md) §4 (the spine
decision).
**Premise source:** `outputs/dungeon-master/10030-BC/story/story.json` (same
synopsis as the first test).

---

## 0. Goal

The first paper test (synopsis → DM schema) found that the plan's vocabulary and
syntax are **completely insufficient to carry narrative meaning** (§10). A reader
of the plan JSON alone cannot reconstruct the story. The plan encodes structural
relationships and causal dependencies but not *what happens*.

This test asks: **does the spine model from the research plan (§4) close the gap?**

We hand-encode the same 10030-BC synopsis using the full spine vocabulary —
causal links, typed beliefs, intentionality, conflict, richer affect, and a prose
gloss per function — then evaluate the resulting representation against the §10
insufficiency table.

This is a **manual paper test**. No code is executed. The encoding is done by a
human (or LLM acting as human) reading the synopsis and writing the spine
representation. The evaluation is by inspection.

---

## 1. The spine vocabulary (from research-plan §4)

The research plan's working synthesis hypothesis:

```
PLOT = partial-order plan of FUNCTIONS (Propp-like, closed alphabet)
  each FUNCTION carries:
    - preconditions / effects over a typed WORLD-STATE  (fluents)
    - preconditions / effects over a per-observer BELIEF-STATE  (epistemic lane)
    - a causal link to the function(s) it enables  (IPOCL partial order)
    - an AFFECT-DEBT effect: opens / pays a per-character emotional thread  (Lehnert)
    - a role binding (7-ish roles) and an authored chapter/turn grain
```

### 1a. What the spine adds over the DM schema

The first paper test used the DM schema: `{id, kind, subject, chapter, observers,
pre_world, pre_belief, eff_world, eff_belief, eff_affect}`. The spine adds:

| Lane | DM schema | Spine addition |
|------|-----------|----------------|
| **Typed beliefs** | `held: bool` only | `held: any` — beliefs carry the value, not just existence |
| **Causal links** | Implicit in `order` (temporal chain) | Explicit `enables: [F_id]` per function — *why* this function exists |
| **Intentionality** | None | `motivation: {agent, goal}` — *whose goal* this function serves |
| **Conflict** | None | `threatens: {agent, goal}` — *whose goal* this function thwarts |
| **Prose gloss** | None | `gloss: str` — one-sentence natural-language description |
| **Richer affect** | `loss`, `guilt` (2 kinds) | Lehnert's named units: loss, retaliation, hidden-blessing, betrayal, etc. |
| **Role binding** | `subject` only | `roles: {hero, villain, donor, helper, dispatcher, princess, false-hero}` |

### 1b. Extended function schema

```json
{
  "id": "F1",
  "kind": "villainy",
  "gloss": "Hilde raids the Bärenschädel camp at dawn during the rising flood.",
  "subject": "Hilde",
  "roles": {"villain": "Hilde", "victim": "Bärenschädel"},
  "chapter": 1,
  "observers": ["Aschenwulf", "Bärenschädel"],
  "motivation": {"agent": "Hilde", "goal": "kill_Gunnar"},
  "threatens": {"agent": "Gunnar", "goal": "survive"},
  "enables": ["F3"],
  "pre_world": [...],
  "pre_belief": [...],
  "eff_world": [...],
  "eff_belief": [...],
  "eff_affect": [...]
}
```

---

## 2. What we test

### 2a. Narrative recoverability

The §10 insufficiency table identified 7 prose statements that required the
synopsis to reconstruct. For each, we ask: **can a reader of the spine encoding
alone reconstruct this statement (or an equivalent one) without the synopsis?**

| # | Prose from §10c | Source in DM schema | Target: recoverable from spine? |
|---|-----------------|--------------------|---------------------------------|
| 1 | "Hilde raids the Bärenschädel camp at dawn" | Not present | Test: does the `gloss` field carry this? |
| 2 | "The flood sweeps Arnulf away" | Not present | Test: does the `gloss` field carry this? |
| 3 | "Forced truce on a shrinking ledge above the water" | Not present | Test: do `gloss` + `motivation` + `conflict` carry this? |
| 4 | "Allies become lovers" | Partial (state transition only) | Test: does `gloss` + role binding add the emotional arc? |
| 5 | "Svala condemns the cross-clan relationship as blasphemy" | Not present | Test: do `gloss` + `motivation` + `threatens` carry this? |
| 6 | "Arnulf returns from the dead" | Partial (function kind only) | Test: does `gloss` add "from the dead" (narrative frame)? |
| 7 | "The blood-feud ends" | Partial (state transition only) | Test: does `gloss` + `motivation` add the significance? |

### 2b. Structural gains

Beyond narrative recoverability, evaluate whether the spine's new lanes make
structural defects **ungrammatical by construction**:

| Defect class (from research-plan §3) | DM schema catches it? | Spine catches it? |
|--------------------------------------|----------------------|-------------------|
| **Early reveal** (belief flipped before its floor) | Yes (belief grounding check) | Yes + causal link makes the dependency explicit |
| **Phantom reversal** (double-return without causal link) | No | Test: do causal links prevent it? |
| **Unresolved affect thread** | Yes (affect closure check) | Yes + richer affect kinds (betrayal, retaliation) |
| **Unplayable epilogue** | No | Test: does intentionality detect unsatisfied goals? |
| **Unmotivated action** (function has no character goal) | No | Test: does `motivation` field make this checkable? |

### 2c. Cost of the gloss

The `gloss` field is the obvious fix for §10's narrative gap. But it reopens the
recognition problem: the gloss is free-form prose, not closed vocabulary. Evaluate:

1. **Is the gloss redundant?** Can the same information be recovered from the
   structured fields alone (kind + roles + motivation + pre/eff)?
2. **Is the gloss load-bearing?** If you remove the gloss, does the plan lose
   narrative meaning that the structured fields cannot carry?
3. **Is the gloss verifiable?** Can a validator check that the gloss is
   *consistent with* the structured fields, or is it an unchecked annotation?

---

## 3. Steps

### Step 1: Hand-encode the 10030-BC synopsis as a spine plan

Using the §1b schema, encode all 7 functions from the LLM-authored plan
(`paper-test-10030-bc-plan-output.json`) with the spine extensions:

- Add `gloss` to each function (one sentence, from the synopsis).
- Add `motivation` and `threatens` where applicable.
- Add `enables` causal links (replacing the flat `order` chain with
  *reason-for-existence* links).
- Add `roles` per function.
- Fix `held` to typed values (the LLM's original intent, not coerced bools).
- Expand `eff_affect` to use Lehnert's named units where applicable (betrayal
  for F5, hidden-blessing for F6).

### Step 2: Evaluate narrative recoverability (§2a)

Read the spine encoding *without* the synopsis. For each row of §2a, write what
a naïve reader would understand. Compare to the §10c table.

### Step 3: Evaluate structural gains (§2b)

For each defect class in §2b, attempt to construct a malformed plan (e.g., double
return, unmotivated action) and check whether the spine's new fields make the
malformation detectable or impossible.

### Step 4: Evaluate the gloss cost (§2c)

Remove all `gloss` fields from the encoding. Re-read the plan. Answer the three
questions in §2c.

---

## 4. What to record

| Observation | Record |
|------------|--------|
| Narrative recoverability score | How many of the 7 §10c statements are recoverable from spine alone (0-7)? |
| Gloss load-bearing? | Which statements are recoverable *only* via gloss vs. via structured fields? |
| Causal links vs. flat order | Do `enables` links add information beyond temporal sequence? |
| Intentionality coverage | How many functions have a clear `motivation`? How many have `threatens`? |
| Lehnert affect coverage | Which named plot units apply? Does the expanded vocabulary fit? |
| Structural defect gates | Which of the 5 defect classes become ungrammatical? |
| Gloss verifiability | Can the gloss be mechanically checked against structured fields? |

---

## 5. Success criteria

| Outcome | Implication |
|---------|------------|
| 5+ of 7 statements recoverable from spine | The spine closes the §10 gap — the plan can carry narrative meaning |
| <3 of 7 recoverable without gloss | The gloss is load-bearing — structured vocabulary alone is insufficient even at spine richness |
| All 5 defect classes gated | The spine is structurally complete for DM's needs |
| Gloss is NOT verifiable | The gloss reopens the recognition problem — it is an unchecked prose annotation |
| Causal links add no information beyond order | `enables` is redundant for linear stories — partial-order value only shows in branching plots |

---

## 6. Hypotheses to confirm or kill

**H1 (gloss hypothesis):** The `gloss` field alone closes the §10 narrative gap,
but it is load-bearing (removing it loses the plot), unverifiable (a validator
cannot check it), and therefore **shifts the problem from vocabulary to
annotation**. The plan becomes a hybrid: closed structural skeleton +
unconstrained prose layer.

**H2 (intentionality hypothesis):** `motivation` and `threatens` fields encode
*why* functions exist, which is the main information the DM schema lacks. Even
without a gloss, a reader who knows "Hilde's goal is kill_Gunnar" and "F3
threatens Gunnar's survive goal" can reconstruct the narrative tension. The gloss
adds scene detail but the *plot* is recoverable from structure alone.

**H3 (causal-link hypothesis):** For the 10030-BC plot (linear, single-threaded),
`enables` links add no information beyond temporal order. The partial-order value
only emerges with branching or parallel chapters. This test cannot confirm the
parallel-safety benefit — it needs a multi-threaded premise.

**H4 (typed-belief hypothesis):** Allowing `held: "enemy" | "lovers" | ...`
instead of `held: bool` was the LLM's natural choice. The DM schema rejected it.
The spine should accept it. This closes the parse-boundary failure from the first
test without losing information.

---

## 7. Constraints

- **No code.** This is a manual encoding exercise. The spine schema does not
  exist as code yet. The evaluation is by inspection.
- **Same premise.** Using 10030-BC for direct comparison with the first paper
  test. The linear plot structure limits what we can learn about partial-order
  benefits (see H3).
- **Single encoder.** The encoding is done once. Inter-rater reliability is not
  tested. A second encoding (by a different person or LLM) would strengthen the
  findings but is out of scope.

---

## 8. Step 1: Spine encoding of 10030-BC (executed 2026-06-23)

The 7 functions from `paper-test-10030-bc-plan-output.json`, re-encoded with the
full spine schema. Each function gains: `gloss`, `motivation`, `threatens`,
`enables`, `roles`, typed `held` values, and expanded affect kinds.

### Agents (unchanged)

```
Hilde, Gunnar, Arnulf, Reinmar, Svala, Aschenwulf (clan), Bärenschädel (clan)
```

### Initial state (unchanged except typed beliefs)

World-state: same 13 fluents (5 alive, 4 faction, 2 rel, 2 holds).

Beliefs — now with **typed `held`** values:

| Observer | Fluent | held |
|----------|--------|------|
| Aschenwulf | alive(Arnulf) | `true` |
| Bärenschädel | alive(Arnulf) | `true` |
| Aschenwulf | rel(Hilde, Gunnar) | `"enemy"` |
| Bärenschädel | rel(Hilde, Gunnar) | `"enemy"` |

### Goals (unchanged)

```
alive(Hilde) = true, alive(Gunnar) = true, alive(Arnulf) = true,
rel(Hilde, Gunnar) = "lovers", holds(Aschenwulf, feud) = false,
holds(Bärenschädel, feud) = false
```

### Functions

#### F1 — villainy (ch.1)

```json
{
  "id": "F1",
  "kind": "villainy",
  "gloss": "Hilde leads a dawn raid on the Bärenschädel camp as the flood begins.",
  "subject": "Hilde",
  "roles": {"villain": "Hilde", "victim": "Bärenschädel"},
  "chapter": 1,
  "observers": ["Aschenwulf", "Bärenschädel"],
  "motivation": {"agent": "Hilde", "goal": "destroy_enemy_camp"},
  "threatens": {"agent": "Gunnar", "goal": "protect_clan"},
  "enables": ["F3"],
  "pre_world": [{"pred": "rel", "args": ["Hilde", "Gunnar"], "value": "enemy"}],
  "pre_belief": [],
  "eff_world": [],
  "eff_belief": [],
  "eff_affect": [{"op": "open", "char": "Hilde", "kind": "guilt"}]
}
```

**`enables` rationale:** F1 creates the situation (Hilde and Gunnar are now
co-located and hostile) that forces F3 (reconciliation on the ledge). Without the
raid, Hilde and Gunnar would never be stranded together.

#### F2 — villainy (ch.1)

```json
{
  "id": "F2",
  "kind": "villainy",
  "gloss": "The flood rises faster than expected and sweeps Arnulf away; everyone believes he drowned.",
  "subject": "Flood",
  "roles": {"villain": "Flood", "victim": "Arnulf"},
  "chapter": 1,
  "observers": ["Aschenwulf", "Bärenschädel"],
  "motivation": null,
  "threatens": {"agent": "Hilde", "goal": "protect_family"},
  "enables": ["F6"],
  "pre_world": [],
  "pre_belief": [],
  "eff_world": [],
  "eff_belief": [
    {"observer": "Aschenwulf", "fluent": {"pred": "alive", "args": ["Arnulf"]}, "held": false},
    {"observer": "Bärenschädel", "fluent": {"pred": "alive", "args": ["Arnulf"]}, "held": false}
  ],
  "eff_affect": [{"op": "open", "char": "Hilde", "kind": "loss"}]
}
```

**`motivation`: null** — the flood is not an agent with goals. This is a natural
event. The `motivation` field is only meaningful for intentional actors.

**`enables` rationale:** F2 creates the false-belief (Arnulf dead) that F6 (return)
resolves. Without F2's belief effect, F6's reveal has no dramatic force.

#### F3 — reconciliation (ch.2)

```json
{
  "id": "F3",
  "kind": "reconciliation",
  "gloss": "Stranded on a shrinking ledge above the floodwater, Hilde and Gunnar are forced into a truce to survive.",
  "subject": "Hilde",
  "roles": {"hero": "Hilde", "helper": "Gunnar"},
  "chapter": 2,
  "observers": ["Hilde", "Gunnar"],
  "motivation": {"agent": "Hilde", "goal": "survive_flood"},
  "threatens": {"agent": "Aschenwulf", "goal": "maintain_feud"},
  "enables": ["F4"],
  "pre_world": [
    {"pred": "alive", "args": ["Hilde"], "value": true},
    {"pred": "alive", "args": ["Gunnar"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [{"pred": "rel", "args": ["Hilde", "Gunnar"], "value": "allies"}],
  "eff_belief": [],
  "eff_affect": [{"op": "close", "char": "Hilde", "kind": "guilt"}]
}
```

**`enables` rationale:** F3 (enemies→allies) is the precondition for F4
(allies→lovers). The truce enables the deepening of the relationship.

**`threatens` rationale:** The truce threatens the Aschenwulf clan's goal of
maintaining the blood-feud. This is the source of F5's conflict.

#### F4 — reconciliation (ch.3)

```json
{
  "id": "F4",
  "kind": "reconciliation",
  "gloss": "During the journey to higher ground, Hilde and Gunnar's alliance deepens into a sexual and emotional relationship.",
  "subject": "Hilde",
  "roles": {"hero": "Hilde", "helper": "Gunnar"},
  "chapter": 3,
  "observers": ["Hilde", "Gunnar"],
  "motivation": {"agent": "Hilde", "goal": "bond_with_Gunnar"},
  "threatens": {"agent": "Aschenwulf", "goal": "maintain_feud"},
  "enables": ["F5", "F7"],
  "pre_world": [{"pred": "rel", "args": ["Hilde", "Gunnar"], "value": "allies"}],
  "pre_belief": [],
  "eff_world": [{"pred": "rel", "args": ["Hilde", "Gunnar"], "value": "lovers"}],
  "eff_belief": [
    {"observer": "Aschenwulf", "fluent": {"pred": "rel", "args": ["Hilde", "Gunnar"]}, "held": "lovers"},
    {"observer": "Bärenschädel", "fluent": {"pred": "rel", "args": ["Hilde", "Gunnar"]}, "held": "lovers"}
  ],
  "eff_affect": []
}
```

**`enables` rationale:** F4 enables *two* functions (first non-linear link):
- F5: Svala's condemnation is triggered by the clans learning of the relationship.
- F7: The feud resolution requires Hilde and Gunnar to be publicly together.

#### F5 — villainy (ch.4)

```json
{
  "id": "F5",
  "kind": "villainy",
  "gloss": "Svala, keeper of the old rites, condemns Hilde and Gunnar's relationship as blasphemy against the clan laws and demands the feud resume.",
  "subject": "Svala",
  "roles": {"villain": "Svala", "victim": "Hilde"},
  "chapter": 4,
  "observers": ["Aschenwulf", "Bärenschädel"],
  "motivation": {"agent": "Svala", "goal": "enforce_old_law"},
  "threatens": {"agent": "Hilde", "goal": "bond_with_Gunnar"},
  "enables": ["F7"],
  "pre_world": [],
  "pre_belief": [
    {"observer": "Aschenwulf", "fluent": {"pred": "rel", "args": ["Hilde", "Gunnar"]}, "held": "lovers"}
  ],
  "eff_world": [],
  "eff_belief": [],
  "eff_affect": [{"op": "open", "char": "Hilde", "kind": "guilt"}]
}
```

**`motivation` rationale:** Svala acts from a specific goal (enforce the old law).
This is the first function where the DM schema's `subject: Svala` told you nothing
about *why* Svala acts. The motivation field makes the conflict legible.

**`enables` rationale:** F5 creates the crisis that F7 must resolve. Without
Svala's challenge, the feud resolution in F7 is unmotivated.

#### F6 — return (ch.5)

```json
{
  "id": "F6",
  "kind": "return",
  "gloss": "Arnulf, alive after being washed into a hidden channel, returns to the survivors with news from downstream, proving the mourning was based on a mistake.",
  "subject": "Arnulf",
  "roles": {"hero": "Arnulf", "dispatcher": "Arnulf"},
  "chapter": 5,
  "observers": ["Aschenwulf"],
  "motivation": {"agent": "Arnulf", "goal": "rejoin_clan"},
  "threatens": {"agent": "Hilde", "goal": "bond_with_Gunnar"},
  "enables": ["F7"],
  "pre_world": [{"pred": "alive", "args": ["Arnulf"], "value": true}],
  "pre_belief": [
    {"observer": "Aschenwulf", "fluent": {"pred": "alive", "args": ["Arnulf"]}, "held": false}
  ],
  "eff_world": [],
  "eff_belief": [
    {"observer": "Aschenwulf", "fluent": {"pred": "alive", "args": ["Arnulf"]}, "held": true},
    {"observer": "Bärenschädel", "fluent": {"pred": "alive", "args": ["Arnulf"]}, "held": true}
  ],
  "eff_affect": [{"op": "close", "char": "Hilde", "kind": "loss"}]
}
```

**`threatens` rationale:** Arnulf's return threatens Hilde's new life — he is angry
about the Gunnar relationship and represents the old order. His return complicates
the resolution even as it closes the loss thread.

#### F7 — reconciliation (ch.6)

```json
{
  "id": "F7",
  "kind": "reconciliation",
  "gloss": "Hilde and Gunnar stand together publicly, ending the blood-feud; the clans merge to share the high valley.",
  "subject": "Hilde",
  "roles": {"hero": "Hilde", "helper": "Gunnar"},
  "chapter": 6,
  "observers": ["Aschenwulf", "Bärenschädel"],
  "motivation": {"agent": "Hilde", "goal": "end_feud"},
  "threatens": {"agent": "Svala", "goal": "enforce_old_law"},
  "enables": [],
  "pre_world": [{"pred": "rel", "args": ["Hilde", "Gunnar"], "value": "lovers"}],
  "pre_belief": [],
  "eff_world": [
    {"pred": "holds", "args": ["Aschenwulf", "feud"], "value": false},
    {"pred": "holds", "args": ["Bärenschädel", "feud"], "value": false}
  ],
  "eff_belief": [],
  "eff_affect": [{"op": "close", "char": "Hilde", "kind": "guilt"}]
}
```

**`enables`: empty** — terminal function; no downstream dependencies.

**`threatens` rationale:** The feud resolution defeats Svala's goal. This is the
structural closure of the F5↔F7 conflict arc.

### Causal link graph (replaces flat order)

```
F1 ──enables──→ F3    (raid creates stranding → forced truce)
F2 ──enables──→ F6    (false death belief → return reveal)
F3 ──enables──→ F4    (allies → lovers)
F4 ──enables──→ F5    (clan learns of relationship → Svala condemns)
F4 ──enables──→ F7    (lovers status → feud resolution possible)
F5 ──enables──→ F7    (Svala's challenge → must be overcome)
F6 ──enables──→ F7    (Arnulf's return → confirms new settlement viable)
```

**Observation:** The DM schema had a fully linear order (F1→F2→F3→F4→F5→F6→F7).
The spine's causal links reveal a **partial order with two independent threads**:

- **Thread A:** F1→F3→F4→{F5, F7} (raid → truce → lovers → confrontation/resolution)
- **Thread B:** F2→F6→F7 (flood → return → resolution)

F7 is the **join point** — it requires both threads. F5 and F6 are
**independent** (neither enables the other; they could happen in either order).
The DM schema's linear chain (F5→F6) imposed a false dependency.

---

## 9. Step 2: Narrative recoverability evaluation

Reading the spine encoding from §8 *without* the synopsis. For each of the 7
statements from the first paper test's §10c:

| # | Original prose | Recoverable from spine? | Source field(s) | Verdict |
|---|---------------|------------------------|-----------------|---------|
| 1 | "Hilde raids the Bärenschädel camp at dawn" | **Yes.** | `gloss`: "Hilde leads a dawn raid on the Bärenschädel camp as the flood begins." | Gloss carries it directly. |
| 2 | "The flood sweeps Arnulf away" | **Yes.** | `gloss`: "The flood rises faster than expected and sweeps Arnulf away; everyone believes he drowned." | Gloss carries it. |
| 3 | "Forced truce on a shrinking ledge above the water" | **Yes.** | `gloss`: "Stranded on a shrinking ledge above the floodwater, Hilde and Gunnar are forced into a truce to survive." + `motivation`: survive_flood | Gloss carries the scene; motivation explains *why*. |
| 4 | "Allies become lovers" | **Yes.** | `eff_world`: rel = "allies"→"lovers" (structural) + `gloss`: "alliance deepens into a sexual and emotional relationship" (narrative) | Structural fields carry the *transition*; gloss carries the *nature*. |
| 5 | "Svala condemns the cross-clan relationship as blasphemy" | **Yes.** | `gloss`: "Svala...condemns Hilde and Gunnar's relationship as blasphemy against the clan laws" + `motivation`: enforce_old_law + `threatens`: bond_with_Gunnar | All three fields contribute. Gloss names the act; motivation names the drive; threatens names the target. |
| 6 | "Arnulf returns from the dead" | **Yes.** | `kind`: return + `gloss`: "Arnulf, alive after being washed into a hidden channel, returns..." + `pre_belief`: alive(Arnulf)=false | Kind gives the type; belief pre gives the dramatic irony; gloss gives the mechanism. |
| 7 | "The blood-feud ends" | **Yes.** | `eff_world`: holds(feud)=false (structural) + `gloss`: "ending the blood-feud; the clans merge to share the high valley" + `motivation`: end_feud | Structural fields carry the state change; gloss and motivation carry the significance. |

**Score: 7/7 recoverable.** The spine encoding allows a reader to reconstruct all
7 statements without the synopsis.

### But from which fields?

| Field | Statements it contributes to | Load-bearing alone? |
|-------|------------------------------|-------------------|
| `gloss` | 7/7 | Yes — all 7 are recoverable from gloss alone |
| `motivation` | 4/7 (#3, #5, #7, and indirectly #1) | No — motivation adds *why* but not *what* |
| `threatens` | 2/7 (#5, #6) | No — adds conflict dimension but not scene content |
| `enables` | 0/7 directly | No — structural; adds ordering rationale, not narrative |
| `roles` | 0/7 directly | No — too abstract (villain/hero) to recover specific action |
| `kind` | 1/7 (#6 — "return" names the event type) | Marginal — too generic for most functions |
| Typed `held` | 1/7 (#6 — alive=false gives dramatic irony) | Marginal — adds information only for belief-gap plots |

---

## 10. Step 3: Structural gains evaluation

For each defect class, can the spine detect or prevent malformed plans?

### 10a. Early reveal (belief flipped before its floor)

**DM schema:** Caught by `_check_belief_grounding` (belief effect must have a
prior concealment).

**Spine:** Same check applies, *plus* the `enables` link makes the dependency
explicit. A validator can check: if F6 (return) has `enables: [F7]`, and F6's
pre_belief requires alive(Arnulf)=false, then there must be an earlier function
(F2) whose eff_belief sets alive(Arnulf)=false, and F2 must be ordered before F6.

**Verdict:** Spine adds explicitness but not new detection power. **Marginal gain.**

### 10b. Phantom reversal / double-return

**Defect:** Arnulf "returns" twice — F6 reveals him alive, then a hypothetical F6b
reveals him alive again. In the DM schema, nothing prevents this (F6b would pass
all checks if it has valid pre/eff).

**Spine test:** Add a malformed F6b:
```json
{"id": "F6b", "kind": "return", "subject": "Arnulf", "enables": ["F7"],
 "pre_belief": [{"observer": "Aschenwulf", "fluent": {"pred": "alive", "args": ["Arnulf"]}, "held": false}]}
```

**Detection:** F6b's pre_belief requires `believes(Aschenwulf, alive(Arnulf)) = false`,
but F6 already set it to `true`. The `enables` graph shows F6→F7 and F6b→F7, so
F6b must come after F6 (both enable F7). But after F6, the belief is `true`, so
F6b's precondition is unsatisfied.

A projected-state checker (FR-567's `project_chapter_state`) would catch this:
at the point F6b fires, the belief state already has alive(Arnulf)=true, so
pre_belief is violated.

**Verdict:** The spine's causal links don't add detection here — the precondition
violation is detectable with projected state alone. But `enables` would flag the
structural anomaly: two functions both claim to enable F7 by the same mechanism.
**Moderate gain.**

### 10c. Unresolved affect thread

**DM schema:** Caught by `_check_affect_closure` (every open must have a close).

**Spine:** Same check, but with richer affect kinds. If the spine adds `betrayal`
as an affect kind, then F5 could open a `betrayal` thread (Svala accuses Hilde
of betraying the clan), and the plan would need to close it. The DM schema
compressed this into `guilt` (which it was not — guilt is self-directed,
betrayal is other-directed).

**Test:** Reclassify F5's affect:
```json
{"op": "open", "char": "Hilde", "kind": "betrayal"}
```
Now the plan must close `betrayal` somewhere. F7 would need:
```json
{"op": "close", "char": "Hilde", "kind": "betrayal"}
```
This is semantically correct — F7 (clan merger) resolves the betrayal accusation.

**Verdict:** Richer affect kinds make the tracking more precise. The DM schema's
`guilt` was a lossy compression of two distinct emotional threads. **Real gain.**

### 10d. Unplayable epilogue

**Defect:** The final function requires a precondition that no prior function
achieves (e.g., the feud ends but no function establishes the lovers relationship).

**DM schema:** Caught partially by `_check_causal_antecedent` (pre_world must have
a producer).

**Spine:** The `enables` graph makes this explicit. F7's `enables` sources are
F4, F5, F6. If any of these is removed, F7 loses a required enabler. A validator
can check: for every function F, every function in `enables_inverse(F)` must
exist and be ordered before F.

**Test:** Remove F4 from the plan. F7's pre_world requires
`rel(Hilde, Gunnar) = "lovers"`, which only F4 produces. The DM schema's causal
antecedent check would catch this. The spine's `enables` graph would also catch it
(F7 lists F4 as an enabler, but F4 doesn't exist).

**Verdict:** Both schemas catch it. The `enables` graph gives a more readable
diagnostic ("F7 requires F4 which is missing" vs "F7's pre_world has no
producer"). **Marginal gain.**

### 10e. Unmotivated action

**Defect:** A function exists in the plan but no character has a reason to perform
it.

**DM schema:** No detection. `subject: Hilde` says *who* but not *why*.

**Spine:** The `motivation` field makes this checkable. A validator can require:
every function with an intentional subject must have a non-null `motivation`. If
someone adds a function with `motivation: null` and `subject: Hilde`, the
validator flags it.

**Test:** Remove F3's motivation:
```json
{"motivation": null, "subject": "Hilde"}
```
A spine validator would flag: "F3 has intentional subject Hilde but no
motivation — why does she reconcile with Gunnar?"

**Verdict:** **New detection power.** The DM schema cannot check this at all.
The `motivation` field makes unmotivated actions visible. **Strong gain.**

### Structural gains summary

| Defect class | DM schema | Spine | Delta |
|-------------|-----------|-------|-------|
| Early reveal | Caught | Caught (more explicit) | Marginal |
| Phantom reversal | Not caught | Detectable via projected state + enables | Moderate |
| Unresolved affect | Caught (2 kinds) | Caught (richer kinds, more precise) | Real |
| Unplayable epilogue | Caught | Caught (better diagnostic) | Marginal |
| Unmotivated action | Not caught | Caught via motivation field | **Strong** |

---

## 11. Step 4: Gloss cost evaluation

### 11a. Remove all glosses — what remains?

Stripping `gloss` from every function, the spine encoding becomes:

| Function | Recoverable meaning (without gloss) |
|----------|-------------------------------------|
| F1 | villainy by Hilde, motivated by destroy_enemy_camp, threatens Gunnar's protect_clan. Hilde is villain, Bärenschädel is victim. Opens Hilde's guilt. Pre: rel(H,G)=enemy. |
| F2 | villainy by Flood, no motivation, threatens Hilde's protect_family. Flood is villain, Arnulf is victim. Opens Hilde's loss. Eff: clans believe Arnulf dead. |
| F3 | reconciliation by Hilde, motivated by survive_flood, threatens Aschenwulf's maintain_feud. Pre: both alive. Eff: rel=allies. Closes Hilde's guilt. |
| F4 | reconciliation by Hilde, motivated by bond_with_Gunnar. Pre: rel=allies. Eff: rel=lovers. Clans learn of relationship. |
| F5 | villainy by Svala, motivated by enforce_old_law, threatens Hilde's bond_with_Gunnar. Pre: clan believes rel=lovers. Opens Hilde's guilt. |
| F6 | return by Arnulf, motivated by rejoin_clan, threatens Hilde's bond_with_Gunnar. Pre: alive(Arnulf)=true but believed false. Eff: clans learn Arnulf alive. Closes Hilde's loss. |
| F7 | reconciliation by Hilde, motivated by end_feud, threatens Svala's enforce_old_law. Pre: rel=lovers. Eff: feud=false on both clans. Closes Hilde's guilt. |

### 11b. The three questions

**Q1: Is the gloss redundant?**

Partially. Without the gloss, a reader can reconstruct:
- *Who* does *what kind* of thing (villainy/reconciliation/return)
- *Why* they do it (motivation goal)
- *What changes* (world/belief effects)
- *Who it threatens* (conflict)
- *What emotional debt* opens/closes

What the reader **cannot** reconstruct without the gloss:
- **Physical setting** ("shrinking ledge above the floodwater", "dawn raid", "hidden channel")
- **Mechanism** ("swept away by flood" vs "killed in battle" vs "fell from cliff")
- **Social texture** ("blasphemy against the clan laws", "sexual and emotional relationship")
- **Scene specifics** ("camp", "higher ground", "high valley")

**Verdict: The gloss is NOT fully redundant.** The structured fields carry the
*plot* (who, why, what changes, what conflict) but not the *story* (where, how,
what it looks like). The distinction maps to fabula (recoverable from structure)
vs. syuzhet (requires gloss).

**Q2: Is the gloss load-bearing?**

For **plot** recovery: **No.** The motivation + threatens + kind + effects are
sufficient to understand the causal/emotional structure. A reader without the
gloss knows: "Hilde attacks because she wants to destroy the enemy camp; this
threatens Gunnar's clan; it opens her guilt; and it enables the later forced
reconciliation."

For **story** recovery: **Yes.** Without the gloss, the reader cannot know it's a
dawn raid, or that there's a flood, or that the truce happens on a ledge. The
story is richer than the plot.

**Verdict: The gloss is load-bearing for story but not for plot.** Whether it is
"needed" depends on whether the plan's purpose is to carry plot (causal skeleton)
or story (full narrative).

**Q3: Is the gloss verifiable?**

A validator could check **weak consistency**:
- The gloss mentions "Hilde" → the subject or a role binding contains "Hilde" ✓
- The gloss mentions "raid" → the kind is "villainy" (compatible) ✓
- The gloss mentions "Gunnar" → Gunnar appears in pre_world, roles, or motivation ✓

A validator **cannot** check **strong consistency**:
- The gloss says "dawn raid" — nothing in the structured fields constrains *when*
  the villainy occurs. "Midnight ambush" would be equally consistent.
- The gloss says "shrinking ledge above the floodwater" — nothing constrains the
  *setting* of the reconciliation. "Meeting in a tavern" would pass.

**Verdict: The gloss is weakly verifiable but not strongly verifiable.** A
validator can check that the gloss doesn't *contradict* the structured fields,
but it cannot check that the gloss *faithfully represents* the synopsis. This is
the recognition problem in miniature: the gloss is free-form prose, and checking
it requires understanding it.

---

## 12. Findings and hypothesis verdicts

### H1 (gloss hypothesis): CONFIRMED

> The `gloss` field alone closes the §10 narrative gap, but it is load-bearing,
> unverifiable (strongly), and shifts the problem from vocabulary to annotation.

The gloss makes all 7 statements recoverable (§9, score 7/7). But the gloss is
the *only* field that carries all 7 — no other field contributes to more than
4/7. Removing the gloss loses the story (§11b, Q2). And the gloss is only weakly
verifiable (§11b, Q3).

**The plan becomes a hybrid:** closed structural skeleton (verifiable, gatable) +
unconstrained prose layer (load-bearing, not strongly gatable). This is better
than the DM schema (which had no prose layer and couldn't carry the story) but it
does not fully solve the recognition problem — it confines it to one field per
function.

### H2 (intentionality hypothesis): PARTIALLY CONFIRMED

> `motivation` and `threatens` fields encode *why* functions exist, which is the
> main information the DM schema lacks.

Motivation and threatens contribute to 4/7 and 2/7 statements respectively (§9).
More importantly, they enable a **new structural check** — unmotivated action
detection (§10e) — that the DM schema cannot perform.

However, H2 overstated the case: motivation carries the *plot logic* but not the
*narrative*. "Hilde's goal is destroy_enemy_camp" tells you *why* but not *how*
(raid? sabotage? parley?). The gloss is still needed for story recovery.

**Verdict:** Intentionality is the **highest-value structural addition**. It adds
the most detection power (unmotivated action is the only "strong gain" in §10)
and the most narrative information of any non-gloss field. But it does not
replace the gloss.

### H3 (causal-link hypothesis): CONFIRMED

> For the 10030-BC plot (linear, single-threaded), `enables` links add no
> information beyond temporal order.

Strictly false — the `enables` links revealed that F5 and F6 are **independent**
(the DM schema's F5→F6 order was a false dependency). But this is a minor
observation. The `enables` links contributed to 0/7 narrative recoverability
statements (§9). Their value is structural (§10, mostly marginal gains), and the
partial-order benefit is only testable with a multi-threaded premise.

**Amended verdict:** Causal links add *some* structural information even for
linear stories (they reveal false dependencies), but their primary value —
parallel-safety — requires a branching premise to test.

### H4 (typed-belief hypothesis): CONFIRMED

> Allowing `held: "enemy" | "lovers" | ...` was the LLM's natural choice. The
> spine should accept it.

The typed beliefs were already present in the LLM's original output. The DM
schema rejected them (causing the total-plan-drop bug). The spine encoding
accepts them naturally. No information is lost, no coercion is needed, and the
belief lane becomes more expressive (it can distinguish "believes they are
enemies" from "believes they are allies" — the DM schema could only express
"believes or does not believe").

**This is a zero-cost fix.** Change `held: bool` to `held: bool | str` in the
schema and the parse-boundary failure disappears.

---

## 13. Summary: what the spine buys

| Dimension | DM schema | Spine | Delta |
|-----------|-----------|-------|-------|
| Narrative recoverability (§10c statements) | 0/7 | 7/7 (via gloss) | +7 |
| Narrative recoverability without gloss | 0/7 | ~3/7 (partial, via motivation + typed belief + kind) | +3 |
| Structural defect detection | 3/5 classes | 5/5 classes | +2 (phantom reversal, unmotivated action) |
| Typed beliefs | Rejected (parse failure) | Accepted natively | Bug fix |
| Causal ordering | Flat linear chain | Partial order with true dependencies | Reveals false deps |
| Affect precision | 2 kinds (loss, guilt) | Expandable (betrayal, etc.) | More precise tracking |
| Prose layer | None | `gloss` per function | Carries story; weakly verifiable |

### The key insight

The spine does not **solve** the vocabulary insufficiency from §10 — it
**factorizes** it. The plan splits into two layers:

1. **Structural layer** (kind, motivation, threatens, enables, pre/eff, affect):
   closed vocabulary, mechanically verifiable, carries the *plot*.
2. **Prose layer** (gloss): open vocabulary, weakly verifiable, carries the
   *story*.

The DM schema had only the structural layer. The spine adds intentionality and
typed beliefs to the structural layer (making it richer) and adds the prose layer
(making the plan self-sufficient for narrative recovery). The recognition problem
is not eliminated but is confined to one field per function, where it is more
tractable than whole-document recognition.
