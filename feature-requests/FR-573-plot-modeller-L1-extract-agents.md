# Feature Request: FR-573 Plot Modeller — L1 extract agents spike

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — Authority GRANTED (C1–C2 folded; 2026-06-24)
**Effort:** 1 day
**Requested:** 2026-06-23
**Plan:** [`plan-implementation-phases.md`](../examples/plot_modeller/docs/plan-implementation-phases.md) Phase 2a
**Predecessor:** FR-572 GO (vocabulary validation — **GO confirmed**, 2026-06-23)
**Blocks:** FR-574 (L2 goals), FR-579 (merge/pipeline)
**Data dependency:** None (L1 reads the synopsis directly)
**Scheduling dependency:** FR-572 (risk-control — spike after vocabulary confirmation; J:N1)

## Summary

Build the first extraction layer: given a prose synopsis, extract the cast of
agents, the initial world state (alive, at, holds, rel, faction), and the
initial beliefs. Spike against all 5 synopses (4 self-derived + 1 blind).

## Value statement

L1 is the pipeline's entry point. Every subsequent layer reads its output
(directly or indirectly). Getting the agent list and world state right is a
prerequisite for goals (L2), glosses (L3), and all formalization layers (L4–L7).
This is a low-risk, high-leverage layer — named entity extraction from prose is
a well-solved NLP task.

## Problem

The current pipeline has no extraction layers. The L4 spike (FR-570) operates in
Mode 1: glosses are extracted from ground-truth plans, not from prose. To run
the full pipeline, L1 must produce agents and world state from a raw synopsis.

## Proposed solution

### Graph: `graphs/extract_agents.yaml`

One LLM node + one validator node, following the LLM-validator-retry pattern
established by `classify_kinds.yaml`:

```
START → extract → validate → END (if ok)
                           → extract (if !ok, max 3 retries)
```

**State keys:**
- `synopsis` (input): the raw prose synopsis text
- `agents_raw` (LLM output): raw YAML text
- `agents` (validated output): parsed agent extraction
- `validation` (validator output): `{ok: bool, flaws: list[str]}`

### Prompt: `prompts/extract_agents.yaml`

The prompt instructs the LLM to extract from the synopsis:

1. **agents** — a list of named characters who act in the story
2. **initial_world** — the world state at the story's opening:
   - `alive` predicates for all agents
   - `at` predicates for agents whose starting location is stated
   - `holds` predicates for agents who possess named objects
   - `rel` predicates for stated relationships between agents
   - `faction` predicates for group memberships
3. **initial_belief** — beliefs that are explicitly stated as wrong, unknown,
   or uncertain at the story's opening (not the default "everyone knows
   everything" — only beliefs that are *marked* as non-default)

Output format: a single YAML document with three top-level keys (`agents`,
`initial_world`, `initial_belief`), matching the `PlotPlan` schema.

### Validator: `validate_agents` in `nodes/tools.py`

Checks:
1. Output is valid YAML with the expected top-level keys
2. `agents` is a non-empty list of strings
3. Every `initial_world` entry parses as a `Fluent` (pred, args, value)
4. Every `initial_belief` entry parses as a `Belief` (observer, fluent, held)
5. All agents referenced in world/belief entries appear in the agents list
6. Every agent has at least one `alive` predicate in `initial_world`

On success: writes `agents` (the full parsed extraction). On failure: writes
only `validation` with flaws (J1 pattern from FR-570).

### Runner: extend `run.py`

Add a Mode 2 flag (`--mode extract-agents`) that:
1. Loads each synopsis from `fixtures/synopses/`
2. Runs the `extract_agents` graph
3. Writes output to `results/l1/<genre>.yaml`
4. Compares against ground-truth agents

### Evaluator: extend `evaluate.py`

Add L1 evaluation:
- **Agent recall:** fraction of ground-truth agents found in the extraction
- **Agent precision:** fraction of extracted agents that are in ground truth
- **World state recall:** fraction of ground-truth initial_world predicates
  present in extraction (exact match on pred+args+value)
- **Belief recall:** fraction of ground-truth initial_belief entries present

The primary gate metric is **agent recall** (are all characters found?).
Precision matters less — an extra minor character is acceptable; a missing
protagonist is not.

## Deliverables

| File | What |
|------|------|
| `graphs/extract_agents.yaml` | L1 graph (LLM → validate → retry) |
| `prompts/extract_agents.yaml` | L1 extraction prompt |
| `nodes/tools.py` (extended) | `validate_agents` function |
| `run.py` (extended) | Mode 2: `--mode extract-agents` |
| `evaluate.py` (extended) | L1 evaluation (recall/precision) |
| `tests/test_l1_validator.py` | Unit tests for `validate_agents` |
| `results/l1/*.yaml` (5 files) | Extracted agents per genre |
| `results/evaluation/l1-summary.yaml` | Agent recall/precision across 5 synopses |

