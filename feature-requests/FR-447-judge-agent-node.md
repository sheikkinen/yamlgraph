# Feature Request: FR-447 — Judge Node as YAMLGraph Agent

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-05-22

## Summary

Create a standalone FR judge as a YAMLGraph agent demo in `examples/demos/judge/`. Input: path to an FR file. Output: structured verdict with criteria evaluation. Proves the agent-with-tools pattern before any chaplain pipeline integration.

## Value Statement

Demonstrates that a `type: agent` node with constrained read-only tools and Pydantic structured output can replace opaque copilot sessions for review tasks. Validates the pattern in isolation — chaplain integration (Phase 2) inherits a proven graph.

## Problem

The judge step (`step-judge-v2.yaml`) currently runs as a `type: copilot` node:

```yaml
nodes:
  judge:
    type: copilot
    prompt: judge
    backend: cli
    cli_flags:
      model: claude-sonnet-4.6
      allow_all_paths: true
      allow_all_tools: true
```

**Issues:**

1. **No observability**: LangSmith traces show "copilot called" but not which files the judge read, which checks it performed, or what evidence led to its verdict.

2. **No structured output**: The verdict is parsed from raw text via keyword matching (`event_map: {APPROVE: approve, ...}`). If the LLM puts commentary before the keyword, parsing fails or picks the wrong verdict.

3. **Unrestricted access**: `--allow-all-tools` grants the judge full terminal access, file editing, and code execution. The judge's contract is to *read* artifacts and *render a verdict* — it needs read access to ~4 files, not root shell.

4. **No tool-call evidence trail**: When the judge AMENDs, it writes issues back to the FR, but there's no structured record of which evaluation criteria triggered the amendment.

## Proposed Solution

Standalone demo graph at `examples/demos/judge/` using `type: agent` with constrained tools and Pydantic structured output.

### Graph: `examples/demos/judge/graph.yaml`

```yaml
version: "1.0"
name: fr-judge
description: "FR-447 — Standalone FR judge with structured verdict output"

prompts_relative: true
prompts_dir: prompts

state:
  fr_path: str
  verdict: dict

tools:
  read_fr:
    type: shell
    command: cat {fr_path}
    description: "Read the feature request document to evaluate"

  check_architecture:
    type: shell
    command: grep -n "REQ-YG-\|CAP-" ARCHITECTURE.md | head -30
    description: "Search architecture doc for related requirements and capabilities"

  search_existing_frs:
    type: shell
    command: grep -rl "{pattern}" feature-requests/ 2>/dev/null | head -10
    description: "Search existing FRs for a pattern to check scope overlap"

  read_file:
    type: shell
    command: head -100 {file}
    description: "Read the first 100 lines of any project file"

nodes:
  judge:
    type: agent
    prompt: judge
    model: claude-sonnet-4.6
    temperature: 0
    tools: [read_fr, check_architecture, search_existing_frs, read_file]
    max_iterations: 8
    state_key: verdict

edges:
  - from: START
    to: judge
  - from: judge
    to: END
```

### Prompt: `examples/demos/judge/prompts/judge.yaml`

```yaml
system: |
  You are a feature request reviewer for YAMLGraph.
  You have tools to read the FR, check architecture alignment,
  and search for related FRs.

  Your task: gather evidence using tools, then render a structured verdict.

user: |
  **Judge.** Evaluate the feature request at {{ fr_path }}.

  ## Process

  1. **Read the FR** — use the read_fr tool
  2. **Check architecture** — use check_architecture to verify alignment
  3. **Check overlap** — use search_existing_frs if scope might overlap
  4. **Read referenced files** — use read_file for any files cited in the FR

  ## Evaluation Criteria

  1. Is the scope clear and minimal?
  2. Are there contradictions or ambiguities?
  3. Are acceptance criteria measurable?
  4. Is the implementation approach feasible?
  5. Does it align with existing architecture?
  6. Single responsibility — or does it bundle orthogonal concerns?
  7. Strategic classification:
     - Framework primitive (3+ use cases)
     - Contrib/example (1-2 use cases)
     - Pattern documentation (0 use cases)
     - Reject (problem not real)
  8. Do acceptance tests compile and fail for the right reasons?

  Render your verdict as structured output.

schema:
  name: JudgeVerdict
  fields:
    verdict:
      type: str
      description: "Exactly one of: APPROVE, AMEND, REJECT, SPLIT"
    classification:
      type: str
      description: "One of: framework_primitive, contrib_example, pattern_documentation, reject"
    reasoning:
      type: str
      description: "2-5 sentence explanation of the verdict"
    criteria_results:
      type: list[dict]
      description: "List of {criterion: str, passed: bool, note: str} for each of the 8 criteria"
    issues:
      type: list[str]
      description: "Specific issues to address (empty if APPROVE)"
```

