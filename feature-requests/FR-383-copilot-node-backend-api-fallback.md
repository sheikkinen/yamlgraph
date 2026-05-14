# Feature Request: FR-383 Copilot node `backend: api` fallback

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-05-14

## Summary

Add `backend: api` as an alternative execution path in `type: copilot` nodes.
When set, the node routes directly to `execute_prompt()` using the configured
`model` and `provider`, bypassing the Copilot CLI subprocess entirely.
This is a hedge against GitHub Copilot pricing restructuring — switchable
with a single YAML change per graph, no pipeline rewrite required.

## Value Statement

If GitHub Copilot premium request multipliers spike after the April 2026
restructuring, the Chaplain pipeline can be switched to direct API calls
(`backend: api`) with a one-line config change per graph, preserving
all prompt logic without rewriting the pipeline.

## Problem

**GitHub Copilot pricing context:** New signups for Pro, Pro+, Student, and
Business plans were paused April 20–22, 2026. Refund window closes May 20, 2026.
This signals an imminent pricing model change. Copilot premium requests
(GPT-5.3-Codex, Claude Sonnet via Copilot) may carry undisclosed multipliers.

The Chaplain pipeline runs 5 `type: copilot` nodes per FR cycle:

| Graph | Node | Current model |
|-------|------|--------------|
| step-plan-unified | plan_unified | gpt-5.3-codex (Copilot CLI) |
| step-judge-v2 | judge | claude-sonnet-4.6 (Copilot CLI) |
| enforce-session | enforce | gpt-5.3-codex (Copilot CLI) |
| validate-session | validate | claude-sonnet-4.6 (Copilot CLI) |
| sanity-check-session | sanity | claude-sonnet-4.6 (Copilot CLI) |

All 5 are exposed to Copilot CLI pricing. If cost spikes, there is currently
no fallback path except a full pipeline rewrite.

Currently, `type: copilot` always routes through the CLI subprocess:
```python
# copilot_node.py
return CopilotResult(..., backend="cli")
```

There is no `backend:` field in `NodeConfig` or the YAML schema.

## Research

### Existing patterns

- `yamlgraph/executor.py::execute_prompt()` — the standard LLM call path.
  Supports all providers, structured output, streaming. Already used by all
  `type: llm` nodes.
- `yamlgraph/node_factory/copilot_node.py` — CLI subprocess path, returns
  `CopilotResult` Pydantic model.
- `CopilotResult` already has a `backend: str` field (currently always `"cli"`).

### Key difference: CLI vs API for agentic tasks

The Copilot CLI is not just an LLM call — it provides:
1. File system tool access (read/write files, run bash)
2. Session continuity across tool calls
3. Streaming output
4. Pre-configured system instructions (`.github/copilot-instructions.md`)

`backend: api` is appropriate for **reasoning-only** nodes (judge, validate,
sanity check) that do not need tool calls — they analyze a prompt and return
structured output. The `enforce` node **requires** tool access and should
remain `backend: cli`.

## Proposed Solution

### YAML interface

```yaml
nodes:
  judge:
    type: copilot
    prompt: judge
    backend: api           # NEW: "cli" (default) | "api"
    provider: anthropic    # used only when backend: api
    model: claude-sonnet-4-6
    state_key: judgment
```

### Execution model

When `backend: api`:
1. Load prompt YAML as normal (Jinja2 rendering, variable injection)
2. Call `execute_prompt()` directly — same path as `type: llm` nodes
3. Return `CopilotResult` with `backend="api"` and the response text
4. Structured output (`schema:`) supported via existing `_parse_structured_output`

When `backend: cli` (default, unchanged):
- Existing subprocess path, unchanged behavior

### Linter check

```
WARNING: node 'judge' uses type: copilot with backend: api but no model: specified.
  Add model: to select the target API model.
```

Error (not warning) if `backend: api` and `type: copilot` node has `tools:` set
(tool access requires CLI backend).

### Files to modify

| File | Change |
|------|--------|
| `yamlgraph/node_factory/copilot_node.py` | Add API execution branch |
| `yamlgraph/models/graph_schema.py` | Add `backend: str = "cli"` to NodeConfig |
| `yamlgraph/linter/checks_providers.py` | Lint: warn on missing model, error on tools+api |
| `reference/graph-yaml.md` | Document `backend:` field |
| `tests/unit/test_copilot_node_backend.py` | New unit tests |

## Acceptance Criteria

- [ ] AC-01: `type: copilot` with `backend: api` calls `execute_prompt()` and
  returns `CopilotResult` with `backend="api"`
- [ ] AC-02: `type: copilot` with `backend: cli` (or no `backend:` field)
  behaves identically to current behavior
- [ ] AC-03: Linter warns when `backend: api` is used without `model:` specified
- [ ] AC-04: Linter errors when `backend: api` is combined with `tools:` on the node
- [ ] AC-05: `CopilotResult` structured output (`schema:`) works with `backend: api`
  using existing `_parse_structured_output`
- [ ] AC-06: Switching `.chaplain/graphs/watcher-plan/step-judge-v2.yaml` judge
  node to `backend: api` passes `yamlgraph graph lint` without errors
- [ ] AC-07: Existing copilot CLI tests pass unchanged
- [ ] Tests added with `@pytest.mark.req("REQ-YG-XXX")`
- [ ] New requirement added to `ARCHITECTURE.md` and `scripts/req_coverage.py`
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary reflection in `docs/diary/`

## Constraints

1. Default `backend: cli` — zero behavior change for existing graphs.
2. `backend: api` does not replicate tool access. It is suitable only for
   reasoning-only nodes. Document this clearly.
3. The `.github/copilot-instructions.md` Scripture injected by Copilot CLI
   is **not** automatically injected in `backend: api` mode. Prompts that
   rely on it must include the relevant sections explicitly (or via FR-382
   cached system segments).
4. No changes to the Copilot CLI subprocess path.

## Alternatives Considered

### Replace Copilot CLI entirely
Rejected: Copilot CLI provides agentic file editing with tool access that
`execute_prompt()` does not. The enforce node genuinely needs CLI backend.

### Per-graph provider env var override
`PROVIDER` env var already switches the default provider for `type: llm`.
`type: copilot` ignores it. Extending `type: copilot` to respect `PROVIDER`
would be messier than an explicit `backend:` field.

## Related

- `docs/plan-token-cost-mitigation.md` — Priority 2 in the mitigation plan
- FR-382 — Prompt caching (Priority 1, should land first)
- FR-381 — Batch API (Priority 3)
- `yamlgraph/node_factory/copilot_node.py` — implementation target
