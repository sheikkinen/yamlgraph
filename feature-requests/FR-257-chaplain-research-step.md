# Feature Request: FR-257 Chaplain Research Step

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented (2026-04-19)
**Effort:** 2 days
**Requested:** 2026-04-19

## Summary

Add a Research step between Plan and Judge in the Chaplain pipeline so the Judge has competitive landscape, existing abstraction overlap, and usage evidence data before rendering a verdict.

## Value Statement

The Chaplain pipeline gains strategic selectivity — the Judge can distinguish "technically feasible" from "strategically warranted," preventing features that should be pattern documentation or contrib functions from becoming framework primitives.

## Problem

The Chaplain pipeline currently runs: `Plan → Judge → Enforce`. The Judge evaluates technical feasibility (scope, contradictions, acceptance criteria, architecture alignment) but lacks data for strategic value judgments.

Questions the Judge cannot currently answer:

1. Does a competing product (Google ADK, CrewAI, AutoGen) already handle this?
2. Does an existing YAMLGraph abstraction (`type: python`, `type: agent`) already cover this use case?
3. How many production graphs or real-world use cases exist for this feature?
4. Is this a framework primitive, an integration, or a pattern that should be documented?

Evidence: The Philosopher session (April 2026) audited 18 pipelines and found a ~25% false-positive rate — features approved as technically feasible that weren't strategically warranted (e.g., the A2A dedicated node type: 362 lines, one demo, later refactored to 80-line contrib function).

The Judge sits on a 100× cost boundary (~$0.02 Judge call vs. $2–10 Enforce run), making it the optimal intervention point for filtering.

## Proposed Solution

Add a **Research step** between Plan and Judge in the Chaplain pipeline:

```
Issue → Plan (generate FR) → Research (NEW) → Judge → Enforce
```

### 1. Research Node

A single `type: copilot` node inserted into `.chaplain/graphs/copilot/graph.yaml` between `plan` and `judge`. The copilot node is agentic — it has codebase access and multi-step reasoning. One node, one prompt, one structured brief.

```yaml
# New node in .chaplain/graphs/copilot/graph.yaml
research:
  type: copilot
  prompt: research
  backend: cli
  cli_flags:
    allow_all_paths: true
    allow_all_tools: true
    resume: "{state.plan_result.session_id}"
  variables:
    drafts_dir: "{state.drafts_dir}"
  state_key: research_brief
  timeout: 500
```

### 2. Research Prompt

New file `.chaplain/graphs/copilot/prompts/research.yaml` instructs the agent to:

1. Read the drafted FR in `{drafts_dir}/`
2. Search existing YAMLGraph abstractions for overlap (grep node types, examples, contrib)
3. Check `docs/diary/` for relevant traps and prior refactorings
4. Classify the proposal as: primitive | contrib | pattern-doc
5. Produce a structured research brief

```yaml
# .chaplain/graphs/copilot/prompts/research.yaml
system: |
  You are a strategic research analyst for a YAML-first LLM framework.
  Your task is to gather evidence about a proposed feature request and
  produce a structured research brief.

user: |
  **Research.** Read the feature request draft in {drafts_dir}/.

  Investigate:
  1. **Existing abstractions**: Search the codebase for overlapping node types,
     tools, examples, or contrib patterns that already cover this use case.
  2. **Diary precedents**: Check docs/diary/ for traps, patterns, or prior
     refactorings relevant to this proposal.
  3. **Usage evidence**: Count how many graphs/examples use the abstractions
     this feature would create or modify.
  4. **Classification**: Is this a framework primitive (needed by many graphs),
     a contrib/example (1-2 use cases), or a pattern that should be documented?

  Append a `## Research Brief` section to the FR draft with:

  ### Existing Abstractions
  - [What overlaps in YAMLGraph, with file paths]

  ### Diary Precedents
  - [Relevant traps/patterns from docs/diary/]

  ### Usage Evidence
  - Existing graphs using related abstractions: N
  - Real-world use cases beyond the proposal: [list or none]

  ### Classification Signal
  - Abstraction level: primitive | integration | pattern
  - Recommended approach: build | contrib | document | reject
  - Key risk: [one sentence]
```

### 3. Edge Update

Update the edge list in `graph.yaml`:

```yaml
edges:
  - from: START
    to: plan
  - from: plan
    to: research    # NEW
  - from: research
    to: judge       # Changed: was plan → judge
  - from: judge
    to: summarize
  - from: summarize
    to: write_diary
  - from: write_diary
    to: END
```

### 4. Judge Prompt Update

Add one criterion to `.chaplain/graphs/copilot/prompts/judge.yaml`:

```
7. Given the research brief, classify this proposal:
   - **Framework primitive** — 3+ use cases, no existing abstraction fits
   - **Contrib/example** — 1-2 use cases, existing abstractions have gaps
   - **Pattern documentation** — 0 use cases beyond proposal, or existing abstractions suffice
   - **Reject** — Problem not real, or solution creates more complexity than it resolves
```

### 5. State Addition

Add `research_brief` to the graph state declaration:

```yaml
state:
  research_brief: dict   # Output from research node
```

### Cost Analysis

```
Research (copilot agent): ~$0.05, ~30-60 seconds
Judge with brief:         ~$0.02, ~3 seconds
Enforce (if approved):    30-60 minutes, $2-10
```

Research is 0.5% of enforce cost. Preventing one unnecessary feature per month saves the enforce run plus later refactoring.

## Acceptance Criteria

- [x] Research node added to `.chaplain/graphs/copilot/graph.yaml` between plan and judge
- [x] Research prompt produces structured brief with: existing abstractions, diary precedents, usage evidence, classification signal
- [x] Research brief appended to FR draft before Judge evaluation
- [x] Judge prompt includes strategic classification criterion (primitive/contrib/pattern/reject)
- [ ] Judge can redirect an FR to "pattern documentation" based on research brief
- [x] Existing Plan → Judge → Enforce flow works unchanged when Research produces empty/low-confidence brief
- [x] Tests added
- [ ] Documentation updated

## Alternatives Considered

1. **Multi-node research graph** (6 nodes: extract → search × 2 → analyze → consult → synthesize): Over-engineered. The copilot node is agentic — it can search, analyze, and synthesize in one step. Decomposing into pipeline nodes is the `framework_costume` trap.

2. **Mechanical grep pre-check**: Count YAML file references as a proxy for usage. Rejected — the A2A insight came from competitive analysis and strategic classification, not line counts.

3. **Expanded Judge prompt only**: Ask the Judge to reason about strategic value without data. Rejected — the LLM doesn't know what existing abstractions overlap without codebase access or what competitors offer without search.

4. **Human-in-the-loop at Judge**: Correct but doesn't scale for 8 FRs/day autonomous operation.

## Related

- `.chaplain/graphs/copilot/graph.yaml` — target graph to modify
- `.chaplain/watch.sh` — orchestrator (no changes needed; runs graph as-is)
- FR-081 — copilot node type
- FR-105 — session continuation (`resume` flag)
- FR-098/FR-196 — consolidated Chaplain graph
- Philosopher session (April 2026) — source analysis identifying the gap
