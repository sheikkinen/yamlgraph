# Feature Request: FR-304 Pros-and-Cons Decision Analysis Demo

**Priority:** LOW
**Type:** Feature
**Status:** Amend Required
**Effort:** 1 day
**Requested:** 2026-05-01

## Summary

Add a new demo at `examples/demos/pros-and-cons/` that runs a four-node decision-analysis pipeline: classify domain with a router node, generate pros and cons in parallel, synthesize a balanced structured verdict, and export the result to markdown.

## Value Statement

Demo authors get a single runnable reference that combines router routing, parallel fan-out/fan-in, schema-validated output, variables, and exports in one YAML-first example.

## Problem

Current demos show these capabilities in isolation (`router/`, `fan-out/`, `five-whys/`) but not as one cohesive decision-analysis flow, so users must piece together the pattern themselves.

### Objectives

1. Deliver one minimal demo that solves one responsibility: balanced pro/con decision analysis from a single `topic` input.
2. Demonstrate router classification (`type: router`) plus parallel fan-out (`to: [a, b]` without `type: conditional`) and fan-in.
3. Demonstrate structured synthesis output and markdown export in the same graph.
4. Keep this as demo-only work (no framework/runtime behavior changes).

### Constraints

1. Scope is limited to `examples/demos/pros-and-cons/` plus demo index documentation updates.
2. Use YAML graph + YAML prompts only (no custom Python nodes or tools).
3. Keep node set fixed to exactly:
   - `classify_domain`
   - `generate_pros`
   - `generate_cons`
   - `synthesize`
4. Router classification must use `route_field: domain` with values `technical|business|personal`.
5. Include `demo-output.log` proving a successful `yamlgraph graph run ... --full` execution (FR-206 policy).

## Proposed Solution

Create:

```text
examples/demos/pros-and-cons/
├── graph.yaml
├── README.md
├── demo-output.log
└── prompts/
    ├── classify_domain.yaml
    ├── generate_pros.yaml
    ├── generate_cons.yaml
    └── synthesize.yaml
```

### Implementation Approach

1. Reuse the router pattern from `examples/demos/router/graph.yaml`:
   - `classify_domain` is a `router` node with:
     - `route_field: domain`
     - `routes` for `technical`, `business`, `personal`
     - `default_route: generate_pros`
2. Reuse the parallel pattern from `examples/demos/fan-out/graph.yaml`:
   - edge `classify_domain -> [generate_pros, generate_cons]` (parallel fan-out, not conditional).
   - fan-in edges `generate_pros -> synthesize` and `generate_cons -> synthesize`.
3. Reuse export pattern from `examples/demos/five-whys/graph.yaml`:
   - export `verdict` as markdown file `decision_analysis.md`.
4. Define prompt schema in `prompts/synthesize.yaml` so the synthesis node returns structured fields suitable for deterministic markdown export.
5. Document usage in README and update `examples/demos/README.md` to list the demo.

### Proposed Graph Shape

```yaml
version: "1.0"
name: pros-and-cons
description: Decision analysis with router classification and parallel pro/con generation
prompts_relative: true
prompts_dir: prompts

state:
  topic: str

nodes:
  classify_domain:
    type: router
    prompt: classify_domain
    route_field: domain
    routes:
      technical: generate_pros
      business: generate_pros
      personal: generate_pros
    default_route: generate_pros
    variables:
      topic: "{state.topic}"
    state_key: classification

  generate_pros:
    type: llm
    prompt: generate_pros
    variables:
      topic: "{state.topic}"
      domain: "{state.classification.domain}"
    state_key: pros

  generate_cons:
    type: llm
    prompt: generate_cons
    variables:
      topic: "{state.topic}"
      domain: "{state.classification.domain}"
    state_key: cons

  synthesize:
    type: llm
    prompt: synthesize
    variables:
      topic: "{state.topic}"
      domain: "{state.classification.domain}"
      pros: "{state.pros}"
      cons: "{state.cons}"
    state_key: verdict

edges:
  - from: START
    to: classify_domain
  - from: classify_domain
    to: [generate_pros, generate_cons]
  - from: generate_pros
    to: synthesize
  - from: generate_cons
    to: synthesize
  - from: synthesize
    to: END

exports:
  verdict:
    format: markdown
    filename: decision_analysis.md
```

