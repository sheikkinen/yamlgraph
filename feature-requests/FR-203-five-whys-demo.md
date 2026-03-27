# Feature Request: Five Whys Demo — Iterative Root Cause Analysis Pipeline

**Priority:** LOW
**Type:** Feature
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-27

## Summary

Add an `examples/demos/five-whys/` demo that performs the Five Whys root cause analysis technique: given a problem statement, iteratively asks "why?" five times, drilling deeper each iteration, then synthesises a root cause summary with actionable recommendations.

## Value Statement

New users see a real-world loop pattern that accumulates structured results across iterations, demonstrating conditional edges, loop limits, Jinja2 state access, and exports — all in pure YAML with zero Python.

## Problem

The existing loop demos (`reflexion/`) use a quality-gate loop (refine until score ≥ threshold). There is no demo that:

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
- [ ] Tests: lint validation test for the graph YAML

## Alternatives Considered

### A. Python tool for list accumulation

Use a `type: python` tool node between iterations to append each answer to a list in state. Rejected: adds Python dependency for what should be a pure-YAML demo. The structured output `chain` field (the LLM returns the full chain each time) avoids the need for a custom reducer.

### B. Map node over fixed list [1,2,3,4,5]

Fan out all five whys in parallel. Rejected: defeats the purpose — each "why" must build on the previous answer. The sequential loop is the correct pattern.

### C. Agent with tools

Use an agent node that calls a "record_why" tool in a tool loop. Rejected: over-engineered for a demo that should showcase the simpler conditional-edge loop pattern.

## Related

- `examples/demos/reflexion/` — Existing loop demo (quality-gate pattern, not fixed-count)
- `examples/demos/novel_generator/` — Multi-phase pipeline with loop + map
- `yamlgraph/models/state_builder.py` — State field generation and reducers
- `reference/graph-yaml.md` — Loop limits, loop exits, conditional edges
