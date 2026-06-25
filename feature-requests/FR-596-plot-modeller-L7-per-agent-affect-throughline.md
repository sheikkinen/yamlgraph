# Feature Request: FR-596 Plot Modeller — L7 per-agent affect throughline (decompose the monolithic affect pass)

**Priority:** HIGH
**Type:** Feature (architecture revision — subject-axis decomposition)
**Status:** Enforced — Gate-1 KILL (per-cast map falsified; deeper root cause = `affect_recall` is the `world_recall` pathology one layer over — under-determined sparse skeleton; regenerability ruler indicated → FR-597) (2026-06-25)
**Effort:** ~1 day (spike-gated; Gate 1 may KILL early)
**Requested:** 2026-06-25
**Predecessor:** FR-578 (L7 monolithic affect pass — Enforced/REVISE, affect_recall 0.09, model-invariant)
**Sibling lineage:** FR-590/FR-591 (L5 per-agent perspective — the proven precedent for this axis)
**Blocks:** FR-579 (merge/pipeline node) — unblocked only when L7 clears its gate

## Summary

L7 (`assign_affects`) reads **affect_recall 0.09** (3/33), and the failure is
**model-invariant** (haiku 0.12 → sonnet-4-6 0.09 — scaling *hurt*). FR-578's own
confusion analysis localized the wound: `char` and `op` are mostly correct (the
model knows *who* feels and *when* an arc opens/closes), but **`kind` is the
dominant error axis** — it over-emits generic `hope`/`loss` and systematically
misses the moral-relational `guilt`/`betrayal`, and the open/close pairing is
shuffled (right timing, wrong *which-kind-closes*).

The current prompt ([prompts/assign_affects.yaml](../examples/plot_modeller/prompts/assign_affects.yaml))
is a **single monolithic pass over the whole board** that asks the model to do four
orthogonal jobs at once: (1) placement (pivotal vs structural) for every beat,
(2) pick `kind` from a closed 6-enum, (3) assign `char`+`toward`, and (4) **plan
cross-beat arc closure** (*"every arc you OPEN should CLOSE later… a close must
match an earlier open of the SAME kind for the SAME char"*). That is the identical
"do everything over all entities per beat" framing that FR-585/587 proved the model
cannot carry for L5 — there, the same load produced the `at` waypoint flood.

This FR cuts the **subject axis**, exactly as FR-590 did for L5: instead of one
global pass, **map over each agent** and ask the model for the one thing it is
strongest at — narrate **a single character's emotional throughline**. Affect is
*intrinsically* per-character: every `AffectDelta` is keyed on `char`, and the
open/close pairing the monolithic prompt begs for by instruction **is** per-character
emotional continuity. Scope the pass to one character and that arc ledger becomes a
single coherent story the model can hold; `guilt`/`betrayal` (the missed relational
kinds) become the *spine* of a character's POV rather than scattered annotations.

## Value Statement

L7 affect_recall rises off the 0.09 floor — by scoping comprehension to one
character at a time, so the model's strongest faculty (single-subject emotional
narrative) supplies arc continuity and kind discrimination for free, rather than
instructing against the flood (FR-578) or scaling the model (proven futile by the
haiku→sonnet invariance). The per-agent affect summaries are a **human-legible
diagnostic** the monolithic pass never produced, making any KILL attributable to
*comprehension* (the character's arc was never narrated) vs *encoding* (it was
narrated but mis-kinded).

## Judgement (2026-06-25)

