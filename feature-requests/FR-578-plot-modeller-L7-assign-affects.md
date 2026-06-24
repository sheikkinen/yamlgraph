# Feature Request: FR-578 Plot Modeller — L7 assign affects spike

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced — REVISE (affect recall 0.12 haiku / 0.09 sonnet-4-6; model-invariant kind-axis confusion, 2026-06-24)
**Effort:** 1 day
**Requested:** 2026-06-24
**Judged:** 2026-06-24
**Plan:** [`plan-implementation-phases.md`](../examples/plot_modeller/docs/plan-implementation-phases.md) Phase 3c
**Predecessor:** FR-577 (L6 causality — scheduling dependency per J:N1)
**Blocks:** FR-579 (merge/pipeline)
**Data dependency:** L3 glosses + L4 kinds + L1 agents (the spike uses ground-truth data to isolate L7)
**Scheduling dependency:** FR-577 (risk-control sequence; J:N1)

## Summary

Build the **affect arc** layer: given classified beats (gloss + kind) and the
agent list, assign emotional affect operations — `eff_affect`, a list of
`AffectDelta` objects describing which emotional arcs open or close at each
beat. Spike against all 5 synopses using ground-truth glosses, kinds, and agents
(isolate L7 from upstream error).

## Value statement

Affect arcs give the plan its emotional skeleton. Without them the plan has
causal structure (L5/L6) but no model of what characters *feel* — which arcs of
loss, guilt, betrayal, or hope open and close across the narrative. The merge
node (FR-579) uses `eff_affect` to validate emotional completeness: the
`affect_policy: unclosed_is_error: true` constraint requires every opened arc to
close somewhere in the function sequence.

## Problem

No pipeline layer assigns affect operations. The ground-truth plans have
hand-authored `eff_affect` lists per beat, but the pipeline cannot produce them.
Unlike L5 (generative predicate invention), L7 classifies into a **closed enum**
(6 `AffectKind` values) with constrained structure (`op` is binary, `char` and
`toward` are drawn from the agent list). The challenge is not vocabulary but
**placement**: knowing *which* beats carry emotional weight and *which* arc
opens or closes there.

## Proposed solution

### Graph: `graphs/assign_affects.yaml`

Same LLM-validator-retry pattern:

```
START → assign → validate → END (if ok)
                          → assign (if !ok, max 3 retries)
```

**State keys:**
- `glosses` (input): classified beats `{id, gloss, chapter, kind, subject}`
- `agents` (input): agent list from L1
- `affects_raw` (LLM output): raw YAML text
- `affects` (validated output): parsed per-beat affect slices
- `validation`: `{ok: bool, flaws: list[str]}`

L7 processes the **whole beat list in one call** — affect arcs span multiple
beats (an `open` in F3 may `close` in F9), so cross-beat context is essential.

### Prompt: `prompts/assign_affects.yaml`

For each beat, assign `eff_affect` — a list of `AffectDelta` objects (may be
empty). Each delta has:
- `op`: `"open"` or `"close"`
- `char`: the character experiencing the affect (must be in agents)
- `kind`: one of the 6 `AffectKind` values (`loss`, `guilt`, `betrayal`,
  `retaliation`, `hidden_blessing`, `hope`)
- `toward`: the target character for relational affects (`guilt`, `betrayal`);
  `null` for non-relational kinds

**Placement guidance.** The prompt must instruct:
- Structural beats (mediation, departure, pursuit, donor_test) typically have
  empty `eff_affect` — they advance the plot mechanically, not emotionally.
- Emotional beats (villainy, provision, victory, punishment, liquidation) are
  where arcs open and close.
- Every `open` must have a matching `close` later in the sequence — plan for
  arc closure before emitting `open` operations.
- Use character names **exactly as they appear in the agents list**.

Output: a YAML list of `{id, eff_affect}` objects, one per beat.

### Validator: `validate_affects` in `nodes/tools.py`

Checks (J1 contract — writes `affects` only on full success, else only
`validation`):

1. Output is valid YAML, a list of mappings with `id` key
2. Every beat ID from glosses is covered (no gaps, no orphans)
3. Each `eff_affect` item validates as `AffectDelta` (`model_validate`, strict,
   `extra="forbid"`)
4. `kind` is a valid `AffectKind` enum value
5. `op` is `"open"` or `"close"`
6. `char` is in agents list
7. `toward` (if present) is in agents list
8. Missing `eff_affect` key defaults to empty list

### Evaluator: extend `evaluate.py`

