# Feature Request: FR-239 Meta-YAMLGraph — Self-Improving Graph Generator

**Priority:** LOW
**Type:** Feature
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-04-19

## Summary

A new `examples/meta_gen/` example that wraps the graph generation pipeline in a closed-loop: generate → lint → run → evaluate → refine, using deterministic gates (exit codes, booleans) for pass/fail decisions and LLM only for advisory quality scoring.

## Value Statement

Graph authors get an automated graph-authoring assistant that validates its output with real tools (lint, run, schema checks) rather than LLM self-assessment, producing correct-by-construction YAMLGraph pipelines.

## Problem

The existing `examples/yamlgraph_gen/graph.yaml` generates YAMLGraph graphs from natural language and lints them — but the pipeline is **open-loop**. It generates once, lints once, and reports. If linting fails, a human must intervene. If the graph runs but produces poor output, there is no feedback mechanism.

The gap is the **closed-loop refinement cycle**:

1. Lint errors are reported but not fed back to the LLM for correction.
2. The generated graph is never actually **run** to verify it produces meaningful output.
3. There is no **evaluation** of the generated graph's output quality.
4. There is no **iteration limit** with quality threshold to stop when good enough.

Without objective evaluation (lint exit codes, runtime errors, structured output validation), the system degenerates into an LLM talking to itself. The critical constraint: **every pass/fail gate must use deterministic tools** — `yamlgraph graph lint` exit code, runtime exit code, schema validation — not LLM-as-judge for binary decisions.

## Proposed Solution

### Architecture: Generate → Validate → Run → Evaluate → Refine

Build a meta-graph that composes existing node types into a self-improving loop. All required primitives already exist in the framework.

### Python Tools

Five Python tools in `examples/meta_gen/tools/`:

**`file_ops.py`** — Write generated graph + prompts to a temp directory and return the path. Follows the same pattern as `examples/yamlgraph_gen/tools/file_ops.py`:

```python
def write_temp_graph_node(state: dict) -> dict:
    """Write generated graph YAML and prompts to a temp directory.

    Returns dict with temp_graph_path (str) and files_written (list).
    """
    import tempfile
    from pathlib import Path

    graph_content = state.get("generated_graph", "")
    prompts = state.get("generated_prompts") or []

    work_dir = Path(tempfile.mkdtemp(prefix="meta_gen_"))
    graph_path = work_dir / "graph.yaml"
    graph_path.write_text(graph_content)

    prompts_dir = work_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    for prompt in prompts:
        filename = prompt.get("filename", "")
        content = prompt.get("content", "")
        if filename and content:
            (prompts_dir / filename).write_text(content)

    return {
        "temp_graph_path": str(graph_path),
        "files_written": [str(graph_path)],
    }
```

**`linter.py`** — Lint the generated graph using `yamlgraph graph lint`. Returns `{lint_valid: bool, lint_errors: list[str], lint_output: str}`. Identical pattern to `examples/yamlgraph_gen/tools/linter.py` (`lint_graph_node`), but reads `temp_graph_path` from state instead of `output_dir`:

```python
def lint_graph_node(state: dict) -> dict:
    """Lint generated graph, returning boolean validity + error list."""
    import subprocess
    graph_path = state.get("temp_graph_path", "")
    result = subprocess.run(
        ["yamlgraph", "graph", "lint", graph_path],
        capture_output=True, text=True,
    )
    errors = _parse_lint_errors(result.stderr) if result.returncode != 0 else []
    return {
        "lint_valid": result.returncode == 0,
        "lint_errors": errors,
        "lint_output": result.stdout,
    }
```

**`runner.py`** — Execute the generated graph with `yamlgraph graph run` and a timeout. Returns `{run_success: bool, run_output: str, run_errors: list[str]}`:

```python
def run_graph_node(state: dict) -> dict:
    """Run generated graph, returning boolean success + output."""
    import subprocess
    graph_path = state.get("temp_graph_path", "")
    result = subprocess.run(
        ["yamlgraph", "graph", "run", graph_path, "--full"],
        capture_output=True, text=True, timeout=120,
    )
    return {
        "run_success": result.returncode == 0,
        "run_output": result.stdout[:4000],  # Truncate for LLM context
        "run_errors": [result.stderr] if result.returncode != 0 else [],
    }
```

**`scorer.py`** — Compute `mean_score` deterministically from structured evaluation fields, removing LLM error surface:

