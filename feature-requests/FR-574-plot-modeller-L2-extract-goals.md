# Feature Request: FR-574 Plot Modeller — L2 extract goals spike

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — Authority GRANTED (C3–C4 folded; 2026-06-24)
**Effort:** 0.5 day
**Requested:** 2026-06-23
**Plan:** [`plan-implementation-phases.md`](../examples/plot_modeller/docs/plan-implementation-phases.md) Phase 2b
**Predecessor:** FR-573 (L1 extract agents)
**Blocks:** FR-579 (merge/pipeline)
**Data dependency:** L1 output (agents list — needed to scope goal extraction)
**Scheduling dependency:** FR-573 (risk-control; J:N1)

## Summary

Build the goal extraction layer: given a synopsis and the extracted agent list,
identify the story's goals as typed `Fluent` predicates. Spike against all 5
synopses using ground-truth agents (isolate L2 from L1 errors).

## Value statement

Goals define what the story is trying to achieve. They scope the reachability
check (Phase 4) and inform causality analysis (L6). Without explicit goals, the
plan has structure but no direction — the merge node cannot verify that the plot
reaches its intended endpoint.

## Problem

No pipeline layer currently extracts goals. The ground-truth plans have
hand-authored `goals` sections, but the pipeline cannot produce them from prose.

## Proposed solution

### Graph: `graphs/extract_goals.yaml`

Same LLM-validator-retry pattern. The LLM receives:
- The synopsis text
- The extracted agent list (from L1 or ground truth for the spike)

**State keys:**
- `synopsis` (input): prose synopsis
- `agents` (input): agent list from L1
- `goals_raw` (LLM output): raw YAML text
- `goals` (validated output): parsed goals
- `validation`: `{ok: bool, flaws: list[str]}`

### Prompt: `prompts/extract_goals.yaml`

Instructions:
1. Identify the story's goals — what outcomes does the plot drive toward?
2. Express each goal as a `Fluent` predicate: `{pred, args, value}`
3. Use the 5-predicate vocabulary: `alive`, `at`, `holds`, `rel`, `faction`
4. Goals should be end-state conditions — what must be true when the story
   resolves (or fails to resolve)
5. Typical goals: "character survives" (`alive`), "character reaches location"
   (`at`), "character possesses object" (`holds`), "relationship restored" (`rel`)

Output: a YAML list of `Fluent` objects.

### Validator: `validate_goals` in `nodes/tools.py`

Checks:
1. Output is valid YAML, a list of mappings
2. Each entry parses as a `Fluent` (pred in {alive, at, holds, rel, faction})
3. All agents referenced in goals appear in the agent list
4. At least one goal exists
5. No duplicate goals (same pred+args+value)

### Evaluation

Goal matching is structural: a ground-truth goal `{pred: alive, args: [X],
value: true}` matches if the extraction contains an identical predicate.

Metrics:
- **Goal recall:** fraction of ground-truth goals present in extraction
- **Goal precision:** fraction of extracted goals present in ground truth

The primary gate metric is **goal recall** — missing a critical goal is worse
than inventing an extra one.

## Deliverables

| File | What |
|------|------|
| `graphs/extract_goals.yaml` | L2 graph |
| `prompts/extract_goals.yaml` | L2 prompt |
| `nodes/tools.py` (extended) | `validate_goals` function |
| `run.py` (extended) | Mode 2: `--mode extract-goals` |
| `evaluate.py` (extended) | L2 evaluation |
| `tests/test_l2_validator.py` | Unit tests for `validate_goals` |
| `results/l2/*.yaml` | Extracted goals per genre |
| `results/evaluation/l2-summary.yaml` | Goal recall/precision |

## Acceptance criteria

1. `validate_goals` catches: invalid fluent structure, unknown predicate,
   agent not in agent list, empty goal list, duplicate goals
2. L2 graph follows the LLM-validator-retry pattern (max 3 retries)
3. Goal recall measured and reported across all 5 synopses
4. No hardcoded provider/model
5. All extracted goals parse as `Fluent` objects (FR-571 schema)
6. Existing tests unchanged

## Go/no-go gate

| Outcome | Goal recall | Action |
|---------|------------|--------|
| **GO** | ≥ 0.80 | Proceed to FR-575 (L3 glosses) |
| **REVISE** | 0.50–0.80 | Analyze misses; revise prompt |
| **KILL** | < 0.50 *and* incoherent pattern | Re-evaluate goal extraction |

Goal extraction is inherently ambiguous — reasonable humans disagree on what
counts as a "goal." The threshold is lower than L1's agent recall because goals
require inference, not just entity recognition. Thresholds trigger; the analysis
decides (J:N2).

## What this FR does NOT do

- Does not extract agents (that's FR-573 / L1)
- Does not extract glosses (that's FR-575 / L3)
- Does not use L1's extracted agents — the spike uses ground-truth agents to
  isolate L2's accuracy from L1's

## Judgement (2026-06-24)

**Verdict: GRANTED with conditions.** Isolating L2 with ground-truth agents is
the right experimental design, and the lower threshold (≥ 0.80) is justified by
goal-inference ambiguity. Two conditions.

### C3 — goal matching is *more* exposed to the exact-match trap than L1, not less

"Structural match: identical predicate" fails harder for goals than for world
state (C1 in FR-573), because goals add two free-form axes:

- **Arg order** on symmetric predicates: ground-truth `rel [A, B]` vs extracted
  `rel [B, A]` is the *same* relationship, scored as a miss.
- **Value strings**: "relationship restored" → `value: restored` vs `reconciled`
  vs `lovers` — all defensible, all unequal under exact match.

The diary cure applies verbatim: *prefix/contains/regex, not exact equality.*
**Fold:** order-insensitive args for symmetric predicates (`rel`, `faction`),
tolerant value comparison (normalize + contains), or declare `goal_recall` a
lower bound. Without this, a working L2 can score 0.5 purely on naming and trip
a false REVISE.

### C4 — AC#3 and the go/no-go table disagree on whether 0.80 is binding

FR-573 AC#3 reads "Agent recall ≥ 0.90 (gate metric)" — a *binding* acceptance
criterion. This FR's AC#3 reads only "Goal recall measured and reported" — the
≥ 0.80 lives solely in the go/no-go table. So is 0.80 an AC the FR must meet, or
just the proceed-decision? The two sibling FRs use opposite conventions. **Fold:**
pick one and apply it to both. Recommended: the *spike* FR is "done" when the
number is measured and a GO/REVISE/KILL verdict is recorded (the gate decides
whether to proceed) — then FR-573 AC#3 should be softened to match, not FR-574
tightened. Either way, state it once so a future reader knows whether a 0.74
fails the FR or merely triggers REVISE.

### Folded

C3 → tolerant goal matching (order-insensitive + value-tolerant). C4 →
reconcile the AC-vs-gate convention across FR-573/574. The validator checks and
L1-isolation design are otherwise sound. Proceed to Enforce.
