# Feature Request: FR-204 Five Whys Demo — Iterative Root Cause Analysis Pipeline

**Priority:** LOW
**Type:** Feature
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-27

## Summary

Add an `examples/demos/five-whys/` demo that performs the Five Whys root cause analysis technique: given a problem statement, iteratively asks "why?" five times, drilling deeper each iteration, then synthesises a root cause summary with actionable recommendations.

## Value Statement

New users see a real-world fixed-count loop pattern that accumulates structured results across iterations, demonstrating conditional edges, loop limits, Jinja2 state access, and exports — all in pure YAML with zero Python.

## Problem

The existing loop demos (`reflexion/`) use a self-correction loop (critique → refine until score ≥ threshold). There is no demo that:

1. Loops a **fixed number of times** with each iteration building on accumulated context.
2. Demonstrates **Jinja2 iteration over previous results** inside prompts.
3. Shows a **progressive deepening** pattern where each step's output feeds the next.
4. Produces a **structured final artifact** (root cause analysis document) via exports.

The Five Whys technique is universally understood, requires exactly the loop-with-accumulation pattern, and produces a tangible deliverable.

## Proposed Solution

### Directory layout

```
examples/demos/five-whys/
├── graph.yaml
├── README.md
└── prompts/
    ├── ask_why.yaml
    └── summarise.yaml
```

### `graph.yaml`

```yaml
version: "1.0"
name: five-whys
description: Five Whys root cause analysis — iterative deepening loop
prompts_relative: true
prompts_dir: prompts

defaults:
  temperature: 0.7

nodes:
  ask_why:
    type: llm
    prompt: ask_why
    variables:
      problem: "{state.problem}"
      iteration: "{state._loop_counts.ask_why}"
      previous: "{state.ask_why}"
    state_key: ask_why
    skip_if_exists: false

  summarise:
    type: llm
    prompt: summarise
    variables:
      problem: "{state.problem}"
      analysis: "{state.ask_why}"
    state_key: summary

edges:
  - from: START
    to: ask_why

  - from: ask_why
    to: ask_why
    condition: _loop_counts.ask_why < 5

  - from: ask_why
    to: summarise
    condition: _loop_counts.ask_why >= 5

  - from: summarise
    to: END

loop_limits:
  ask_why: 5

loop_exits:
  ask_why: summarise

exports:
  summary:
    format: markdown
    filename: root_cause_analysis.md
```

**Design rationale:**

- `skip_if_exists: false` ensures `ask_why` executes every iteration (overwriting via `last_value` reducer is intentional — the LLM returns the full `chain` each time, so no external accumulation is needed).
- `_loop_counts.ask_why` is auto-incremented by the framework (`node_factory/llm_nodes.py`) and accessed in conditions via `evaluate_condition()` (`utils/conditions.py`).
- `loop_limits` + `loop_exits` act as safety guards: if the conditional edge logic fails, the framework still terminates the loop and routes to `summarise`.
- `exports` produces `outputs/{thread_id}/root_cause_analysis.md` after execution via `storage/export.py`.
- `prompts_relative: true` + `prompts_dir: prompts` resolves prompt names relative to the graph file, following the pattern established in `hello/`, `reflexion/`, and other demos.

### `prompts/ask_why.yaml`

```yaml
schema:
  name: WhyAnalysis
  fields:
    why_number:
      type: int
      description: "Which 'why' iteration this is (1-5)"
    question:
      type: str
      description: "The 'why' question being asked"
    answer:
      type: str
      description: "The answer to this why question"
    chain:
      type: list[str]
      description: "All answers so far including this one"

system: |
  You are a root cause analysis expert using the Five Whys technique.
  Given a problem, ask "why?" repeatedly, each time digging deeper into
  the underlying cause. Each answer should be a concise causal statement.

user: |
  Problem: {problem}

  {% if previous and previous.chain %}
  Previous analysis:
  {% for answer in previous.chain %}
  Why {{ loop.index }}: {{ answer }}
  {% endfor %}

  Ask why #{{ (previous.chain | length) + 1 }}, digging deeper into the last answer.
  {% else %}
  This is the first "why". Ask why this problem occurs.
  {% endif %}

  Return the why question, your answer, and the full chain of all answers so far.
```

The LLM returns the full `chain` list on every iteration, so progressive context is maintained without a custom reducer. The `{% if previous and previous.chain %}` guard handles the first iteration (when `previous` is `None`).

### `prompts/summarise.yaml`

