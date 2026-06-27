# Plan: Scene Typing — Tag Scene Dynamics and Feed Them to the LLM

**Date:** 2026-06-27
**Status:** Proposed.
**Origin:** Falsified out of [plan-interiority-ab-test.md](plan-interiority-ab-test.md). The interiority
A/B was a GO on an adrenaline-rush scene (Floodmark) and a REVISE on a touchy-feely scene (the Loom).
Reading the raw verdicts showed the gap was **not** the interiority technique — it was that one writer
instruction and one judge rubric were applied to two *kinds of scene* that demand opposite affect
handling. The cure is to make scene type a **first-class, tagged input**, not an implicit assumption
baked into a single prompt.
**Gates:** the affect-closure validator in [plan-generative-roundtrip.md](plan-generative-roundtrip.md)
(net-new build #3) and the L7 `affect_throughline` layer in [status-L1-L7.md](status-L1-L7.md).

---

## The claim in one line

A scene's affect budget and its closure mode are determined by its **scene type**. Author the type,
tag it on the beat, and feed it to every prompt that writes or judges that beat — or the same rubric
will punish the most explicit arm on every reflective scene and over-write interior on every action
scene.

---

## Don't invent a taxonomy — adopt the canonical one

"Adrenaline-rush vs touchy-feely" is a folk re-derivation of a sixty-year-old craft classification. We
adopt the established vocabulary so the tag is grounded in prior art.

### Primary axis: proactive vs reactive (Swain Scene/Sequel)

Dwight V. Swain, *Techniques of the Selling Writer* (1965), split passages into **Scene** and
**Sequel**; Jack Bickham (*Scene and Structure*, 1993) and Randy Ingermanson / Evan Marshall reframed
the same split as **proactive** vs **reactive** scenes.

| | Swain | structure | how the feeling closes | folk alias |
|---|---|---|---|---|
| **proactive** | Scene | Goal → Conflict → **Disaster** | spent *through the choice / disaster* | adrenaline-rush |
| **reactive** | Sequel | **Reaction** → Dilemma → Decision | resolved *internally, in a Decision* | touchy-feely |

A proactive scene closes a feeling through *action*; a reactive scene closes it *internally*, by
reaching a decision, recognition, or a shift in dialogue. This is exactly the open/close-mode
distinction the Loom probe exposed.

### The mechanism: the Motivation–Reaction Unit (MRU)

Swain's small-scale unit is the **MRU**: external **Motivation** → internal **Reaction**, where the
Reaction is strictly ordered **Feeling → Reflex → Rational action/speech**, and parts may be *dropped*.

- In a **proactive** scene the Reaction compresses to Feeling+Reflex (*"a bolt of adrenaline... he
  jerked the rifle"*) — interior is spent, not dwelt on; lingering interior kills pace.
- In a **reactive** scene the Reaction *expands* into the whole Dilemma→Decision — the interior is the
  event.

This is the formal basis of the user's principle **"use less emotional input in a pure action scene."**
It is not a stylistic preference; it is the MRU prescription. Affect is *dosed by scene type*.

### Secondary axis (orthogonal): fiction-writing mode

A scene is also typed by the **mode** dominating its presentation — **action, dialogue, feeling,
thought, narration, description, exposition** (Wikipedia, *fiction-writing mode*; Evan Marshall, *The
Marshall Plan for Novel Writing*, 1998). This is a finer sub-tag under proactive/reactive that decides
*how* the closure is rendered (e.g. a reactive scene closed in *dialogue* vs in *thought*).

---

## Schema — tag the dynamics on the beat

Scene typing is an **additive layer** on the existing beat record
(`{id, gloss, chapter, kind, subject}`; `kind` = the L4 16-kind Propp classification). It does not
replace `kind` — `kind` is *what happens* (a Propp function); `scene_type` is *how the feeling moves*.

```yaml
# additive fields on each beat / scene definition
scene_type: proactive | reactive        # Swain/Marshall — the affect-dose + closure switch
mode: action | dialogue | feeling | thought | narration | description | exposition  # optional sub-tag
affect_dose: low | high                  # DERIVED from scene_type (proactive=low, reactive=high)
```

`affect_dose` is derived, not authored — a deterministic projection of `scene_type` (proactive → low,
reactive → high). It is materialised as a field only so the writer prompt and the judge rubric read one
explicit value rather than re-deriving it.

### Where the tag is assigned

A new typed classifier layer, parallel to L4 `classify_kinds`: one LLM node reads the beat glosses (in
narrative order, so the proactive/reactive rhythm is visible) and emits `scene_type` + `mode` per beat;
a Python validator enforces the closed vocabularies. Provisional name **L4b `classify_scene_type`**,
graph `graphs/classify_scene_type.yaml`, prompt `prompts/classify_scene_type.yaml`. Closed sets are
validated exactly like the affect/kind layers — unknown values are a hard validation failure, never a
silent fallback.

---

## These tags are inputs to the LLM — both writer and judge

The whole point is that scene type is **fed forward** into every prompt that touches the beat.

### Writer / projection prompt (affect-dosage policy)

The prose-projection prompt (roundtrip reconstruct; interiority sketch) receives `scene_type` and doses
the interior accordingly:

- **proactive** — goal + belief lead; the named feeling is a brief visceral spike (Feeling→Reflex),
  resolved *through* the disaster/choice. **Low** explicit-interior budget. Do not linger.
- **reactive** — the feeling leads; the scene *is* the affect arc (Reaction→Dilemma→Decision), resolved
  internally. **High** explicit-interior budget.

The interiority sheet (goal + belief + affect arc) is still injected; `scene_type` only governs *how
much of it surfaces as explicit interior* in the prose.

### Judge / validator rubric (closure mode — MUST branch on scene_type)

The affect-closure check is the half that the Loom probe proved is scene-type-blind today. It must
branch:

- **proactive** — a feeling closes iff it is **spent in a choice / the disaster lands**; a feeling
  merely named and then dropped *is* a defect.
- **reactive** — a feeling closes iff it is **recognised, named, or shifted toward a decision in
  dialogue or thought**; resolution-through-action is **not** required. Demanding it under-credits the
  most explicit arm — the exact Loom v2 mis-grade.

The closed `held_as` set (`true | false | mistaken | unknown`) and the `affect` set
(`guilt | hope | betrayal | fear | relief | grief`) are unchanged; only the *acceptance condition* for
"closed" gains a scene-type branch.

---

## Why this belongs in the round-trip

The generative round-trip's deterministic coherence validators (net-new build #3) replace a subjective
LLM grade with typed checks. The affect-closure validator is one of them. Without `scene_type` on the
beat:

- it will mark every reactive beat as "feeling opened but never carried" (false defect), and
- the projection prompt will over-write interior on every proactive beat (pace defect the judge cannot
  see).

So `scene_type` is a **required field on every round-trip beat**, and the affect-closure validator
**must** accept the resolution mode that matches the tag. The validator should also carry the sibling
impossible-knowledge check (cross-character interior-leak AND plot-fact variants) surfaced by the same
A/B — both are coherence checks, not affect checks.

---

## Build order

1. **Closed vocabularies** — freeze `scene_type ∈ {proactive, reactive}` and `mode` set; write the
   validator (hard-fail on unknowns) first, RED.
2. **L4b classifier** — `classify_scene_type` graph + prompt; tag beats in narrative order; GREEN the
   validator.
3. **Writer input** — thread `scene_type`/`affect_dose` into the projection (and interiority-sketch)
   prompt; low/high interior budget.
4. **Judge branch** — split the affect-closure acceptance condition on `scene_type`; re-grade the
   existing Loom v2 draws under the reactive closure mode. If arm B then leads, the original gap was the
   rubric, not the technique (the predicted result).
5. **Confirm transfer** — run the interiority battery on a *proactive* scifi scene (Mara breaking into
   the server, triggering the rollback) to confirm the GO transfers when scene type is held constant.

Steps 4 and 5 are the two falsification follow-ups carried over from the interiority A/B; step 4 is the
cheaper one (re-grade existing draws, no new generation).

---

## Sources

- Dwight V. Swain, *Techniques of the Selling Writer* (1965), pp. 84–85, 96–100 (Scene/Sequel, MRU).
- Jack M. Bickham, *Scene and Structure* (1993).
- Randy Ingermanson, "Writing the Perfect Scene" (proactive/reactive scenes + MRU).
- Evan Marshall, *The Marshall Plan for Novel Writing* (1998) (section types).
- Wikipedia, *Scene and sequel*; *Fiction-writing mode*.