## Acceptance criteria

1. `validate_agents` catches: missing agents key, non-list agents, invalid
   fluent/belief structure, agent referenced in world/belief but not in agents
   list, missing alive predicates
2. L1 graph follows the LLM-validator-retry pattern (max 3 retries)
3. Agent recall ≥ 0.90 across the 5-synopsis corpus (gate metric)
4. No hardcoded provider/model in the graph or prompt
5. All extracted agents/world/belief entries parse into the FR-571 schema
   (`PlotPlan.model_validate` succeeds on the extraction output)
6. Existing L4 tests (FR-570) and schema tests (FR-571) still pass

## Evaluation output

```yaml
# results/evaluation/l1-summary.yaml
corpus:
  synopses: 5
  self_derived: 4
  blind: 1
agent_recall: "X/Y (0.XX)"
agent_precision: "X/Y (0.XX)"
world_recall: "X/Y (0.XX)"
belief_recall: "X/Y (0.XX)"
per_genre:
  detective-thriller-the-vanished-witness:
    agent_recall: "X/Y"
    agent_precision: "X/Y"
  # ... (all 5)
verdict: GO | REVISE | KILL
conditions:
  - "agent recall ≥ 0.90 for GO"
  - "borderline 0.70–0.90 defaults to REVISE (J:N2 — thresholds trigger,
     analysis decides)"
note: >
  World/belief recall are informational — the gate is on agents. World state
  extraction is harder (the model must infer predicates from prose) and is
  expected to be lower than agent recall.
```

## Go/no-go gate

| Outcome | Agent recall | Action |
|---------|-------------|--------|
| **GO** | ≥ 0.90 | Proceed to FR-574 (L2 goals) |
| **REVISE** | 0.70–0.90 | Analyze misses; revise prompt or extraction strategy; re-run |
| **KILL** | < 0.70 *and* incoherent error pattern | Re-evaluate L1 approach |

The KILL band is narrow (J:N2): with 5 synopses of ~5 agents each, a bare
miss-by-one is within noise. A KILL requires both a clear collapse *and* an
error pattern that does not point to a fixable prompt issue.

## What this FR does NOT do

- Does not extract goals (that's FR-574 / L2)
- Does not extract glosses (that's FR-575 / L3)
- Does not run L1 output through L2+ (that's FR-579 / orchestrator)
- Does not add new validators to `validators/` (L1 output is validated by the
  tool function, not by the plan validators — plan validators run on complete
  plans, not partial extractions)
- Does not modify the schema (FR-571 already covers all needed types)

## Judgement (2026-06-24)

**Verdict: GRANTED with conditions.** Predecessor check passes — FR-572
returned GO (blind 0.90, overall 0.81), verified in
[summary.yaml](../examples/plot_modeller/results/evaluation/summary.yaml), so
the "GO confirmed" header is factual, not aspirational. The data/scheduling
dependency split (J:N1) and narrow KILL band (J:N2) are both honored. Two
conditions, one shared root cause.

### C1 — `world_recall` exact match contradicts the repo's own tolerant-match law

AC's evaluator scores world state by "exact match on pred+args+value." Args are
*names the LLM chose* — "Moussa Keita" vs "Moussa" vs "Keita"; a location arg
like "the salt road" vs "Timbuktu road." One naming variance = a miss. This is
exactly the trap FR-570 already solved with **tolerant subject matching**, and
the diary's standing cure: *tolerant_matching — prefix/contains/regex, not exact
equality for LLM*. Exact match here will report a near-zero `world_recall` that
means "the model named things differently," not "the model got the world wrong."
**Fold:** normalize args (case/whitespace/article-strip) and match
contains/prefix, OR explicitly declare `world_recall` a rough lower bound in the
evaluation note. The gate is on agents, so this does not move the verdict — but
an uncorrected 0.1 world_recall will be misread as a defect.

### C2 — `belief_recall` is measured against unrecoverable ground truth (declare it)

The prompt correctly extracts only beliefs *marked* non-default in the synopsis.
But ground-truth `initial_belief` was authored by someone who knew the whole
plot — those beliefs encode dramatic irony that pays off in later chapters and
may never be *stated at the opening* of a 500-word synopsis. This is the FR-570
J2 self-derived-leakage problem, now at the belief layer: a low `belief_recall`
is the *expected, correct* outcome of reading the synopsis alone, not a bug to
chase. **Fold:** state in the evaluation note that `belief_recall` is
informational and expected to be low — ground-truth beliefs are an upper bound
authored with full-plot knowledge.

### Folded

C1 → tolerant world matching or a declared lower-bound. C2 → note belief recall
expected-low (J2 leakage). AC#3's binding agent-recall ≥ 0.90 gate, the
LLM-validator-retry reuse, and the no-hardcoded-provider rule are all sound.
Proceed to Enforce: validator RED first, then graph + prompt + evaluator.