```yaml
schema:
  name: RootCauseSummary
  fields:
    problem:
      type: str
      description: "Original problem statement"
    root_cause:
      type: str
      description: "Identified root cause"
    chain:
      type: list[str]
      description: "The five why answers"
    recommendations:
      type: list[str]
      description: "Actionable recommendations to address root cause"

system: |
  You are a root cause analysis expert. Summarise the Five Whys analysis
  into a clear report identifying the root cause and recommending actions.

user: |
  Problem: {problem}

  Five Whys analysis:
  {% for answer in analysis.chain %}
  Why {{ loop.index }}: {{ answer }}
  {% endfor %}

  Identify the root cause and provide actionable recommendations.
```

### CLI usage

```bash
yamlgraph graph run examples/demos/five-whys/graph.yaml \
  --var problem="Deployment failed on Friday" --full
```

## Acceptance Criteria

- [ ] `yamlgraph graph lint examples/demos/five-whys/graph.yaml` passes
- [ ] `yamlgraph graph run` with `--var problem="..."` completes 5 loop iterations then summarises
- [ ] Each iteration receives and extends the previous chain via Jinja2 `{% for %}`
- [ ] `loop_limits` and `loop_exits` are configured as safety guards
- [ ] Export produces `root_cause_analysis.md` with structured output
- [ ] `README.md` documents the pattern, CLI usage, and what the demo teaches
- [ ] No Python code required — pure YAML demo
- [ ] Tests: `five-whys` added to `STANDARD_DEMOS` in `examples/demos/tests/test_demos.py` (structure, loader, and prompt existence tests pass)

## Alternatives Considered

### A. Python tool for list accumulation

Use a `type: python` tool node between iterations to append each answer to a list in state. Rejected: adds Python dependency for what should be a pure-YAML demo. The structured output `chain` field (the LLM returns the full chain each time) avoids the need for a custom reducer.

### B. Map node over fixed list [1,2,3,4,5]

Fan out all five whys in parallel. Rejected: defeats the purpose — each "why" must build on the previous answer. The sequential loop is the correct pattern.

### C. Agent with tools

Use an agent node that calls a "record_why" tool in a tool loop. Rejected: over-engineered for a demo that should showcase the simpler conditional-edge loop pattern.

## Implementation Notes

- **State accumulation strategy:** The LLM returns the full `chain` list every iteration. This is intentional — with the `last_value` reducer (default for all state keys in `state_builder.py`), each iteration overwrites `ask_why` entirely. The LLM is responsible for including all prior answers in the returned `chain`, eliminating the need for a custom `add` reducer or Python accumulation node.
- **Test integration:** Add `"five-whys"` to the `STANDARD_DEMOS` list in `examples/demos/tests/test_demos.py`. The existing parameterised tests (structure, loader, prompts) will automatically cover the new demo.
- **No new requirements needed:** This demo exercises existing capabilities (`REQ-YG-006` loop/graph validation, `REQ-YG-003` linting, `REQ-YG-038` exports). No new `REQ-YG-XXX` entry required.

## Judgement

**Verdict: APPROVE**
**Judged:** 2026-03-27

**Findings:**

1. **Scope** — Clear and minimal. Single demo, 3 YAML files + README + test registration. No framework changes required.
2. **Acceptance criteria** — All measurable: lint passes, 5 iterations complete, export produced, tests pass, no Python code.
3. **Feasibility** — All framework features verified to exist and work as described: `_loop_counts` auto-increment, `last_value` reducer, conditional edge evaluation with dotted paths, `loop_limits`/`loop_exits`, markdown export, relative prompt resolution.
4. **Architecture alignment** — Follows established demo patterns exactly (matches `hello/`, `reflexion/`, `novel_generator/`). Variable syntax (`{state.X}`) matches framework resolution in `utils/expressions.py`.
5. **Single responsibility** — One demo, one pattern (fixed-count accumulation loop). No orthogonal concerns.

**Corrections applied:**

- **FR number collision:** Renumbered FR-203 → FR-204 (FR-203 already assigned to linter-e302-accept-state-key).
- **Terminology:** "quality-gate loop" → "self-correction loop" for reflexion characterisation.
- **Requirement IDs:** Corrected from `REQ-YG-003/006/010` to `REQ-YG-006/003/038` (loop validation, linting, exports respectively).

**Scope is frozen. Authority granted to implement.**

## Related

- `examples/demos/reflexion/` — Existing loop demo (quality-gate pattern, not fixed-count)
- `examples/demos/novel_generator/` — Multi-phase pipeline with loop + map
- `examples/demos/hello/` — Simplest demo structure reference
- `yamlgraph/models/state_builder.py` — State field generation and `last_value` reducer
- `yamlgraph/node_factory/llm_nodes.py` — Loop counter increment and `skip_if_exists` logic
- `yamlgraph/utils/conditions.py` — Condition evaluation for `_loop_counts.X < 5`
- `yamlgraph/routing.py` — Expression router and loop exit handling
- `reference/graph-yaml.md` — Loop limits, loop exits, conditional edges