### Deferred to Phase 2: Chaplain integration

Event routing, `write_judge_notes` tool, mtime writeback guard, and pipeline wiring are **out of scope** for this FR. They belong in a follow-up FR once the standalone demo is validated. See `docs/plan-dogfood-chaplain.md` for the phased plan.

## Acceptance Criteria

- [x] `examples/demos/judge/graph.yaml` runs as `type: agent` with 4 constrained read-only tools
- [ ] ~~Verdict returned as structured Pydantic output~~ — **Deferred to FR-448**: agent nodes do not apply prompt `schema:` to output. Demo returns text. Structured output requires framework change.
- [x] Demo: `yamlgraph graph run examples/demos/judge/graph.yaml --var fr_path=feature-requests/FR-447-judge-agent-node.md --full`
- [x] LangSmith trace shows individual tool calls (read_fr, check_architecture, etc.)
- [x] `demo-output.log` captured (demo-gate requirement)
- [x] Tests added with `@pytest.mark.req("REQ-YG-408")`

## Acceptance Test

The judge evaluates an FR as its acceptance test:

```bash
yamlgraph graph run examples/demos/judge/graph.yaml \
  --var fr_path="feature-requests/FR-447-judge-agent-node.md" \
  --full
```

Expected: structured output with `verdict` (APPROVE/AMEND/REJECT/SPLIT), `classification`, `reasoning`, `criteria_results` (8 items), and `issues` list.

Unit test skeleton:

```python
@pytest.mark.req("REQ-YG-XXX")
@pytest.mark.slow
def test_judge_agent_produces_structured_verdict(mock_llm, tmp_path):
    """Judge agent returns JudgeVerdict schema with all required fields."""
    fr = tmp_path / "FR-TEST.md"
    fr.write_text("# Feature Request: Test\n\n## Summary\nTest feature.\n\n## Acceptance Criteria\n- [ ] Works\n")

    config = load_graph_config(
        "examples/demos/judge/graph.yaml"
    )
    graph = compile_graph(config)
    result = graph.invoke({"fr_path": str(fr)})

    verdict = result["verdict"]
    assert verdict["verdict"] in {"APPROVE", "AMEND", "REJECT", "SPLIT"}
    assert verdict["classification"] in {
        "framework_primitive", "contrib_example",
        "pattern_documentation", "reject",
    }
    assert isinstance(verdict["reasoning"], str)
    assert len(verdict["reasoning"]) > 20
    assert isinstance(verdict["criteria_results"], list)
    assert len(verdict["criteria_results"]) == 8
```

## Alternatives Considered

1. **Keep copilot node, add structured output parsing**: Copilot CLI doesn't support Pydantic schemas — we'd still be keyword-parsing raw text.

2. **Use LLM node instead of agent**: The judge needs to read files (FR, topic, architecture) — without tools it would need all content injected via variables, blowing up the prompt. Agent with tools loads content on demand.

3. **Hybrid: copilot for AMEND writeback, agent for verdict**: Adds complexity of two LLM calls. Prefer single agent with a write tool.

## Implementation Notes

### Files created

1. **`examples/demos/judge/graph.yaml`** — Agent graph with 4 read-only tools
2. **`examples/demos/judge/prompts/judge.yaml`** — Prompt with structured output schema
3. **`examples/demos/judge/demo-output.log`** — Captured demo run output
4. **Tests** — Unit test with mock LLM

### What doesn't change

- Entire `.chaplain/` directory — untouched
- Pipeline FSM, event routing, writeback guards — untouched
- All existing graphs, prompts, tools — untouched

