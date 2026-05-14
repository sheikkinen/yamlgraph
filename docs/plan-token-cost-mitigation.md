# Token Cost Mitigation Plan

Last updated: 2026-05-14

## Background

Two concurrent signals triggered this plan:

1. **GitHub Copilot restructuring** — New signups for Pro, Pro+, Student, and Business paused April 20–22, 2026. Refund window closes May 20, 2026. This signals an imminent pricing model change. YAMLGraph's Chaplain pipeline runs `gpt-5.3-codex` and `claude-sonnet-4.6` via Copilot CLI, exposing it to potential cost spikes from premium request multipliers.

2. **Anthropic batch and caching already available** — Batch API (50% discount) and prompt caching (90% read discount) are live now and underutilised in the current codebase.

---

## Exposure Audit

### Chaplain Pipeline (highest risk)

| Graph | Node | Model | Transport | Risk |
|-------|------|-------|-----------|------|
| step-plan-unified | plan_unified | gpt-5.3-codex | Copilot CLI | HIGH |
| step-judge-v2 | judge | claude-sonnet-4.6 | Copilot CLI | MEDIUM |
| enforce-session | enforce | gpt-5.3-codex | Copilot CLI | HIGH |
| enforce-session | plan_context | mercury-2 | Inception API | LOW |
| validate-session | validate | claude-sonnet-4.6 | Copilot CLI | MEDIUM |
| sanity-check-session | sanity | claude-sonnet-4.6 | Copilot CLI | MEDIUM |

**216 YAML graphs** use `type: copilot` nodes. Not all of these are chaplain — most are examples/demos — but all are exposed to the same Copilot CLI cost structure.

### Anthropic API Current Pricing

| Model | Input | Output | Cache Read | Batch Discount |
|-------|-------|--------|------------|----------------|
| Sonnet 4.6 | $3/MTok | $15/MTok | $0.30/MTok | 50% off |
| Haiku 4.5 | $1/MTok | $5/MTok | $0.10/MTok | 50% off |
| Opus 4.7 | $5/MTok | $25/MTok | $0.50/MTok | 50% off |

Prompt cache read is **90% cheaper** than fresh input on Sonnet 4.6.

---

## Mitigation Work Items

Four FRs, ordered by cost/effort ratio (cheapest value first):

### FR-C — Prompt Caching for Chaplain System Prompts

**Mechanism:** Convert chaplain `system:` blocks to `system_segments:` with `cache: true` on static sections (Scripture, CLAUDE.md excerpts, ARCHITECTURE.md excerpts). YAMLGraph already supports this syntax (FR-prior). Zero Python code change required — pure YAML configuration.

**Expected savings:** 80–90% on input tokens for repeat chaplain invocations within 5-minute cache TTL. The chaplain FSM invokes plan→judge→enforce in rapid succession — all three can share a warm cache from the same system prompt corpus.

**Files affected:**
- `.chaplain/graphs/watcher-plan/prompts/judge.yaml`
- `.chaplain/graphs/watcher-plan/prompts/plan.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/*.yaml`
- `.chaplain/graphs/watcher-diary/prompts/*.yaml`

**Scope:** YAML-only. No feature request required; straightforward configuration change.

---

### FR-A — Copilot Node `backend: api` Fallback

**Mechanism:** Add `backend: api` as an alternative to `backend: cli` in `type: copilot` nodes. When `backend: api`, the node routes directly to `execute_prompt()` using the configured `model` and `provider` (bypassing the Copilot CLI subprocess entirely). This is a pure hedge — Copilot CLI remains the default for agentic coding tasks.

**Rationale:** If Copilot premium request multipliers spike after the restructuring, chaplain can be switched to `backend: api` with a one-line YAML change per graph. No pipeline rewrite required.

**Files affected:**
- `yamlgraph/node_factory/copilot_node.py` — add API execution path
- `yamlgraph/node_compiler.py` — pass backend flag
- `.chaplain/graphs/*/` — add fallback config comments

**Acceptance criteria:**
- `type: copilot` with `backend: api` produces a `CopilotResult` with `backend: "api"`
- Existing `backend: cli` behaviour unchanged
- Linter warns when `backend: api` is used without `model:` specified

---

### FR-B — Anthropic Batch API for LLM Nodes

**Mechanism:** Add `use_batch: true` to `type: llm` node config. Implement `yamlgraph/utils/batch_executor.py` wrapping the Anthropic Message Batches API. Non-interactive chaplain nodes (judge, validate, sanity) do not require synchronous streaming — they can be submitted as batch jobs.

**Expected savings:** 50% on all input and output tokens for batch-eligible nodes.

**Constraints:**
- Batch is async by nature (up to 24h, typically minutes). Requires polling or webhook.
- Not suitable for nodes where the next node depends on the result immediately in a synchronous FSM run. Chaplain judge is synchronous today — this may require a pipeline architecture change (async FSM step).
- Opt-in only (`use_batch: false` default). Graceful fallback to sync if batch unavailable or times out.

**Files affected:**
- `yamlgraph/utils/batch_executor.py` (new)
- `yamlgraph/node_factory/llm_node.py`
- `yamlgraph/models/graph_schema.py` — add `use_batch` field

---

### FR-D — Cost Profile / Model Tiering

**Mechanism:** Add `cost_profile: economy | balanced | premium` to graph `defaults:`. Allow `YAMLGRAPH_COST_PROFILE` environment variable override. Each profile maps to a set of default models per provider.

| Profile | Anthropic default | OpenAI default |
|---------|------------------|----------------|
| economy | claude-haiku-4-5 | gpt-5-mini |
| balanced | claude-sonnet-4-6 | gpt-5.4 |
| premium | claude-opus-4-7 | gpt-5.5 |

Update graph linter (`yamlgraph/linter/checks_providers.py`) to emit a warning when Opus-tier models are used without an explicit `# cost: justified` comment on the node.

**Files affected:**
- `yamlgraph/config.py` — add `COST_PROFILE` env var
- `yamlgraph/utils/llm_factory.py` — resolve model from profile
- `yamlgraph/models/graph_schema.py` — add `cost_profile` field
- `yamlgraph/linter/checks_providers.py` — add Opus-without-justification lint check

---

## Priority Order

| Priority | FR | Effort | Expected Savings |
|----------|----|--------|-----------------|
| 1 | FR-C — Prompt caching | Hours (YAML) | 80–90% on repeated input |
| 2 | FR-A — backend: api | Days | Removes Copilot pricing exposure |
| 3 | FR-B — Batch API | Days | 50% on batch-eligible nodes |
| 4 | FR-D — Cost profiles | Days | Governance, prevents drift |

---

## Non-Goals

- Removing Copilot CLI support (it remains the primary agentic coding backend)
- Switching default provider away from Anthropic
- Breaking changes to existing public graph YAML API
- Automatic cost monitoring / billing alerts (out of scope; deployment concern)

---

## Seeds

- Could a cost estimator node run *before* expensive nodes and route to economy tier when the task is simple?
- Should the Chaplain FSM emit a cost summary after each plan→judge→enforce cycle?
- Is there a batch-compatible variant of the chaplain FSM where plan and judge run in parallel (judge reads a committed artifact, not streaming plan output)?
