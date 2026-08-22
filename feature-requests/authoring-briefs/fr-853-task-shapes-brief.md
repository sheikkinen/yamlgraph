# Authoring Brief: FR-853 D-2 — Task shapes clauses in demo graph descriptions

**Governing FR:** feature-requests/FR-853-agent-instrument-registry.md
(Judged APPROVED WITH REVISIONS 2026-08-22; this brief executes
deliverable D-2 only.)

**Prior art:** fr-790-authoring-brief.md — noun overlap only ("brief");
unrelated FR's authoring brief, same committed-brief convention
(FR-852), no scope overlap. Disposition: precedent for format, superseded
by nothing.

## Task

Edit the `description` metadata field of six EXISTING registered demo
graphs so each contains a literal `Task shapes:` clause mapping an
agent task shape to the graph. Description-only edits: do NOT change
nodes, edges, state, prompts, defaults, or any other key. Do NOT create
any new files.

## Target files and exact new descriptions

1. `examples/demos/map/graph.yaml` (name: map-demo)
   description: `"Demonstrates parallel fan-out with type: map. Task shapes: for each item in a list, ask the model — parallel map-reduce over N items."`

2. `examples/demos/fan-out/graph.yaml` (name: fan-out-demo)
   description: `"Parallel fan-out edges running three branches concurrently. Task shapes: run several different analyses of one input concurrently."`

3. `examples/demos/race/graph.yaml` (name: race-demo)
   description: `"Race multiple LLM providers for the fastest response. Task shapes: same question to multiple providers or models, take the fastest good answer (hedging)."`

4. `examples/demos/five-whys/graph.yaml` (name: five-whys)
   description: `"Five Whys root cause analysis — iterative deepening loop. Task shapes: iterative root-cause drill-down of a defect, incident, or symptom."`

5. `examples/demos/innovation_matrix/graph.yaml` (name: innovation-matrix)
   description: `"Generate an Innovation Matrix crossing capabilities with constraints. Task shapes: structured ideation — cross domain capabilities with constraints to surface non-obvious directions."`

6. `examples/demos/router/graph.yaml` (name: tone-router-demo)
   description: `"Route responses based on detected message tone. Task shapes: classify an input, then dispatch to a specialized handler (conditional routing)."`

## Validation

- `yamlgraph graph lint` must pass on all six touched files (AC-06).
- Smoke: `yamlgraph graph list` (or discovery) must show the updated
  descriptions; full graph runs are NOT required for description-only
  metadata edits — record this rationale honestly in the report's
  Validation section.
- Witness test (already committed RED):
  `tests/unit/test_fr853_task_shapes_index.py` — must pass after the
  edits (`pytest tests/unit/test_fr853_task_shapes_index.py -q --no-cov`).

## Constraints

- No new directories, registries, MCP tools, or discovery commands
  (FR-853 AC-05; judgement gates C-4/C-5).
- Preserve YAML comments and formatting outside the description line.