```python
def compute_score_node(state: dict) -> dict:
    """Deterministic mean of evaluation dimensions."""
    evaluation = state.get("evaluation") or {}
    completeness = evaluation.get("completeness", 0)
    coherence = evaluation.get("coherence", 0)
    correctness = evaluation.get("correctness", 0)
    mean = (completeness + coherence + correctness) / 3.0
    return {"mean_score": round(mean, 2)}
```

**`history.py`** — Accumulate refinement history after each refine iteration. Appends the current iteration's lint errors, run errors, evaluation, and iteration number to `refinement_history`. This fills the gap where no node previously wrote to `refinement_history`:

```python
def accumulate_history_node(state: dict) -> dict:
    """Append current iteration context to refinement_history."""
    history = list(state.get("refinement_history") or [])
    loop_counts = state.get("_loop_counts") or {}
    iteration = loop_counts.get("refine", 0)

    entry = {
        "iteration": iteration,
        "lint_errors": state.get("lint_errors") or [],
        "run_errors": state.get("run_errors") or [],
        "evaluation": state.get("evaluation"),
        "mean_score": state.get("mean_score"),
    }
    history.append(entry)
    return {"refinement_history": history}
```

### Graph YAML

```yaml
# examples/meta_gen/graph.yaml
version: "1.0"
name: meta-yamlgraph
description: "Self-improving graph generator with objective evaluation gates"

prompts_relative: true
prompts_dir: prompts

defaults:
  provider: anthropic
  model: claude-sonnet-4-20250514

state:
  request: str
  generated_graph: str
  generated_prompts: list
  temp_graph_path: str
  lint_valid: bool
  lint_errors: list
  lint_output: str
  run_success: bool
  run_output: str
  run_errors: list
  evaluation: dict
  mean_score: float
  refinement_history: list
  report: str

tools:
  write_temp_graph:
    type: python
    module: examples.meta_gen.tools.file_ops
    function: write_temp_graph_node
    description: "Write generated graph and prompts to temp directory"

  lint_graph:
    type: python
    module: examples.meta_gen.tools.linter
    function: lint_graph_node
    description: "Lint generated graph with yamlgraph CLI"

  run_graph:
    type: python
    module: examples.meta_gen.tools.runner
    function: run_graph_node
    description: "Run generated graph with yamlgraph CLI"

  compute_score:
    type: python
    module: examples.meta_gen.tools.scorer
    function: compute_score_node
    description: "Compute deterministic mean of evaluation dimensions"

  accumulate_history:
    type: python
    module: examples.meta_gen.tools.history
    function: accumulate_history_node
    description: "Append current iteration context to refinement_history"

nodes:
  # Phase 1: Generate graph YAML from request
  generate:
    type: llm
    prompt: generate_graph
    state_key: generated_graph
    variables:
      request: "{state.request}"
      refinement_history: "{state.refinement_history}"

  # Phase 2: Write to temp directory
  write_temp:
    type: python
    tool: write_temp_graph
    state_key: temp_graph_path

  # Phase 3: Lint (deterministic gate)
  lint:
    type: python
    tool: lint_graph
    state_key: lint_valid

  # Phase 4: Run the graph (deterministic gate, only if lint passed)
  run:
    type: python
    tool: run_graph
    state_key: run_success

  # Phase 5: LLM evaluates output quality (advisory scoring)
  evaluate:
    type: llm
    prompt: evaluate_output
    state_key: evaluation
    variables:
      request: "{state.request}"
      run_output: "{state.run_output}"

  # Phase 6: Deterministic mean score
  score:
    type: python
    tool: compute_score
    state_key: mean_score

  # Phase 7: Accumulate history before refinement
  accumulate:
    type: python
    tool: accumulate_history
    state_key: refinement_history

  # Phase 8: Feed errors back to generator for refinement
  refine:
    type: llm
    prompt: refine_graph
    state_key: generated_graph
    variables:
      generated_graph: "{state.generated_graph}"
      lint_errors: "{state.lint_errors}"
      run_output: "{state.run_output}"
      run_errors: "{state.run_errors}"
      evaluation: "{state.evaluation}"
      refinement_history: "{state.refinement_history}"

  finalize:
    type: llm
    prompt: finalize
    state_key: report
    variables:
      request: "{state.request}"
      generated_graph: "{state.generated_graph}"
      evaluation: "{state.evaluation}"
      mean_score: "{state.mean_score}"

  abort:
    type: llm
    prompt: abort
    state_key: report
    variables:
      request: "{state.request}"
      lint_errors: "{state.lint_errors}"
      run_errors: "{state.run_errors}"
      refinement_history: "{state.refinement_history}"

edges:
  - from: START
    to: generate
  - from: generate
    to: write_temp
  - from: write_temp
    to: lint

  # Deterministic gate: lint pass → run, lint fail → accumulate → refine
  - from: lint
    to: run
    condition: "lint_valid == true"
  - from: lint
    to: accumulate
    condition: "lint_valid == false"

  - from: run
    to: evaluate
    condition: "run_success == true"
  - from: run
    to: accumulate
    condition: "run_success == false"

  - from: evaluate
    to: score
  - from: score
    to: finalize
    condition: "mean_score >= 3.5"
  - from: score
    to: accumulate
    condition: "mean_score < 3.5 and _loop_counts.refine < 3"
  - from: score
    to: abort
    condition: "mean_score < 3.5 and _loop_counts.refine >= 3"

  # Accumulate history then refine, refine loops back to write_temp
  - from: accumulate
    to: refine
  - from: refine
    to: write_temp

  - from: finalize
    to: END
  - from: abort
    to: END

loop_limits:
  refine: 3

loop_exits:
  refine: abort
```