### Phase 2 (follow-up FR)

Once demo is validated, a separate FR wires it into the chaplain pipeline:
- Replace `step-judge-v2.yaml` copilot node with the proven agent graph
- Add `write_judge_notes` tool for AMEND writeback
- Wire event routing (existing `extract_event` handles dicts — no framework change)

## Related

- `docs/plan-dogfood-chaplain.md` — Overall plan for chaplain dogfooding (Phase 1–3)
- `docs/plan-yamlgraph-skills.md` — Skills feature that enables tool reuse across agents
- `.chaplain/graphs/watcher-plan/step-judge-v2.yaml` — Current judge implementation (Phase 2 target)

## Judge Notes

**Date:** 2026-05-22
**Verdict:** AMEND
**Classification:** framework_primitive

### Evaluation

| # | Criterion | Pass | Note |
|---|-----------|------|------|
| 1 | Scope clear and minimal | YES | Single step conversion, well-bounded |
| 2 | Contradictions/ambiguities | NO | 3 issues found (see below) |
| 3 | Acceptance criteria measurable | YES | Structured schema, LangSmith traces, pass rate |
| 4 | Implementation feasible | YES | Uses proven agent node + shell tool primitives |
| 5 | Aligns with architecture | YES | Three-layer pattern; agent node is Layer 2 |
| 6 | Single responsibility | YES | Judge step only; plan/enforce untouched |
| 7 | Classification | framework_primitive | Pattern extends to sanity check + inquisitor (3+ use cases) |
| 8 | Tests compile/fail correctly | N/A | Test skeleton used non-existent `run_graph()` — corrected |

### Issues found and resolved

1. **`event_key: judge_result.verdict` was scope creep** — The existing `extract_event` in `yamlgraph/utils/fsm/helpers.py` already handles dict values by iterating all string fields. Keys are lowered by `_normalize_event_map` in `yamlgraph/utils/fsm/action.py`. No framework change needed. **Fix:** kept `event_key: judge_result`, removed dot-path proposal and `yamlgraph_async_action.py` change from scope.

2. **`write_judge_notes` used invalid module path** — `module: .chaplain.tools.judge_tools` is a relative import with leading dot. `load_python_function()` in `yamlgraph/tools/python_tool.py` calls `importlib.import_module()` which doesn't support relative imports without a `package` argument. **Fix:** changed to `path: .chaplain/tools/judge_tools.py` which resolves relative to graph root.

3. **Test skeleton referenced non-existent `run_graph()`** — No such test utility exists. **Fix:** replaced with established pattern: `load_graph_config()` → `compile_graph()` → `graph.invoke()`.

### Reasoning

The FR is architecturally sound and the value proposition is clear. The three issues were: one scope creep (adding a framework feature inside a dogfood FR), one factual error (invalid Python import path), and one underspecified test. All corrected inline.

### v2 amendment (2026-05-22)

**Human judgement override:** Detach from chaplain pipeline. First version must be a standalone demo in `examples/demos/judge/` — proves the pattern in isolation before touching production pipeline. Rationale:
- Demo-first validates the agent graph without blast radius to the chaplain
- Removes `write_judge_notes`, event routing, mtime guard from scope
- Reduces blast radius from 5 changed files across `.chaplain/` to 4 new files in `examples/`
- Chaplain integration becomes a follow-up FR with a proven graph to import

Scope changes:
- Removed: `topic_file` input, `verify_tests_compile` tool, `read_topic` tool, event routing, `write_judge_notes` tool
- Changed: graph location from `.chaplain/graphs/` to `examples/demos/judge/`
- Changed: state key from `judge_result` to `verdict`
- Changed: effort from 3 days to 2 days
- Added: `demo-output.log` requirement (demo-gate)

### Re-judgement (2026-05-22)

**Verdict:** APPROVE
**Classification:** contrib_example (graduates to framework_primitive at Phase 2)

All 8 criteria pass. Previous 3 issues resolved. Scope is clear, minimal, and internally consistent. One non-blocking observation: Problem section describes chaplain issues but FR delivers a demo — acceptable as motivation for the pattern. Freeze scope. Grant authority to implement.
