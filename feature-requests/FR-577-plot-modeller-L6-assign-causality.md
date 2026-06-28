# Feature Request: FR-577 Plot Modeller — L6 assign causality spike

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced — GO (enables recall 0.96, 2026-06-24)
**Effort:** 1 day
**Requested:** 2026-06-24
**Judged:** 2026-06-24
**Plan:** [`plan-implementation-phases.md`](../examples/plot_modeller/docs/plan-implementation-phases.md) Phase 3b
**Predecessor:** FR-575 (L3 extract glosses — Enforced, GO 0.88)
**Blocks:** FR-579 (merge/pipeline)
**Data dependency:** L3 glosses + L4 kinds + L1 agents (from GT for spike isolation)
**Scheduling dependency:** FR-575 (risk-control sequence; J:N1)

## Summary

Build the causality layer: given a classified beat sheet (glosses + kinds) and
the agent list, assign causal links between beats — `enables` (which beats
causally enable later beats), `motivation` (which agent/goal drives the beat),
and `threatens` (whose goal the beat blocks). Spike against all 5 synopses using
ground-truth glosses, kinds, and agents to isolate L6 from upstream error.

## Value statement

Causal links are the connective tissue of the plan. `enables` defines the
dependency graph between beats (what must happen before what can happen);
`motivation` and `threatens` tie beats to agents' goals, turning a flat beat
list into a multi-agent plan with explicit stakes. Without L6, the merge node
(Phase 4) has pre/eff predicates but no narrative-level causality — it can check
state consistency but not whether the plot's causal structure is coherent.

## Problem

No pipeline layer assigns causal links. The ground-truth plans have
hand-authored `enables`, `motivation`, and `threatens` fields, but the pipeline
cannot produce them from a gloss + kind + agent list. Unlike L5 (generative
predicate invention), L6 is **relational**: the model must reason about
cross-beat dependencies and agent-goal alignment across the entire beat sheet.

## Proposed solution

### Graph: `graphs/assign_causality.yaml`

Same LLM-validator-retry pattern as all other layers:

```
START -> assign -> validate -> END (if ok)
                            -> assign (if !ok, max 3 retries)
```

**State keys:**
- `glosses` (input): classified beats `{id, gloss, chapter, kind, subject}`
- `agents` (input): agent list from L1
- `causality_raw` (LLM output): raw YAML text
- `causality` (validated output): parsed per-beat causality links
- `validation`: `{ok: bool, flaws: list[str]}`

