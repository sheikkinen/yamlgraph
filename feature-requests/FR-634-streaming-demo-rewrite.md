# Feature Request: Streaming Demo Rewrite

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-07-01
**Depends on:** FR-633

## Summary

Replace `demos/streaming/` (raw Python script) with a proper YAML graph demo that uses `yamlgraph graph run --stream`.

## Value Statement

New users see streaming demonstrated the YAML-first way — same paradigm as every other demo — instead of a Python script that contradicts the framework's identity.

## Problem

The current streaming demo:
- Has no `graph.yaml` (one of 5 demos missing it)
- Is a Python script that imports `execute_prompt_streaming()` directly
- Hardcodes `provider="mistral"` and uses the `greet` prompt from a different demo
- Has no `demo-output.log` (unproven execution)
- Documents `stream: true` per-node annotation which is dead code (FR-635)

This is the #1 feature people look for in an LLM framework, demonstrated via a script that bypasses the framework.

## Proposed Solution

Replace contents of `examples/demos/streaming/` with:

```
demos/streaming/
├── graph.yaml          # 2-node pipeline: draft → polish
├── prompts/
│   ├── draft.yaml      # Generate initial text
│   └── polish.yaml     # Refine the draft
├── README.md           # Shows: yamlgraph graph run graph.yaml --stream
└── demo-output.log     # Captured --stream output
```

### graph.yaml

```yaml
version: "1.0"
name: streaming-demo
description: |
  Two-node pipeline demonstrating token-by-token streaming.
  Run with: yamlgraph graph run graph.yaml --var topic="..." --stream

defaults:
  prompts_relative: true
  prompts_dir: prompts

variables:
  topic:
    type: str
    description: "Topic to write about"

nodes:
  draft:
    type: llm
    prompt: draft
    state_key: draft_text

  polish:
    type: llm
    prompt: polish
    state_key: final_text

edges:
  - from: START
    to: draft
  - from: draft
    to: polish
  - from: polish
    to: END
```

### README.md

Shows three usage modes:
1. `yamlgraph graph run graph.yaml --var topic="streaming" --stream` (CLI)
2. Python API with `run_graph_streaming_native()` (for integration)
3. Comparison: `--stream` vs without (latency perception difference)

## Acceptance Criteria

- [ ] `demos/streaming/graph.yaml` exists and passes `yamlgraph graph lint`
- [ ] `yamlgraph graph run demos/streaming/graph.yaml --var topic="AI" --stream` produces token-by-token output
- [ ] `demo-output.log` captured proving execution
- [ ] Old `demo_streaming.py` removed
- [ ] README documents both CLI and Python API approaches
- [ ] Demo listed in examples/README.md learning path or demos index
- [ ] No reference to `stream: true` per-node annotation (that's dead code per FR-635)

## Alternatives Considered

1. **Keep Python script alongside graph** — Sends mixed signal about how to use the framework. The demo should be opinionated about the YAML-first approach.

2. **Single-node graph** — Too trivial. Two nodes shows that streaming works across the full pipeline (you see tokens from both nodes in sequence).

## Related

- FR-633 (prerequisite — CLI `--stream` flag)
- FR-635 (cleanup — removes the dead per-node `stream: true` that old README documented)
- `examples/demos/streaming/` — current broken demo
- `examples/README.md` — demos index to update