**Verdict: Authority GRANTED.** This is the most disciplined FR in the arc — it has
internalized the floor discipline (J:N2), the attributable-KILL requirement
(FR-590), the dumb-adapter confound (structured output, not prose-grep), the
`audit_as_ritual` guard (correctly notes this is L7's *first* subject-axis attempt,
not a fifth wording pass), and the one-iteration rule. The diagnosis is sound and
the lever is the proven one: FR-590/591 established per-character viewpoint as the
authoring seam, and affect is its purest instance (every `AffectDelta` is keyed on
`char`). Claims verified against the codebase: `assign_affects.yaml` is the
monolithic four-job pass as described (op/char/6-closed-kinds/toward, with the
cross-beat closure self-enforcement instruction); `AffectDelta` lives in
`schema/affects.py`; `validate_affects` and `_norm_name` are in `nodes/tools.py`;
`main_l7` + `_l7_verdict` are in `evaluate.py`, and the **≥ 0.50 GO bar is the
existing REVISE threshold**, not an invented number; the model-invariance diary
(`the-bigger-model-that-knew-less`) exists. The instrument (detection /
kind-given-detection / toward-given-relational) is the right *additive* diagnostic
and correctly subordinated to the generation change as the cure.

**Corrections required before enforce (do not widen scope):**

1. **Gate 1 must map over GT agents, not `extract_agents` output (PRIMARY — isolation
   confound).** The map keys on a roster, and `evaluate.main_l7` scores against GT
   affects whose `char` set is fixed. If Gate 1 maps over **extracted** agents, any
   GT-scored affect for a character that `extract_agents` dropped is **structurally
   unreachable** — no map cell exists for that feeler — capping recall below 0.50
   regardless of how good the affect framing is. detective and scifi (the 0/8
   genres) are the *richest* casts, exactly where extract_agents most likely sheds a
   minor character, so a roster gap would masquerade as a framing KILL on precisely
   the cells that decide the FR. The cure is already in the repo and is the
   established layer-spike convention: feed **`_load_gt_agents`** into the Gate-1 map
   (as `spike_snapshot_diff.py` / the L5 perspective spike do), isolating the affect
   framing from upstream extraction quality. `extract_agents` is correct for the
   GO-time production wiring; it is the wrong roster for the isolating A/B. If GT
   agents are not fed, the FR must first report the **agent-coverage ceiling** (% of
   GT affect `char` values present in the extracted roster, per genre) so a miss is
   attributed to roster, not framing.

2. **Name the detection-recall inflation, so ≥ 0.70 is read honestly (secondary).**
   Because each map cell fixes `char` to the focal agent, `char`-match is structurally
   near-free; detection recall (`op`+`char`) collapses largely to **op + beat-id
   alignment** recall. That is still a valid "did the reframe drop arcs?" floor, but
   record that `char` is not an earned component of it — otherwise 0.70 reads as a
   harder bar than it is, and a beat-misalignment failure (Risk 3) could hide inside
   a passing-looking detection number.

3. **Make the two KILL flavors route different next levers explicitly (endorse +
   pin).** The FR already distinguishes prose-missed-the-arc (→ framing falsified →
   FR-578 model scale) from prose-right-but-encode-miskinded (→ encode prompt is the
   bug, framing still untested). Pin that the Stop Rule's **model-scale escalation
   fires ONLY on the prose-missed flavor**; a sub-0.50 result with the arcs *present*
   in the throughlines is an encode-prompt miss, not a framing falsification, and
   must not trigger scale. The verdict must read the stored throughlines and state
   the flavor before citing the aggregate.

**Minor:** A GO at ≥ 0.50 promotes the spike to a graph but does **not** clear the
production ACCEPT bar (`_l7_verdict` ≥ 0.70) — L7 stays REVISE until 0.70, so
"promote to graph" ≠ "L7 done" and FR-579 unblocks on the graph existing, not on
ACCEPT. REQ-YG-020 reuse (no new CAP for a spike), one wording iteration,
precision-reported-not-gated, diary + changelog `req: REQ-YG-020` — all correct,
endorse.

**Frozen scope:** the two new prompts (`affect_throughline`, `encode_affect`), the
pure `combine_affects` helper (unit-tested, no LLM, no dedup), the `spike_affect.py`
Gate-1 harness over **GT agents**, and the additive sub-axis diagnostic on the frozen
FR-578 gate. No graph wiring, no `run.py` change, no model scale until a clean
attributed prose-missed KILL. The gate decides the FR; the instrument only attributes
the decision.