### Objective Evaluation Gates

The evaluation chain uses **deterministic checks first**, LLM scoring second:

1. **Lint gate** (deterministic): Python tool wraps `yamlgraph graph lint`, sets `lint_valid: bool`. Conditional edge routes on the boolean — no LLM interpretation.
2. **Run gate** (deterministic): Python tool wraps `yamlgraph graph run`, sets `run_success: bool`. Conditional edge routes on the boolean.
3. **Quality score** (deterministic computation): Python tool computes `mean_score` from structured LLM evaluation fields. Conditional edge routes on `mean_score >= 3.5`.
4. **Quality evaluation** (LLM-assisted): Only reached after all deterministic gates pass. Scores coherence, completeness, correctness on a rubric. Provides advisory feedback for refinement — not the pass/fail gate.

### Evaluation Prompt

```yaml
# examples/meta_gen/prompts/evaluate_output.yaml
system: |
  You are evaluating the output of a generated YAMLGraph pipeline.
  All deterministic checks (lint, runtime) have already passed.
  Score ONLY the quality of the output content.
template: |
  The generated graph was run with this request:
  {{ request }}

  Run output:
  {{ run_output }}

  Score each dimension 1-5:
  - completeness: Does the output address the full request?
  - coherence: Is the output well-structured and logical?
  - correctness: Does the output contain factual errors?
schema:
  name: GraphEvaluation
  fields:
    completeness: {type: int, description: "1-5 score"}
    coherence: {type: int, description: "1-5 score"}
    correctness: {type: int, description: "1-5 score"}
    issues: {type: list[str], description: "Specific problems found"}
    suggestion: {type: str, description: "Concrete refinement suggestion"}
```

### Iteration Control

- `loop_limits: refine: 3` prevents infinite refinement (existing `check_loop_limit()` mechanism)
- `loop_exits: refine: abort` routes to abort when limit reached
- `accumulate` node (Python tool) appends `{iteration, lint_errors, run_errors, evaluation, mean_score}` to `refinement_history` before each `refine` call, giving the refine prompt full context to avoid repeating mistakes
- Conditional edges on `_loop_counts.refine` provide explicit iteration-aware routing at the `score` node

### Refinement History Accumulation

The `accumulate_history` Python tool node sits between every failure gate and the `refine` node. It appends a structured entry to `refinement_history` containing the current iteration's lint errors, run errors, evaluation results, and mean score. This follows Option (a) from the Judgement — a single-responsibility Python tool, consistent with the existing tool pattern in `yamlgraph_gen`.

The flow for each failure path:
- **Lint failure**: `lint` → `accumulate` → `refine` → `write_temp` → `lint` ...
- **Run failure**: `run` → `accumulate` → `refine` → `write_temp` → `lint` ...
- **Low score**: `score` → `accumulate` → `refine` → `write_temp` → `lint` ...

### Relationship to Existing `yamlgraph_gen`

This FR does **not** modify `yamlgraph_gen`. It creates a new `examples/meta_gen/` that:

- Follows the same tool definition patterns as `yamlgraph_gen` (Python tools with `_node` wrappers)
- Can reuse the snippet library pattern from `yamlgraph_gen` for the generate phase
- Adds the lint → run → evaluate → refine loop that `yamlgraph_gen` lacks
- Demonstrates the self-referential capability: a YAMLGraph graph that produces YAMLGraph graphs

## Acceptance Criteria

- [ ] `examples/meta_gen/graph.yaml` defines the generate → lint → run → evaluate → refine loop
- [ ] Lint gate uses Python tool wrapping `yamlgraph graph lint` exit code, setting `lint_valid: bool` in state
- [ ] Run gate uses Python tool wrapping `yamlgraph graph run` exit code, setting `run_success: bool` in state
- [ ] All routing on lint/run/abort uses deterministic conditional edges on boolean/numeric state fields (no LLM routers for pass/fail)
- [ ] `mean_score` computed deterministically in a Python tool, not by LLM
- [ ] Evaluation uses inline Pydantic schema for structured quality scoring
- [ ] `loop_limits` and `loop_exits` configured to prevent infinite loops (default: 3 iterations)
- [ ] `refinement_history` accumulated by `accumulate_history` Python tool node before each `refine` call, appending `{iteration, lint_errors, run_errors, evaluation, mean_score}` per iteration
- [ ] `tools:` section defines all Python tools with `type: python`, `module`, `function`, `description` fields
- [ ] `temp_graph_path` stored in state via `state_key` on the `write_temp` node
- [ ] At least one successful end-to-end run demonstrated (generate a simple graph, iterate to passing lint + run)
- [ ] Prompts live in `examples/meta_gen/prompts/` (no hardcoded strings)
- [ ] Tests added for Python tools (file_ops, linter, runner, scorer, history)
- [ ] `examples/meta_gen/README.md` documents usage, architecture, and limitations
- [ ] Demo output logged to `examples/demos/meta_gen/demo-output.log`

## Design Decisions

### Deterministic gates over LLM routers

The original draft used `type: router` with LLM prompts for lint and run pass/fail decisions. This contradicts the stated objective of deterministic evaluation. Conditional edges on boolean state keys (`lint_valid == true`) are strictly cheaper, faster, and more reliable than asking an LLM to interpret a lint exit code. LLM routers are reserved for genuinely ambiguous decisions.

### Separate Python tools over inline `command:` syntax

The original draft used `command:` directly on nodes, which is not valid YAMLGraph syntax. Shell commands belong in the `tools:` section (see `examples/demos/system-status/graph.yaml`). However, for lint and run, Python tool wrappers are preferred over shell tools because they can parse exit codes, capture stderr, and return structured `{valid: bool, errors: list}` dicts rather than raw text.

### Deterministic `mean_score` computation

The original draft had the LLM compute `mean_score` as part of the evaluation schema. Since the three sub-scores are already structured fields, computing the mean in a Python tool eliminates an LLM error surface. The LLM evaluates quality; arithmetic is not its job.

### Explicit `accumulate_history` node over implicit accumulation

The Judgement identified that no node wrote to `refinement_history`. Rather than overloading the `refine` node's schema with both graph output and history management, a dedicated `accumulate_history` Python tool follows single-responsibility: it captures the current iteration's context and appends it to state before `refine` runs. This matches the existing tool pattern in `yamlgraph_gen` and keeps the `refine` prompt focused on graph generation.

### New example vs extending `yamlgraph_gen`

`yamlgraph_gen` is a ~200-line graph serving as a clean "generate once" teaching example. Adding the iterative loop triples its complexity and conflates two concerns: generation and self-improvement. Separate examples, separate responsibilities.

### Snake_case directory naming

Per CLAUDE.md convention ("Convert python code paths with hyphens to snake_case to avoid import issues"), the directory is `examples/meta_gen/` (not `meta-gen`). Python cannot import from hyphenated directories — `import examples.meta-gen.tools.linter` is a syntax error. The existing `examples/yamlgraph_gen/` follows this convention.

## Alternatives Considered

### 1. Extend `yamlgraph_gen` with a refinement loop

**Pros:** Single example, no duplication.
**Cons:** `yamlgraph_gen` is already complex. Adding run + evaluate + refine triples its size. The linear flow is a clean teaching example; the iterative loop is a different concern.
**Verdict:** Rejected. Keep `yamlgraph_gen` as the simple example; `meta_gen` as the advanced one.