## Acceptance Criteria

- [ ] `examples/demos/pros-and-cons/` exists with `graph.yaml`, `README.md`, `demo-output.log`, and prompt files `classify_domain.yaml`, `generate_pros.yaml`, `generate_cons.yaml`, `synthesize.yaml`
- [ ] Graph defines exactly four nodes: `classify_domain`, `generate_pros`, `generate_cons`, `synthesize`
- [ ] `classify_domain` is `type: router` with `route_field: domain` and route keys `technical`, `business`, `personal`
- [ ] Graph includes parallel fan-out edge `classify_domain -> [generate_pros, generate_cons]` without `type: conditional`
- [ ] `synthesize` consumes both `{state.pros}` and `{state.cons}`
- [ ] `prompts/synthesize.yaml` defines a schema containing at least `balanced_verdict`, `score`, and `recommendation`
- [ ] `graph.yaml` includes `exports.verdict` with `format: markdown` and `filename: decision_analysis.md`
- [ ] `yamlgraph graph lint examples/demos/pros-and-cons/graph.yaml` passes
- [ ] `yamlgraph graph run examples/demos/pros-and-cons/graph.yaml --var topic="Should we adopt microservices architecture?" --full` completes successfully
- [ ] `decision_analysis.md` is produced by the run
- [ ] Demo unit tests are added for graph shape, prompt presence/schema, and lint contract
- [ ] Documentation is updated in demo README and `examples/demos/README.md`

## Judgement

**Verdict: AMEND**

### Evaluation

1. **Scope clarity/minimality:** Mostly clear and appropriately demo-scoped.
2. **Contradictions/ambiguities:** Present (router semantics and lint compatibility are not explicit).
3. **Measurable acceptance criteria:** Mostly measurable; a few criteria are underspecified relative to the acceptance tests in worktree.
4. **Implementation feasibility:** Feasible with existing primitives, but requires explicit handling of current router-lint constraints.
5. **Architecture alignment:** Aligned with YAML-first, demo-only architecture.
6. **Single responsibility:** Yes (single demo responsibility), no orthogonal framework work is required if scope is tightened.
7. **Research-brief classification:** **Contrib/example** (1 demo use case; existing abstractions suffice).
8. **Acceptance tests in worktree:** `tests/unit/test_fr304_pros_and_cons_decision_analysis_demo.py` compiles and fails for missing implementation artifacts (expected RED), not for import or fixture wiring failures.

### Required Amendments

1. **Router lint compatibility must be explicit.**
   The FR requires `route_field: domain` and lint-clean graph, but current router lint checks require router prompt schema fields to include `intent` or `tone` (E102 behavior). Amend the FR to define one explicit path:
   - keep demo-only scope and require `classify_domain` prompt schema to include a compatibility field accepted by current lint behavior, or
   - explicitly expand scope to include linter behavior change and its tests (this would no longer be demo-only).

2. **Align FR acceptance criteria with existing RED tests.**
   The worktree acceptance test currently requires:
   - companion test file `tests/unit/test_pros_and_cons_demo.py`
   - `synthesize` schema fields beyond the current FR minimum (`topic`, `domain`, `pros`, `cons` in addition to `balanced_verdict`, `score`, `recommendation`)
   Amend AC text to match this contract, or update the RED test to match the FR; they must be identical.

3. **Clarify router-vs-fanout intent.**
   The FR currently combines a router node with non-conditional parallel fan-out from the same node. Amend wording to state this is intentional classification + fan-out composition (not conditional branch routing), so implementation and review do not drift.

## Alternatives Considered

1. **Conditional router to separate domain-specific pro/con generators**
   Rejected: increases node count and breaks the minimal four-node scope.
2. **Map node over `["pros", "cons"]`**
   Rejected: less explicit for beginner learning goals than two named branches.
3. **Python node for markdown formatting**
   Rejected: built-in `exports` already covers markdown output in YAML-first style.

## Related

- `.chaplain/processing/pros-and-cons-demo.md`
- `feature-requests/TEMPLATE.md`
- `examples/demos/router/graph.yaml`
- `examples/demos/fan-out/graph.yaml`
- `examples/demos/five-whys/graph.yaml`
- `feature-requests/FR-206-demo-proof-gate.md`
- `reference/graph-yaml.md`