Add L7 evaluation. Per-beat matching:
- For each GT beat, compare its `eff_affect` entries against the predicted beat
- Match criteria: same `op` (exact), same `char` (tolerant — lowercase, strip),
  same `kind` (exact — closed enum), and `toward` matched **symmetrically**
  (J:C3): GT-null matches predicted-null OR an absent `toward` key; GT-non-null
  requires predicted-non-null with tolerant char match. A GT-null matched
  against a hallucinated non-null `toward` is a **precision miss**, not a free
  pass.
- **Recall:** GT affects matched by prediction / total GT affects
- **Precision:** predicted affects matched by GT / total predicted affects
  (reported alongside recall in the gate report — over-emission detector, J:C2)
- **Open/close balance:** informational — does the predicted sequence have every
  `open` matched by a `close`? Reported but does not gate.

### Runner: extend `run.py`

Add `--mode assign-affects`:
1. Load each ground-truth plan's glosses, kinds, and agents (Mode 1 isolation)
2. Run the `assign_affects` graph
3. Write output to `results/l7/<genre>.yaml`
4. Compare against ground-truth `eff_affect`

## Deliverables

| File | What |
|------|------|
| `graphs/assign_affects.yaml` | L7 graph (LLM → validate → retry) |
| `prompts/assign_affects.yaml` | L7 prompt (placement guidance + arc closure) |
| `nodes/tools.py` (extended) | `validate_affects` function |
| `run.py` (extended) | Mode: `--mode assign-affects` |
| `evaluate.py` (extended) | L7 evaluation (per-affect matching, recall/precision) |
| `tests/test_l7_validator.py` | Unit tests for `validate_affects` (incl. J1 contract) |
| `results/l7/*.yaml` (5 files) | Assigned affects per genre |
| `results/evaluation/l7-summary.yaml` | Affect recall/precision + balance check |

## Acceptance criteria

1. **RED first:** `test_l7_validator.py` written and failing before implementation
2. `validate_affects` catches: orphan/missing IDs, invalid AffectDelta structure,
   unknown AffectKind, character not in agents, invalid `toward`
3. L7 graph follows the LLM-validator-retry pattern (max 3 retries)
4. `kind` matching is **exact** (closed 6-value enum — no tolerance needed)
5. `char`/`toward` matching is **tolerant** (lowercase, strip whitespace)
6. **Affect recall >= 0.70** across the 5-synopsis corpus is the gate metric
7. No hardcoded provider/model in the graph or prompt
8. All generated affects parse into `AffectDelta` (FR-571 schema)
9. Open/close balance reported (informational, not gating)
10. Verdict recorded: GO / REVISE / KILL with confusion analysis
11. **Affect precision** reported alongside recall (over-emission detector, J:C2)
12. **Execution gated:** enforcement does not begin until FR-577 records a
    verdict (J:N1/R1 — evidence-gated serialization; both layers are
    GT-isolated, so parallel drafting is fine, only serial execution is required)

## Evaluation output

```yaml
# results/evaluation/l7-summary.yaml
corpus:
  synopses: 5
  isolation: ground-truth glosses + kinds + agents (Mode 1)
affect_recall:    "X/Y (0.XX)"   # GATE metric
affect_precision: "X/Y (0.XX)"
open_close_balance:
  balanced: true|false
  unclosed: [...]                 # informational
per_genre:
  detective-thriller-the-vanished-witness: { recall: "X/Y", precision: "X/Y" }
  # ... (all 5)
verdict: GO | REVISE | KILL
conditions:
  - "affect recall >= 0.70 for GO"
  - "borderline 0.50-0.70 defaults to REVISE (J:N2)"
```

## Go/no-go gate

| Outcome | affect recall | Action |
|---------|--------------|--------|
| **GO** | >= 0.70 | Proceed to FR-579 (merge/pipeline) |
| **REVISE** | 0.50-0.70 | Analyze confusion (wrong kind? wrong char? wrong placement?); revise prompt; re-spike |
| **KILL** | < 0.50 *and* incoherent confusion pattern | Re-evaluate L7 approach |

J:N2 applies: the threshold is a trigger; the confusion analysis carries the
verdict. A bare miss near 0.50 with a coherent, fixable error cluster (e.g.
systematic kind confusion between `loss` and `guilt`) is a REVISE, not a KILL.

## Out of scope

- **Open/close balance enforcement in the validator** — the validator checks
  structural correctness (valid AffectDelta, known chars, valid kinds) but does
  NOT enforce that every `open` has a matching `close`. Balance enforcement is a
  plan-level invariant that belongs in the merge node (FR-579), not in the
  per-layer validator. The evaluator reports balance as informational.