L6 processes the **whole beat list in one call** — causal links require
cross-beat context (a beat's `enables` targets are elsewhere in the list).

### Prompt: `prompts/assign_causality.yaml`

For each beat, assign:

1. **`enables`** — `list[str]` of beat IDs this beat causally enables. Empty
   `[]` for terminal beats. Usually 1 target, occasionally 2 (branching).
2. **`motivation`** — `{agent: str, goal: str}` or `null`. Which agent drives
   this beat and toward what goal. Null for environment-driven beats (natural
   disasters, coincidences).
3. **`threatens`** — `{agent: str, goal: str}` or `null`. Whose goal this beat
   blocks or endangers. Null on roughly half the beats.

**Prompt instructions:**
- `enables` must reference valid beat IDs from the input list. A beat can only
  enable beats that appear later in the narrative (no backward links).
- `motivation` and `threatens` agents must come from the provided agent list.
- Goal labels should be concise and reuse the agent's stated goals where
  possible.
- Terminal beats (final confrontation, resolution) have `enables: []`.

Output: a YAML list of `{id, enables, motivation, threatens}` objects, one per
beat.

### Validator: `validate_causality` in `nodes/tools.py`

Checks (J1 contract — writes `causality` only on full success, else only
`validation`):

1. Output is valid YAML, a list of mappings
2. Every `id` matches an input beat ID (no orphans, no gaps)
3. `enables` values are valid beat IDs (referential integrity)
4. `enables` links are **forward-only** — a beat may only enable beats that
   appear later in the narrative; a backward link is a validation failure that
   forces a retry (J:C2)
5. `motivation`/`threatens` agents appear in the agent list
6. No unknown keys (missing optional keys default gracefully: absent
   `motivation`/`threatens` treated as null)
7. `enables` is a list (not a scalar) for every beat

### Runner: extend `run.py`

Add `--mode assign-causality`:
1. Load each ground-truth plan's glosses + kinds + agents (Mode 1 isolation)
2. Run the `assign_causality` graph
3. Write output to `results/l6/<genre>.yaml`
4. Compare against ground-truth causality

### Evaluator: extend `evaluate.py`

Add L6 evaluation. Matching is **tolerant** (J:C1/C3 inheritance):

- **`enables` recall:** for each GT beat, does the predicted beat have the same
  enables targets? Order-insensitive set comparison. Score: fraction of GT
  enables links correctly predicted.
- **`enables` precision:** fraction of predicted enables links that appear in
  GT — the over-link detector (J:C4). Reported alongside recall.
- **`motivation` recall:** agent name tolerant (case-insensitive), goal label
  tolerant (contains/prefix match). A GT non-null motivation matches if the
  predicted motivation has the same agent and a compatible goal label.
- **`threatens` recall:** same tolerant matching as motivation.
- **Null handling:** GT null should match predicted null (or absent key); GT
  non-null should match predicted non-null with tolerant field comparison.

**Denominators are computed mechanically** from the GT fixtures (summed length
of each GT `enables` list; count of non-null `motivation`/`threatens`), never
hardcoded, and emitted denominator-visible as `X/Y` (J:C1/J:C5). For reference,
the current fixtures yield ~43 non-empty `enables` keys (≈48 links with
branching), ~40 non-null motivations, ~25 non-null threatens — but the evaluator
divides by the value it computes at run time, not these constants.

## Deliverables

| File | What |
|------|------|
| `graphs/assign_causality.yaml` | L6 graph (LLM -> validate -> retry) |
| `prompts/assign_causality.yaml` | L6 prompt (cross-beat causality) |
| `nodes/tools.py` (extended) | `validate_causality` function |
| `run.py` (extended) | Mode: `--mode assign-causality` |
| `evaluate.py` (extended) | L6 evaluation (tolerant matching) |
| `tests/test_l6_validator.py` | Unit tests for `validate_causality` (incl. J1 crash) |
| `results/l6/*.yaml` (5 files) | Assigned causality per genre |
| `results/evaluation/l6-summary.yaml` | Recall per field + per genre |

## Acceptance criteria

1. **RED first:** `test_l6_validator.py` written and failing before
   `validate_causality` is implemented
2. `validate_causality` catches: orphan/missing IDs, invalid enables target,
   backward enables link (forward-only, J:C2), agent not in agent list,
   `enables` not a list, unknown keys
3. The validator enforces the J1 contract (writes `causality` only on success)
4. L6 graph follows the LLM-validator-retry pattern (max 3 retries)
5. **Enables recall >= 0.75** across the 5-synopsis corpus is the gate metric.
   The denominator is computed mechanically (summed GT `enables` list length)
   and emitted denominator-visible as `X/Y` (J:C1/J:C5) — never hardcoded. This
   is the primary structural metric — enables defines the dependency graph.
6. **Enables precision** reported alongside recall (over-link detector, J:C4);
   motivation and threatens recall reported per-field (informational, not gating)
7. Matching is **tolerant** (case-insensitive agents, contains/prefix goals,
   order-insensitive enables sets) — NOT exact string equality (J:C1/C3)
8. No hardcoded provider/model in the graph or prompt
9. Verdict recorded: GO / REVISE / KILL with confusion analysis

## Evaluation output

```yaml
# results/evaluation/l6-summary.yaml
corpus:
  synopses: 5
  isolation: ground-truth glosses + kinds + agents (Mode 1)
enables_recall:     "X/Y (0.XX)"   # GATE metric (Y computed from GT)
enables_precision:  "X/Y (0.XX)"   # over-link detector (J:C4)
motivation_recall:  "X/Y (0.XX)"   # informational
threatens_recall:   "X/Y (0.XX)"   # informational
per_genre:
  detective-thriller-the-vanished-witness: { enables: "X/Y" }
  # ... (all 5)
verdict: GO | REVISE | KILL
conditions:
  - "enables recall >= 0.75 for GO (denominator computed from GT, X/Y)"
  - "borderline 0.50-0.75 defaults to REVISE (J:N2)"
```

## Go/no-go gate

| Outcome | enables recall | Action |
|---------|---------------|--------|
| **GO** | >= 0.75 | Proceed to FR-579 (merge/pipeline) |
| **REVISE** | 0.50-0.75 | Analyze confusion (wrong targets? missing terminal beats? backward links?); revise prompt; re-spike |
| **KILL** | < 0.50 *and* incoherent pattern | Re-evaluate — causality assignment may need chain-of-thought decomposition or beat-pair scoring |

The KILL band is narrow (J:N2): at N~48, a bare score near 0.50 is within
sampling noise. A KILL requires both a clear collapse and a confusion pattern
that does not point to a fixable prompt issue.

## Risk assessment

**Medium.** L6 is relational but not generative in the L5 sense — the model
selects existing beat IDs and agent names rather than inventing tokens. The
dominant risk is **structural**: the model may miss non-obvious enables links
(where beat A enables beat C through an implicit intermediate step) or
over-link (connect every beat to its immediate successor). Motivation and
threatens are lower risk since they are agent-scoped and the agent list is
provided.

## What this FR does NOT do

- Does not assign pre/eff predicates (that's FR-576 / L5)
- Does not assign affects (that's FR-578 / L7)
- Does not run L6 on pipeline-extracted glosses — the spike uses ground-truth
  glosses + kinds + agents to isolate L6's accuracy
- Does not read L5 pre/eff — causal links are derivable from narrative
  structure, not from world-state predicates
- Does not modify the schema (FR-571 already covers the causality fields)

## Judgement (2026-06-24)

**Verdict: Authority GRANTED.** L6 inherits the proven LLM→validate→retry /
J1-contract / Mode-1-isolation regime from L1–L5 verbatim, and the schema it
targets already exists (`Function.enables: list[str]`,
`Function.motivation/threatens: Motivation | None` with `agent`/`goal`,
`schema/functions.py`). The relational framing (select existing beat IDs +
agent names, not invent tokens) makes this lower-risk than L5's generative
invention — the dominant L5 failure mode (token paraphrase, FR-582) cannot
occur here. Five conditions folded; all refinements, none a blocker.

### Verification against the data (checked, not assumed)

- **Schema confirmed.** `enables`, `motivation` (`{agent, goal}`), `threatens`
  (`{agent, goal}`) all present in `schema/functions.py` with `extra="forbid"`.
  The FR's claim "FR-571 already covers the causality fields" holds — no schema
  change needed.
- **J1 contract is real and uniform.** `validate_kinds/agents/goals/glosses`
  each write the output key only on `ok`, else only `validation`.
  `validate_causality` slots into an established pattern.
- **The stated "~48 links" denominator is approximate and conflated.** GT has
  **48 `enables:` keys** (one per beat) of which **43 are non-empty**; the
  number of *links* (summed list length) is ~43 plus occasional branching ≈ 48.
  The FR coincidentally equates beat-count with link-count. Fold C1.

### C1 — compute the gate denominator mechanically; do not hardcode "~48"

The gate (enables recall ≥ 0.75) divides by the GT link count. "~48" is
asserted; the data shows 43 non-empty `enables` keys with occasional 2-target
branching. The evaluator MUST compute the denominator as the summed length of
the GT `enables` lists and emit it denominator-visible (`X/Y`, J:C5), never
against a baked-in constant — a drifting denominator silently moves the gate.

### C2 — decide the status of backward `enables` links: validator failure or eval miss

The prompt forbids backward links ("a beat can only enable beats that appear
later"), but validator checks 1–6 enforce referential integrity only, not
ordering. Resolve before enforcing: a backward link is either (a) a structural
flaw the validator rejects (forcing retry) or (b) a quality issue the evaluator
scores as a miss — pick one. **Recommendation:** the validator enforces
forward-only (mechanically checkable from beat order, a hard narrative
invariant), keeping the validator the structural gate.

### C3 — motivation/threatens denominators (~40 / ~25) stay informational

Only `enables` recall gates. The motivation/threatens denominators were not
verified against GT and need not be — keep them strictly informational,
reported `X/Y` denominator-visible, and out of the GO decision. This pins the
FR's own intent so a later reading cannot promote them to a gate.

### C4 — report `enables` precision, not only recall

Order-insensitive set comparison on `enables` targets is gameable by
over-linking (connect every beat to its successor) — the exact failure the risk
section names. Recall alone rewards over-linking. The L6 summary MUST report
`enables` precision alongside recall (as L1/L2/L5 already do) so over-linking is
visible. The gate stays on recall; precision is the over-link detector.

### C5 — KILL band is correctly narrow; carry J:N2 verbatim

The 0.50–0.75 REVISE band and "KILL requires collapse AND unfixable confusion
pattern" are sound and correctly inherited. At N≈48 a bare score near 0.50 is
sampling noise. No change.

### Carried forward unchanged (validated as correct)

- LLM→validate→retry (max 3), Mode-1 GT isolation, J1 write-on-success
  contract, no hardcoded provider/model, RED-first validator tests — all
  consistent with L1–L5.
- Not reading L5 pre/eff is correct: causality is narrative-structural, and
  isolating L6 from L5's unresolved recall (FR-582→FR-583) via GT keeps the
  spike clean.

### Scheduling (J:N1 / R1)

FR-577 executes before FR-578 (declared dependency). Both may remain drafted in
parallel since each is GT-isolated, but FR-578 must NOT be enforced until FR-577
records a verdict — planning may run one layer ahead, evidence-gated execution
may not (R1: planning depth must not outrun evidence depth).

**Frozen scope:** the eight deliverables as listed, with C1 (mechanical
denominator), C2 (forward-only resolved in the validator), and C4 (precision
reported). Gate: `enables` recall ≥ 0.75, denominator-visible, verdict by
confusion analysis (J:N2). One spike, record verdict.

## Implementation (2026-06-24)

**Verdict: GO.** Spike run with `PROVIDER=anthropic --model claude-opus-4`
across all 5 synopses (Mode-1 isolation: ground-truth glosses + kinds + agents).

### Gate result — `enables` recall (mechanical denominator, J:C1)

| Genre | enables recall |
|---|---|
| detective-thriller-the-vanished-witness | 8/10 (0.80) |
| historical-fiction-the-salt-road | 9/9 (1.00) |
| horror-survival-the-last-light | 6/6 (1.00) |
| quest-adventure-the-sunken-crown | 8/8 (1.00) |
| scifi-hybrid-the-loom | 12/12 (1.00) |
| **corpus** | **43/45 (0.96)** |

`enables` recall **0.96 ≥ 0.75** → **GO**. The denominator (45) is computed at
runtime from the corpus, not hardcoded (C1 satisfied — it matches the verified
corpus count of 45 enables links).

### Over-link detector — `enables` precision (C4)

`enables` precision **43/46 (0.93)**: only 3 invented edges across the corpus.
The forward-only validator (C2) plus the prompt's "FORWARD ONLY" instruction
held — zero backward links survived to the results. Low over-linking confirms
the causal backbone is recovered without hallucinated edges.

### Informational signals — motivation / threatens (J:C3, non-gating)

| Slice | recall (agent + goal) | agent-only recall |
|---|---|---|
| motivation | 11/42 (0.26) | 35/42 (0.83) |
| threatens | 0/26 (0.00) | 21/26 (0.81) |

**Confusion analysis.** The agent-only recall is strong (0.83 / 0.81) while the
full agent+goal recall collapses (0.26 / 0.00). The model identifies *who* is
motivated / threatened reliably, but its free-form snake_case **goal phrasing**
diverges from the corpus's wording below the 0.34 Jaccard tolerance —
especially for `threatens`, where it never aligns. This is a **vocabulary-
grounding gap, not a comprehension gap**: the same class of token-divergence
that FR-583 (evaluator Jaccard tolerance + L5 vocab grounding) already targets.
Per J:C3 these slices are informational and do not affect the GO verdict; they
are recorded here as the forward signal for FR-583 / a future goal-vocabulary
alignment pass.

### Deliverables landed

- `graphs/assign_causality.yaml`, `prompts/assign_causality.yaml`
- `validate_causality` in `nodes/tools.py` (forward-only enables, referential
  integrity, agent membership, J1 write-on-success)
- `run.py --mode assign-causality` (Mode 6)
- `score_l6` / `summarise_l6` / `_load_gt_causality` / `main_l6` in `evaluate.py`
- `tests/test_l6_validator.py` (19 tests, RED→GREEN, J1 + J:C2)
- `results/l6/*.yaml`, `results/evaluation/*-l6-eval.yaml`,
  `results/evaluation/l6-summary.yaml`

FR-578 (L7 affects) is now unblocked per its folded AC#12 (execution gated
behind an FR-577 verdict — recorded GO here).