## Problem

The shared wound is **generic-kind flooding under global attention**. Root cause,
mirroring the L5 `at` flood one dimension over: a global all-characters pass spreads
shallow attention across every agent's arcs simultaneously, so the model defaults to
the easy generic kinds (`hope`/`loss`) and cannot hold each character's
moral-relational ledger (`guilt`/`betrayal`, which require tracking *who wronged
whom* across beats). The two richest-character genres — detective (0/8) and scifi
(0/8) — score **zero** recall, consistent with attention thinning as the cast grows.

The monolithic framing also makes **open/close balance** an instruction the model
must self-enforce across the whole sequence (currently informational, deferred to
the FR-579 merge node). Per-character framing makes balance a property each map cell
*owns end-to-end* — a dangling `open` is visible within one character's arc, not
buried in a global list.

The untested hypothesis: the wound is an artifact of the **global framing**, not the
model tier (the haiku→sonnet invariance is positive evidence for this — an invariant
gap means the bottleneck is upstream of the model). **No prior L7 work has touched
the subject axis** — the monolithic prompt is L7's only framing ever, so this is the
*first* untried lever, not a fifth (the `audit_as_ritual` guard is not yet live for
L7).

## Proposed Solution

### Decomposition axis: per-agent affect throughline (map-reduce)