- Does not assign pre/eff (L5) or causality (L6) — those are independent layers
- Does not run L7 on extracted (non-GT) data — the spike uses ground-truth
  inputs to isolate L7's accuracy
- Does not modify the schema (`AffectKind`, `AffectDelta` already exist in
  FR-571 `schema/affects.py`)

## Judgement (2026-06-24)

**Verdict: Authority GRANTED — execution gated behind FR-577.** L7 is the
lowest-vocabulary-risk layer in the chain: `kind` is a closed 6-value enum
(`AffectKind`), `op` is binary, `char`/`toward` are drawn from the provided
agent list. The schema is exactly as the FR describes
(`AffectDelta(op: Literal["open","close"], char, kind: AffectKind,
toward: str | None)`, `extra="forbid"`, `schema/affects.py`). The real
difficulty is *placement* (which beats carry affect, which arc opens/closes),
correctly identified. Four conditions folded.

### Verification against the data (checked, not assumed)

- **Schema confirmed exactly.** The 6 `AffectKind` values
  (`loss, guilt, betrayal, retaliation, hidden_blessing, hope`) and the
  `AffectDelta` structure match the FR's validator spec verbatim;
  `model_validate` with `extra="forbid"` rejects unknown keys as claimed.
- **GT has 48 `eff_affect` beat-keys** across the 5 synopses (one per beat); the
  affect-delta count (recall denominator Y) is the summed list length and is
  left open (`X/Y`) in the FR — correct, no false precision.
- **J1 contract uniform** — `validate_affects` matches the established
  write-on-success pattern (`validate_kinds/agents/goals/glosses`).

### C1 — keep balance enforcement OUT of the validator (confirm the boundary)

The FR already scopes open/close balance out of the validator and into the
merge node (FR-579), with the evaluator reporting balance as informational.
This is the correct architectural boundary and must hold: the per-layer
validator checks structural correctness (valid `AffectDelta`, known
chars/kinds), never the cross-beat plan invariant. Ratified and pinned so it is
not later smuggled into `validate_affects`.

### C2 — report precision, not only recall

Like L6, per-affect recall alone rewards over-emission (open an arc on every
emotional beat). The summary MUST report affect precision alongside recall (the
FR's evaluator section already computes both — this pins it into the gate
report) so over-emission is visible. The gate stays on recall ≥ 0.70.

### C3 — `toward` null-handling must be symmetric and explicit

Matching compares `toward` "tolerant, or both null." Make the rule explicit:
GT-null matches predicted-null OR absent key; GT-non-null requires
predicted-non-null with tolerant char match. A GT-null matched against a
hallucinated non-null `toward` is a **precision miss**, not a free pass —
otherwise the model can append spurious targets without penalty.

### C4 — `kind` exact-match is correct; do not add tolerance

The closed 6-value enum means `kind` matching is exact (no tolerance), unlike
the open free-text labels of L2/L5. This is correct and is *why* L7 is
lower-risk. Pinned so no one later adds fuzzy kind matching that would mask
systematic kind confusion (e.g. `loss`↔`guilt`) — the exact signal the
confusion analysis needs.

### Carried forward unchanged (validated as correct)

- LLM→validate→retry, Mode-1 GT isolation, J1 contract, no hardcoded
  provider/model, RED-first tests, gate ≥ 0.70 with J:N2
  (confusion-carries-the-verdict) — all sound and correctly inherited.
- Placement guidance (structural beats empty, emotional beats carry arcs) is the
  right prompt lever; whether it suffices is the spike's question.

### Scheduling (J:N1 / R1) — the binding condition

FR-578 declares FR-577 as a scheduling dependency. Authority is granted to draft
and (later) enforce, but **enforcement MUST NOT begin until FR-577 records a
verdict**. Planning depth may run one layer ahead; evidence depth governs
execution order (R1). Both layers are GT-isolated, so a parallel draft is sound
— only serial execution is required.

**Frozen scope:** the eight deliverables as listed, with C2 (precision reported)
and C3 (explicit null-handling). Gate: affect recall ≥ 0.70,
denominator-visible, verdict by confusion analysis. One spike, record verdict —
after FR-577.

## Implementation (2026-06-24)

**Verdict: REVISE.** The gate (affect recall ≥ 0.70) is not met, but the
sub-threshold result is carried by a **coherent, model-invariant confusion**
(J:N2) — not the incoherent failure that a KILL requires. Two spikes were run
under Mode-1 isolation (ground-truth glosses + kinds + agents):

