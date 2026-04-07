# Feature Request: Research Agent Demo — 5-Step Agentic Pattern

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-04-07

## Summary

Add a new demo at `examples/demos/research-agent/` that implements the canonical 5-step agentic pattern (Extract Intent → Plan → Execute → Validate → Respond) using `type: agent` and `type: llm` nodes. This proves that bounded, tool-using agents can perform multi-phase research entirely through declarative YAML — no copilot delegation required.

## Value Statement

Graph authors get a reference implementation showing how to decompose agentic workflows into explicit, auditable phases with verification gates, replacing unbounded copilot delegation with structured agent pipelines.

## Problem

Existing agent demos use 2-node patterns (agent → llm synthesis). This conflates planning with execution and omits explicit validation. The codebase lacks a demo that:

1. **Separates intent extraction from execution** — current demos pass raw user queries directly to agents.
2. **Includes a planning phase** — no demo shows an agent creating an explicit plan before executing it.
3. **Has a dedicated verification node** — `verified-search` embeds verification in prompts; `verification-gate` uses the `verification` field on generation nodes. Neither shows a standalone critique node that gates output quality.
4. **Demonstrates the full agentic lifecycle** — the 5-step pattern (extract → plan → execute → validate → respond) is the canonical agentic architecture but has no YAMLGraph reference implementation.

## Proposed Solution

A 5-node graph that researches a codebase topic through structured phases:

```yaml
version: "1.0"
name: research-agent
description: >
  5-step agentic research: extract intent, plan approach,
  execute research with tools, validate findings, synthesize report.

prompts_relative: true
prompts_dir: prompts

variables:
  query:
    description: Research question to investigate
    example: "How does the agent node type work?"
  scope:
    description: Directory scope for research
    default: yamlgraph/

tools:
  search_code:
    type: shell
    command: grep -rn "{pattern}" --include="*.py" {scope} | head -20
    description: Search Python source files for a pattern
  list_files:
    type: shell
    command: find {path} -name "*.py" -type f | head -30
    description: List Python files in a directory
  read_file:
    type: shell
    command: head -80 {file}
    description: Read the first 80 lines of a file
  count_lines:
    type: shell
    command: wc -l {file}
    description: Count lines in a file

nodes:
  extract_intent:
    type: llm
    prompt: extract_intent
    state_key: intent
    variables:
      query: "{query}"

  plan_research:
    type: agent
    prompt: plan_research
    tools: [search_code, list_files]
    max_iterations: 5
    state_key: plan
    requires: [intent]
    variables:
      intent: "{state.intent}"
      scope: "{scope}"

  execute_research:
    type: agent
    prompt: execute_research
    tools: [search_code, list_files, read_file, count_lines]
    max_iterations: 10
    state_key: findings
    tool_results_key: _research_tools
    requires: [plan]
    variables:
      plan: "{state.plan}"
      scope: "{scope}"

  validate_findings:
    type: llm
    prompt: validate_findings
    state_key: validation
    requires: [intent, findings]
    variables:
      intent: "{state.intent}"
      findings: "{state.findings}"

  synthesize_report:
    type: llm
    prompt: synthesize_report
    state_key: report
    requires: [intent, findings, validation]
    variables:
      query: "{query}"
      intent: "{state.intent}"
      findings: "{state.findings}"
      validation: "{state.validation}"

edges:
  - from: START
    to: extract_intent
  - from: extract_intent
    to: plan_research
  - from: plan_research
    to: execute_research
  - from: execute_research
    to: validate_findings
  - from: validate_findings
    to: synthesize_report
  - from: synthesize_report
    to: END
```

### Node Responsibilities

| Step | Node | Type | Purpose |
|------|------|------|---------|
| 1. Extract | `extract_intent` | llm | Parse query into structured fields (topic, scope, depth) via Pydantic schema |
| 2. Plan | `plan_research` | agent | Explore directory structure, identify relevant files, output ordered plan |
| 3. Execute | `execute_research` | agent | Follow the plan: read files, search patterns, gather evidence |
| 4. Validate | `validate_findings` | llm | Check findings against original intent; flag gaps or unsupported claims |
| 5. Respond | `synthesize_report` | llm | Combine findings + validation into final structured report |