A **YAMLGraph-native map-reduce** over agents (CAP-11), mirroring FR-590/591.
**Gate-1 maps over the GT agent roster** (`_load_gt_agents`), not `extract_agents`
output, to isolate the affect framing from upstream extraction quality (Judgement
correction #1): scoring is against GT affects whose `char` set is fixed, so a feeler
the extractor dropped would be structurally unreachable and masquerade as a framing
KILL. `extract_agents` is the correct roster only for the GO-time *production*
wiring.

```
GT agent roster  (_load_gt_agents — Gate-1 isolation; extract_agents at GO only)
        │
        ▼  map over agents (CAP-11 map node)
   ┌──────────────────────────────────────────────────┐
   │  affect_throughline  (LLM, free prose)            │  ← stored to
   │     "trace THIS character's emotional arc:         │     results/l7/throughlines/<genre>/<agent>.md
   │      where does guilt/betrayal/hope open & close?" │
   │            │                                       │
   │            ▼                                       │
   │  encode_affect  (LLM, AffectDelta list for THIS    │  ← closed 6-kind vocab, keyed by beat_id,
   │                  agent only, beat-keyed)           │     ONLY this agent's felt affects
   └──────────────────────────────────────────────────┘
        │
        ▼  combine_affects (deterministic code, no LLM)
   per-beat eff_affect  { id, eff_affect: [AffectDelta, …] }
```

### Stage 1 — per-agent comprehension (LLM, the map body)

**`affect_throughline.yaml`** (new) — input: the full beat glosses + one focal
agent. Output: free prose narrating that character's **emotional arc** across the
story, anchored to beat ids (e.g. *"F2: I review the footage and feel the first
guilt toward Jonas … F6: ARIA's deception lands as betrayal … F12: at the shutdown I
close both — the guilt to Jonas and the loss"*). This is the kind-discrimination
filter: a single character's moral story names *guilt*, *betrayal*, *hope* as the
spine, not as annotations. **Stored** at
`results/l7/throughlines/<genre>/<agent>.md` (the attribution artifact).

**`encode_affect.yaml`** (new) — input: that agent's throughline + the beat ids.
Output: `AffectDelta` list (`op`/`char`/`kind`/`toward`, the same closed 6-kind
vocab as `assign_affects.yaml`) for **only this agent's felt affects**, each keyed to
its `beat_id`. The felt affect belongs to the feeler, so `char` is always the focal
agent; `toward` references another named agent for relational kinds. Structured
output — no dumb-adapter confound.

### Stage 2 — combination (deterministic code, no LLM)

**`combine_affects` helper (`nodes/tools.py`).** Given per-agent `AffectDelta` lists:

- **Group by `beat_id`** into per-beat `eff_affect`.
- **No symmetric dedup needed** (unlike FR-590's `rel`): affect is owned by exactly
  one feeler, so two agents never emit the same delta — union is clean. (A relational
  `betrayal` opened in A's POV `toward` B is owned by A alone; B's own felt response,
  if any, is a *separate* delta in B's cell.)
- Reuse `_norm_name` for the `toward` agent-name normalization; no new affect logic.

Open/close balance is checkable **per cell** during combine (each agent's arcs are
self-contained), surfacing dangling opens as a diagnostic.

### Instrument (diagnostic, alongside the gate — not a new metric FR)

To make the Gate-1 decision **attributable**, decompose `affect_recall` for the gate
read only into sub-axes (no change to the FR-578 gate definition, no `evaluate.py`
contract change beyond an additive diagnostic):

- **detection recall** = `op`+`char` match (found the event, right feeler, right
  open/close) — proves the per-agent framing did not *drop* arcs;
- **kind-given-detection** = of detected events, fraction with correct `kind` — the
  axis FR-578 named as the wound;
- **toward-given-relational** = of relational kinds, fraction with correct target.

This is the instrument that reads *which axis the reframe moved*; the cure is the
per-agent generation, the instrument only measures it.

### Files (spike, Gate-1-first — do NOT wire the full graph until GO)

- `prompts/affect_throughline.yaml` — new (per-agent emotional prose).
- `prompts/encode_affect.yaml` — new (per-agent AffectDelta list, beat-keyed).
- `nodes/tools.py` — `combine_affects` deterministic helper (pure, unit-tested);
  reuse `validate_affects` for per-agent structural validation; reuse `_norm_name`.
- `examples/plot_modeller/spike_affect.py` — throwaway spike harness: per fixture,
  **per GT agent** (`_load_gt_agents` — correction #1) → throughline (store) → encode
  → `combine_affects` → `results/l7/<genre>.yaml` → `evaluate.main_l7`. Reports the
  per-genre **agent-coverage ceiling** (% of GT affect `char` values present in the
  roster) so any miss is attributable to roster vs framing.
- `evaluate.py` — **frozen gate** (clean A/B against FR-578's 0.09 baseline); only an
  *additive* sub-axis diagnostic for the Gate-1 read, no gate-threshold change.
- On GO only: `graphs/assign_affects.yaml` gains the map-over-agents subgraph;
  `run.py` wires it (the `--mode assign-affects` path).

## Acceptance Criteria

- [ ] **Gate 1 — affect-throughline spike (decides the whole FR).** Build the two
      prompts + `combine_affects` only. Run on haiku (verify
      `Creating LLM: anthropic/claude-haiku-4-5`), regenerate `results/l7`, report
      `affect_recall`, `affect_precision`, and the three sub-axis recalls.
      **Decision rule (carries FR-578's J:N2 floor discipline):** GO requires
      `affect_recall` to clear the **REVISE floor (≥ 0.50)** — a >5× jump from 0.09 —
      **AND** detection recall (`op`+`char`) to hold **≥ 0.70** (per-agent framing
      must not *drop* arcs) **AND** the dominant error class to shift off `kind`
      (kind-given-detection materially up). `affect_recall` still < 0.50 after one
      wording iteration, **or** detection recall dropping (lost events), is a
      **KILL**, not a GO.
- [ ] `combine_affects` has unit tests (pure function): per-beat grouping across two
      agents, union recall (an affect felt by exactly one agent survives), relational
      `toward` cross-reference preserved, and per-cell open/close balance surfaced —
      each tagged `@pytest.mark.req("REQ-YG-020")` (python tool node). Reuse the
      existing REQ; do **not** mint a new CAP for an example spike.
- [ ] Per-agent throughlines are written to
      `results/l7/throughlines/<genre>/<agent>.md` and are **human-legible** — the
      attribution artifact for any recall miss (comprehension vs encoding).
- [ ] **KILL must be attributable** (the FR's diagnostic value): the verdict states
      *which stage flooded/missed* by reading the stored throughlines before the
      aggregate — did the **prose itself miss the guilt/betrayal arc** (→ subject-axis
      framing falsified at this tier; FR-578 scale justified), or was the **prose
      right but the encode mis-kinded it** (→ the encode prompt is the bug, framing
      still untested)?
- [ ] One prompt-wording iteration only (FR-584 fourth-iteration lesson). No GT
      leakage, no gate-threshold change, no LLM in `combine_affects`, no larger model
      before this axis is tested.
- [ ] Diary reflection recorded (satisfies `diary-gate`); changelog fragment with
      `req: REQ-YG-020` (satisfies `changelog-req-gate`).

## Stop Rule

This is L7's **first** subject-axis attempt — `audit_as_ritual` is not yet live. But
commit the escalation now: **on a clean, attributed KILL where the throughline prose
itself misses the moral-relational arcs**, the next lever is **model scale**
(FR-578's reserved escalation, with the throughline prompt as the larger model's
input) — not a second wording reframe. State this so the escalation is decided on
evidence, not deferred.

## Alternatives Considered — head-to-head with the L5 precedent

| Layer | Decomposition axis | Hard property handled by | Baseline | Target | precedent verdict |
|-------|--------------------|--------------------------|----------|--------|-------------------|
| L5 (584) | none (global pass) | LLM, fused | precision 0.30 | — | flat |
| L5 (585/587) | **operation** | LLM / deterministic code | `at`-FP 69–86 | — | KILL ×2 |
| L5 (**590/591**) | **subject — per-agent** | **the framing itself** | — | precision ↑ | **promoted to graph** |
| L7 (578) | none (global pass) | LLM, fused | recall 0.09 | — | REVISE (stuck) |
| L7 (**596**) | **subject — per-agent** | **the framing itself** | recall 0.09 | **≥ 0.50** | **spike** |

**Why this is the proven lever, not a re-skin.** FR-590/591 established that the
per-character viewpoint is *"the correct authoring primitive — character arcs are the
seam along which a synopsis is elaborated into a full plot."* Affect arcs are the
purest instance of that seam: they are *defined* per character. FR-578 fought the
flood with wording and scale; this moves one layer earlier — change *what is
comprehended* (one character's emotional story) rather than *how the global
comprehension is represented*.

**Alternatives rejected:**

- **Bigger model on the global framing.** Already falsified for L7 — haiku→sonnet was
  invariant (0.12→0.09). Scale pays before testing whether the wound is the framing;
  reserved only as the post-KILL escalation per the Stop Rule.
- **Decompose the *metric* only (sub-axis recall) without changing generation.**
  Rejected as the *primary* move: it measures the wound better but does not heal it
  (the FR-595 metric-fix reflex, correctly subordinated here to the structural cure).
  Retained as the Gate-1 *instrument*.
- **Per-kind or per-beat decomposition.** Rejected: kinds and beats have no narrative
  voice; the per-character throughline is the model's strongest compression mode and
  every `AffectDelta` is agent-owned.
- **Wording iteration #N on the monolithic prompt.** Rejected: FR-578 already
  exhausted the global framing; a fifth wording pass is the `audit_as_ritual` trap.

## Risks (Red Hat)

1. **Per-character framing under-emits genuinely shared arcs** (a death two
   characters both grieve). Mitigated: affect is feeler-owned; each cell emits its
   own delta, union recall ≥ per-beat recall *if* each agent narrates their own
   feeling. The detection-recall ≥ 0.70 gate exists to falsify this.
2. **Relational ownership ambiguity** (`betrayal` toward B felt by A). Mitigated: the
   feeler owns the delta, `toward` is a reference — *cleaner* than L5's symmetric
   `rel` (no dedup needed at all).
3. **Beat-id misalignment at combine** — the encode prompt MUST key every delta to a
   shared beat id. Enforced by the prompt contract + a combine unit test.
4. **N× LLM calls** (N agents). Accepted: the map node parallelizes; this is a
   quality spike, not a perf one.
5. **The throughline invents emotional weight the GT does not score** (precision
   risk). Accepted for Gate 1 — recall is the bar; precision is reported, not gated
   (FR-578 C2).

## Gate-1 Outcome — KILL (per-cast map falsified; `affect_recall` demotion indicated → FR-597)

Ran `examples/plot_modeller/spike_affect.py` on `claude-haiku-4-5` over the 5 GT
fixtures, mapping over the **GT agent roster** (correction #1). Log:
`logs/fr596-gate1.log`.

| Axis (frozen FR-578 gate + additive diagnostics) | Result |
|---|---|
| **affect_recall (official gate)** | **0.09 (3/33)** — KILL, flat vs FR-578 baseline |
| affect_precision | 0.03 (3/117) — **collapsed** (full-cast over-generation) |
| agent-coverage ceiling | 1.00 (5/5) — isolation clean; recall is not roster-capped |
| detection recall (op+char) | 0.55 (18/33) — inflated by over-generation + free `char` |
| kind \| detection | 0.17 (3/18) |
| toward \| relational detection | 0.00 (0/10) |

**Attributed root cause (the spike's real finding).** The GT affect layer is authored
as a **single protagonist's emotional throughline**, not a cast-distributed property.
Every fixture's affects sit on exactly one character:

```
detective→Marren(8)  historical→Naima(6)  horror→Brynn(5)
quest→Eira(6)        scifi→Mara(8)
```

Mapping `affect_throughline` over the **full** GT cast therefore emits ~N× the GT
volume (117 predicted vs 33 GT), destroying precision and burying the protagonist
arc in non-scored cast affect. The per-agent decomposition that cured L5 does **not**
transfer to L7, because L5 world-state genuinely *is* multi-perspective whereas L7
affect, in this corpus, is **mono-perspective (protagonist-owned)**. Risk #1
("under-emits shared arcs") and Risk #5 (precision) were under-stated: the GT is not
"shared arcs" but a single arc.

**Flavor (correction #3).** This is **neither** clean PROSE-MISSED **nor** simple
ENCODE-MISKINDED — detection 0.55 is *inflated by over-generation*, so it does not
license reading the framing as confirmed. The dominant lever is **structural, not
model-scale**: model scale stays unjustified (the Stop Rule holds — no clean
attributed prose-missed KILL).

**Manual inspection — numbers lie (the deeper root cause).** Beyond the cast-flood,
hand-comparison of the detective output against GT revealed a second, independent
failure the recall scalar conflates. Restricting to the protagonist (Marren) alone —
i.e. *granting* the protagonist-throughline fix in advance — the prediction still
misses on every sub-axis at once:

| Beat | predicted (Marren) | GT (Marren) |
|---|---|---|
| F1 | — | open loss |
| F2 | open loss, open hidden_blessing | — |
| F4 | open **guilt → Pell** | open **betrayal → Hagen** |
| F5 | close guilt → Pell | close loss, open hope |
| F6 | close loss, close hidden_blessing | close betrayal → Hagen |
| F7 | open hope, close hope | open hidden_blessing |
| F8 | — | close hidden_blessing, close hope |

The model's Marren throughline is coherent and beat-anchored — it narrates her
**empathy toward the witness she protects (`guilt → Pell`)**. The GT encodes her
**moral relation to the antagonist (`betrayal → Hagen`)**. *Both readings regenerate
the same beats.* The sparse affect skeleton cannot distinguish them, so `affect_recall`
scored a miss on what is narratively a valid second reading.

**Cross-genre confirmation (`numbers lie` is structural, not detective-specific).**
The GT affect skeleton is uniformly **mono-protagonist and radically sparse** — 5–8
deltas spanning ~3–4 matched `open…close` arcs on one character, across all five
genres (detective→Marren 8, historical→Naima 6, horror→Brynn 5, quest→Eira 6,
scifi→Mara 8). An ~8-token emotional skeleton is *far* sparser than L5's world-state
(dozens of `at`/`rel`/belief predicates) and encodes interior states with no unique
grounding in prose.

**Corrected root cause.** `affect_recall = 0.09` is the **`world_recall` pathology
one layer over, and worse**: it measures token-agreement against a sparse,
under-determined, mono-perspective skeleton — not whether the emotional story was
captured. FR-595 demoted `world_recall` at L5 for exactly this reason (the GT
world-state could not regenerate its own stories, scoring up to 1.00 underdetermined);
the L7 affect skeleton is *more* underdetermined still. Chasing 0.09 → 0.50 on this
ruler is chasing a number that lies. The cast-flood (precision) is real but is the
*shallower* of the two failures; under-determination caps recall even after the
protagonist fix.

**Indicated follow-up — two FRs, sequenced (new scope → back to Plan/Judge).**
The corrected root cause re-orders the work:

1. **FR-597 — L7 affect-regenerability ruler (the affect port of FR-594, FIRST).**
   Before any model effort is spent lifting the number, port the L5 regenerability
   probe to L7: feed the GT's *own* affect skeleton back and measure how
   underdetermined it is (predicted: ≥ L5's 0.70–1.00, given the greater sparsity).
   If GT is underdetermined, `affect_recall` is demoted as the L7 gate exactly as
   `world_recall` was at L5 — and FR-579's blocker is reframed: L7 is failing against
   a ruler that cannot measure affect capture, not because the encoder is weak.

2. **Protagonist-throughline, AGAINST the new ruler (provisional, SECOND).** Only
   after (1) reframes the gate: re-decompose along the single subject/protagonist
   agent (most-affect-bearing GT char, or the L4 `subject` axis) — one
   `affect_throughline` + `encode_affect` pass for that character, no full-cast map.
   This fixes the cast-flood (precision); the manual inspection above warns it will
   **not** by itself fix recall while the under-determined skeleton remains the
   target — hence it must follow, not precede, the ruler reframe.

Both are different decomposition/measurement axes than FR-596's granted GT-agents
map, so they are **out of FR-596's frozen scope** and deferred to follow-up FRs
rather than spent as the one permitted in-scope wording iteration (which a structural
mismatch would not heal anyway — `symptom_patch` avoided).

**Kept deliverables (tested, in scope):** `combine_affects` + `affect_balance`
(`nodes/tools.py`, 9 unit tests, REQ-YG-020), `prompts/affect_throughline.yaml`,
`prompts/encode_affect.yaml`, `spike_affect.py` (the Gate-1 instrument with the
3 sub-axis diagnostics + agent-coverage ceiling that produced this attribution).
The frozen FR-578 evaluator gate was **not** modified.

## Related

- FR-578 — the monolithic L7 baseline this FR decomposes (affect_recall 0.09).
- FR-590 / FR-591 — the L5 per-agent precedent: spike → proven → promoted to graph.
- FR-594 / FR-595 — the L5 regenerability ruler + `world_recall` demotion this
  analysis ports to L7 (the corrected root cause above is their L7 analog).
- FR-597 — the indicated L7 affect-regenerability ruler (affect port of FR-594),
  to run *before* any protagonist-throughline encoder work.
- FR-579 — the merge node blocked on L7 clearing its gate.
- `docs/diary/diary-2026-06-24-the-bigger-model-that-knew-less.md` — the model-
  invariance probe that pointed L7 upstream of the model tier (toward framing).