| Model (verified in log: `Creating LLM: anthropic/...`) | affect recall | affect precision |
|---|---|---|
| `claude-haiku-4-5` | 4/33 (0.12) | 4/42 (0.10) |
| `claude-sonnet-4-6` | 3/33 (0.09) | 3/46 (0.07) |

### Decisive finding — the bottleneck is not model capability

Scaling haiku → sonnet-4-6 did **not** move the gate (0.12 → 0.09, within noise;
precision also flat-to-down). Both `Creating LLM` log lines were verified, so the
swap genuinely took effect via `ANTHROPIC_MODEL` → `create_llm()`. A 6×-stronger
model cannot brute-force the gap, which means the limitation is in the **task
framing**, not the LLM. This redirects the revision hypothesis away from "use a
bigger model."

### Confusion analysis (identical axis under both models)

Comparing GT vs predictions per beat across all 5 genres:

- **`char` is almost always correct** — the model reliably identifies *who* the
  emotion belongs to (Naima, Eira, Mara).
- **`op` (open/close) is roughly correct** — it tracks *when* emotional onset /
  resolution lands (the right beats carry arcs).
- **`kind` is the dominant error axis** — the model over-emits generic
  `hope`/`loss`/`retaliation` and systematically *misses* the moral-relational
  kinds (`guilt`, `betrayal`). Examples: GT `guilt`→PRED `hope` (scifi F2,
  both models); GT `loss(toward Jonas)`→PRED `betrayal(toward ARIA)` (scifi F6);
  GT `betrayal(toward ARIA)` missed or mis-kinded (scifi F7).
- **`toward` (relational target) is mis-targeted** — Jonas ↔ ARIA swapped
  (scifi F6/F10), and several relational arcs dropped entirely.
- **Open/close *pairing* is not tracked** — the close timing is roughly right but
  *which kind closes* is shuffled (historical F6/F9: `loss`↔`hope` swap).

The model recovers **who** and **roughly when**, but cannot recover the authors'
specific **emotional kind** — especially the moral-relational arcs that require
reading inter-character moral debt (guilt/betrayal toward a named target) out of
a one-line gloss + Proppian kind. This is a stable signal, not stochastic noise:
the same axis appears across both models and all genres.

### Revision hypothesis (for the re-spike before FR-579 integration)

The exact-match `kind` enforcement (C4) is correct and stays — it is *what
exposed* the kind-axis confusion; fuzzy matching would have masked it. The fix is
not the matcher and not the model; candidate levers, in order of expected
leverage:

1. **Decompose the task**: split affect assignment into (a) "does this beat carry
   emotional weight?" and (b) "name the kind + relational target," rather than a
   single per-beat pass — the placement signal (char + op) is already strong and
   should be preserved while the kind classifier is strengthened.
2. **Ground the relational kinds**: give the prompt explicit definitions /
   exemplars for `guilt` and `betrayal` and *require* a `toward` target for them,
   since the moral-relational arcs are the systematic blind spot.
3. **Track open/close pairing**: feed the running set of open arcs so a `close`
   names the same `kind`+`char` it opened, fixing the pairing shuffle.
4. **Reconsider the input**: gloss + kind may be too thin to recover authorial
   affect; richer beat context (or L5/L6 effects) may be required input for L7.

Per J:N2 the gate number triggers and the confusion carries the verdict: a
coherent, prompt-addressable failure cluster → **REVISE**, not KILL. L7 does
**not** pass to the merge node (FR-579) until a revised spike clears ≥ 0.70.

### Deliverables landed

- `graphs/assign_affects.yaml`, `prompts/assign_affects.yaml`
- `validate_affects` in `nodes/tools.py` (AffectDelta structural validation,
  closed-enum `kind`, agent membership for `char`/`toward`, J1 write-on-success;
  does **not** enforce open/close balance per C1 — that is the FR-579 merge node)
- `run.py --mode assign-affects` (Mode 7)
- `score_l7` / `summarise_l7` / `_load_gt_affects` / `main_l7` in `evaluate.py`
  (recall gate, precision over-emission detector C2, symmetric `toward`
  null-handling C3, informational open/close balance C1)
- `tests/test_l7_validator.py` (19 tests, RED→GREEN, J1 + C4 exact-enum)
- `results/l7/*.yaml`, `results/evaluation/*-l7-eval.yaml`,
  `results/evaluation/l7-summary.yaml`
- Spike logs: `logs/l7-spike.log` (haiku), `logs/l7-spike-sonnet.log` (sonnet-4-6)

FR-579 (merge/pipeline) remains blocked on a REVISE re-spike of L7 clearing the
0.70 gate.