### Key Design Decisions

- **Agent nodes get explicit tool whitelists** — `plan_research` only gets `search_code` and `list_files` (discovery), while `execute_research` gets all four tools (full access). This demonstrates least-privilege tool assignment.
- **Validation is a separate LLM node**, not embedded in prompts or `verification` config. This makes the critique auditable as a distinct state entry.
- **`tool_results_key`** on the execute node captures raw tool call history for debugging.
- **Linear flow** (no loops) — the validation node reports gaps but does not trigger re-execution. This keeps the demo simple. A loop-back variant is a natural follow-up.

### Prompt Schemas

`extract_intent` returns structured output:

```yaml
# prompts/extract_intent.yaml
schema:
  name: ResearchIntent
  fields:
    topic: {type: str, description: "Core topic to research"}
    key_questions: {type: "list[str]", description: "Specific questions to answer"}
    expected_artifacts: {type: "list[str]", description: "Files or patterns likely relevant"}
```

`validate_findings` returns structured output:

```yaml
# prompts/validate_findings.yaml
schema:
  name: ValidationResult
  fields:
    questions_answered: {type: "list[str]", description: "Which key questions were addressed"}
    gaps: {type: "list[str]", description: "Questions not adequately answered"}
    confidence: {type: str, description: "low, medium, or high"}
    notes: {type: str, description: "Additional observations"}
```

## Acceptance Criteria

- [ ] `examples/demos/research-agent/graph.yaml` with 5 nodes following the extract → plan → execute → validate → respond pattern
- [ ] Uses `type: llm` for structured extraction (`extract_intent`) and validation (`validate_findings`)
- [ ] Uses `type: agent` with explicit tool whitelists for planning and execution
- [ ] `plan_research` gets a subset of tools (discovery only); `execute_research` gets all tools
- [ ] Validation node checks findings against extracted intent; returns structured gaps/confidence
- [ ] Shell tools use `{placeholder}` variables with descriptions
- [ ] `examples/demos/research-agent/README.md` documenting the 5-step pattern, usage, and key concepts
- [ ] `demo-output.log` proving execution via `yamlgraph graph run`
- [ ] Graph passes `yamlgraph graph lint`
- [ ] Prompts use `prompts_relative: true` with local `prompts/` directory
- [ ] Tests: at least one unit test with `@pytest.mark.req` covering graph load/lint

## Alternatives Considered

### A. Extend an existing 2-node demo
Add nodes to `verified-search` or `code-analysis`. Rejected: those demos teach specific patterns (prompt-based verification, multi-tool aggregation). Grafting a 5-step flow onto them dilutes their focus.

### B. Use copilot node instead of agent
A `type: copilot` node could handle all 5 steps autonomously. Rejected: the entire point is to prove the pattern works with bounded, auditable agents. Copilot delegation is the anti-pattern this demo contrasts against.

### C. Add conditional loop-back from validate to execute
If validation finds gaps, route back to `execute_research` for another pass. Deferred: the reflexion demo already teaches loops. This demo's value is the linear 5-step decomposition. A loop variant can be a follow-up FR.

### D. Use map node for parallel subtask execution
Replace `execute_research` with a map node that fans out over planned subtasks. Deferred: adds complexity without teaching the core pattern. Map-based research is a good follow-up.

## Related

- `examples/demos/feature-brainstorm/` — Closest prior art (agent → agent → llm → llm, 4 nodes)
- `examples/demos/verified-search/` — Verification via prompt, not separate node
- `examples/demos/code-analysis/` — Agent with 8 shell tools, 2 nodes
- `examples/demos/verification-gate/` — `verification` field on generation nodes (FR-164)
- `examples/demos/reflexion/` — Loop-back pattern with quality gates
- Diary entry 2026-04-07 — ChatGPT roadmap analysis motivating this pattern