### 2. Agent node with lint/run/evaluate as tools

**Pros:** Single agent node handles the entire loop via tool calls. Simpler graph structure.
**Cons:** The agent decides when to stop, violating the "objective evaluation" constraint. Agent loops are harder to trace and debug than explicit graph edges. Token cost grows quadratically with conversation history.
**Verdict:** Viable as a Phase 2 optimization. Start with explicit nodes and edges for auditability.

### 3. Use FR-043 evaluation framework

**Pros:** Standardized evaluation schema and logging.
**Cons:** FR-043 Phase 1 is approved but not yet implemented. This FR should not depend on unimplemented infrastructure.
**Verdict:** When FR-043 lands, migrate the evaluation node to use its `EvaluationResult` schema. For now, use a local inline schema.

### 4. Accumulate history inside the `refine` node schema

**Pros:** Fewer nodes in the graph.
**Cons:** Overloads the `refine` prompt with two responsibilities: generating a corrected graph AND maintaining iteration history. The `refine` node's `state_key: generated_graph` would need to change to a compound object, requiring a separate extraction step. More complex, less testable.
**Verdict:** Rejected. Dedicated `accumulate_history` tool is simpler and follows single-responsibility.

## Dependencies

- **Existing (satisfied):** `type: python` tool nodes, conditional edges with expression evaluation, inline Pydantic schemas, `yamlgraph graph lint` CLI, `yamlgraph graph run` CLI, `loop_limits` / `loop_exits` mechanism, `_loop_counts` state tracking
- **Optional (future):** FR-043 evaluation framework (can adopt when available), FR-069 map node timeout (useful if meta_gen runs multiple test cases)

## Related

- `examples/yamlgraph_gen/graph.yaml` — Existing graph generator (linear, no feedback loop)
- `examples/yamlgraph_gen/tools/linter.py` — Lint tool pattern to follow
- `examples/demos/system-status/graph.yaml` — Canonical `tools:` section pattern
- `examples/demos/five-whys/graph.yaml` — `loop_limits` / `loop_exits` pattern
- `examples/demos/reflexion/graph.yaml` — Expression-based condition routing on nested fields
- FR-043 — Evaluation framework (complementary; provides standardized scoring)
- FR-173 — Bug-condemning test pipeline (same pattern: objective gates before LLM assessment)
- FR-169 — Enforce reflexion loop (similar iterative refinement pattern)
- Commandment 6 — "Thou shalt not hedge with silent fallbacks" — evaluation must have teeth
- **Seed origin:** Philosopher session 2026-04-19, competitive landscape reflection

## Judgement

**Verdict: APPROVED** — 2026-04-19

### Findings

All 14 claimed dependencies verified as existing in the codebase: `type: python` tool nodes, conditional edges with expression evaluation, inline Pydantic schemas, `loop_limits`/`loop_exits`, `_loop_counts`, CLI commands, `prompts_relative`, and all referenced example patterns (`yamlgraph_gen`, `five-whys`, `reflexion`, `system-status`).

**Scope:** Clear and minimal. New `examples/meta_gen/` directory with 5 Python tools, 1 graph YAML, prompts, tests, README, and demo output. Zero modifications to existing framework code or examples.

**Single responsibility:** Confirmed. All components serve the one concern: a self-improving graph generator with objective evaluation gates.

**Acceptance criteria:** All 16 criteria are measurable and verifiable — file existence, boolean state fields, deterministic routing, schema presence, loop configuration, test coverage, demo log.

**Architecture alignment:** Follows 3-layer pattern (YAML graph → Python tools → CLI side effects). Matches `yamlgraph_gen` tool definition patterns. Snake_case directory naming per CLAUDE.md convention.

**Design decisions:** Well-reasoned. Deterministic gates over LLM routers, separate Python tools over inline `command:`, deterministic `mean_score` computation, explicit `accumulate_history` node — all principled and consistent with Commandment 6.

### Implementation Note

`state_key` on Python tool nodes that return dicts is a no-op (see `python_tool.py:184-188` — dict returns are merged directly into state; `state_key` is only used for scalar returns). The existing `yamlgraph_gen` example omits `state_key` on its python tool nodes for this reason. During implementation, either omit `state_key` from python tool nodes to match convention, or keep it as documentation of the primary output — the behavior is identical either way.

### Authority Granted

Scope frozen. Implement per acceptance criteria. Update this FR with implementation status and decisions.
