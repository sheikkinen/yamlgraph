# Diary: The Trilogy — Demo vs Production Plan/Judge/Enforce

**Date:** 2026-05-31
**Context:** Rigorous analysis of the Plan, Judge, Enforcer demo graphs vs their production counterparts in the Chaplain pipeline.
**Trap:** `gate_checks_shape_not_substance` + `mock_escape_hatch`

## The Artifacts

### Demo Trilogy (examples/demos/)

| Component | Graph | Prompt | Tools | Node type |
|-----------|-------|--------|-------|-----------|
| Planner | 55 lines | 68 lines | 5 shell + 1 python | `type: agent` |
| Judge | 55 lines | 79 lines | 5 shell + 1 python | `type: agent` |
| Enforcer | 85 lines | 68 lines | 8 shell + 2 python | `type: agent` |
| **Total** | **195 lines** | **215 lines** | **14 shell + 4 python** | |

### Production Pipeline (.chaplain/)

| Component | Graph | Prompt(s) | Tools | Node type | Orchestrator |
|-----------|-------|-----------|-------|-----------|-------------|
| Planner | 50 lines (1 node) | 47+44+27 = 118 lines | copilot's full toolset | `type: copilot` | FSM state `plan` |
| Judge | 36 lines (1 node) | 54 lines | copilot's full toolset | `type: copilot` | FSM state `judge` |
| Enforcer | 78 lines (4 nodes) | 76+48 = 124 lines | copilot's full toolset + 2 python | `type: copilot` | FSM state `enforce_session` |
| Validate | separate graph | 75 lines | copilot's full toolset | `type: copilot` | FSM state `validate_fix` |
| Sanity Check | separate graph | 63 lines | copilot's full toolset | `type: copilot` | FSM state `sanity_check` |
| FSM | 428 lines | — | — | — | watcher-pipeline-v2.yaml |
| **Total** | **~592 lines** | **~434 lines** | **copilot CLI** | | **12 states, 30 transitions** |

## Structural Differences

### 1. Node Type: `agent` vs `copilot`

The demos use `type: agent` — yamlgraph's built-in tool-calling loop. The LLM receives a list of shell/python tools, decides which to call, executes them, reads results, iterates up to `max_iterations`.

Production uses `type: copilot` — shells out to the Copilot CLI (`gpt-5.3-codex` for plan/enforce, `claude-sonnet-4.6` for judge). The copilot process has its own tool discovery, file access, terminal access, and context window management. YAMLGraph doesn't see the intermediate tool calls — it fires a subprocess and waits for the result.

**Implication:** The demos exercise yamlgraph's agent node type (tool loop is visible, traceable, bounded by `max_iterations`). Production exercises the copilot node type (tool loop is opaque, bounded only by timeout). The demo is testable at the framework level; production is testable only at the outcome level.

### 2. Model Independence: Enforced vs Absent

Production enforces model independence between Plan and Judge:

```yaml
# step-judge-v2.yaml comment:
# Design: judge MUST NOT share session with plan (no anchoring bias).
# Uses a DIFFERENT model from plan to catch different classes of errors.
```

Plan uses `gpt-5.3-codex`. Judge uses `claude-sonnet-4.6`. Different vendor, different weights, different failure modes.

The demos both use `defaults: provider: mistral` (planner) or no default (judge/enforcer — falls back to project default). There's no architectural enforcement of model independence.

**Implication:** The demos demonstrate the *shape* of plan-judge-enforce but not the *substance*. The crucial adversarial property — different models catching different errors — is absent. This is the `mock_escape_hatch` trap: a demo that exercises the mechanism but not the phenomenon.

### 3. FSM Orchestration: Present vs Absent

Production wraps the trilogy in a 428-line FSM with:

- **Revise loop:** `judge → plan` on AMEND verdict (retry the plan with judge feedback)
- **Validate loop:** `validate_gate → validate_fix` up to 5 times (pre-commit + lint + test)
- **Timeouts:** 600s for plan/judge, 3600s for enforce
- **Error routing:** every state has `→ failed` on error
- **Global shutdown:** `from: "*" → stopped` on stop signal
- **Cost ceiling:** timeout is the implicit budget (no €47 runaway loops)
- **Post-enforcement gates:** micro_changelog → micro_title → sanity_check → validate_gate → done → push/PR/CI/merge

The demos have no orchestration — they're standalone graphs with `START → agent → END`. No retries, no revise loops, no validation gates, no cost ceiling.

**Implication:** The demos are *unit tests* of the agent's reasoning ability. Production is a *system test* of the complete pipeline including error recovery, budget control, and quality gates. The gap between them is the FSM — which is the entire point of the FSM-as-conductor pattern.

### 4. Context Assembly: Bounded vs Unbounded

Production (enforce-session) has a 4-node graph:

```
load_module_map → plan_context → assemble_context → enforce
```

The context planner (Mercury-2, deterministic) reads the static module map and selects task-relevant files. The assembler reads those files. The enforcer receives pre-assembled context — it doesn't waste iterations discovering the codebase.

The demo enforcer starts with zero context and must discover everything via tool calls (`read_file`, `search`, `list_dir`). With `max_iterations: 25`, it spends 5-10 iterations just orienting before it starts implementing.

**Implication:** Production invests cheap tokens (Mercury-2 context planning) to save expensive tokens (Codex implementation time). The demos can't do this because the agent node doesn't support multi-model pipelines within a single graph node — the graph topology is the mechanism for model handoff.

### 5. Tool Surface: Constrained vs Unbounded

Demos: 5-10 explicitly declared shell/python tools. The agent can only call what's listed.

Production copilot: `allow_all_paths: true, allow_all_tools: true`. The copilot CLI has full filesystem access, terminal access, and its own tool discovery. The constraint is the prompt instruction, not the tool list.

**Implication:** Demos are *sandboxed by construction* (you can't call what isn't declared). Production is *sandboxed by instruction* (the prompt says "work in {worktree_dir}" but nothing prevents escaping). The FSM's worktree isolation (`worktree_setup.sh`) provides the filesystem boundary that the copilot node lacks internally.

## What the Demos Prove

1. **The agent node can research, evaluate, and implement.** A single `type: agent` node with shell/python tools can perform non-trivial multi-step reasoning tasks.

2. **Structured output works.** Each demo produces a typed schema (`PlanResult`, `JudgeVerdict`, `ImplementationResult`) from free-form agent reasoning.

3. **The graph is trivially simple.** `START → agent → END`. The complexity lives in the prompt, not the topology.

4. **The pattern is portable.** No Copilot CLI dependency, no FSM dependency, no worktree isolation. Runs with `yamlgraph graph run` and any LLM provider.

## What the Demos Don't Prove

1. **Adversarial independence.** Same model can plan and judge its own work — confirmation bias is architecturally possible.

2. **Error recovery.** No revise loop, no validate-fix cycle. If the agent produces a bad plan or fails to implement, the graph ends.

3. **Cost control.** `max_iterations: 25` is the only budget. No timeout, no cost ceiling, no escalation path.

4. **Quality gates.** No pre-commit, no lint gate, no test gate between enforce and "done." The agent self-reports `tests_passed: true` without external verification.

5. **Isolation.** The agent has shell access to the working directory. No worktree boundary, no branch protection.

## The Gap Is the FSM

The difference between the demo trilogy and the production pipeline is exactly the FSM config (428 lines). That config provides:

| Concern | FSM mechanism | Demo equivalent |
|---------|--------------|-----------------|
| Retry on judge AMEND | `judge → plan` transition on `revise` event | None |
| Error escalation | Every state `→ failed` on `error` | Agent returns `success: false` |
| Timeout budget | `timeout(600)` / `timeout(3600)` events | `max_iterations` only |
| Quality verification | `validate_gate` (deterministic, no LLM) | Self-reported by agent |
| Post-enforcement cleanup | `micro_changelog → micro_title → sanity_check` | None |
| Deployment | `done` action: push → PR → CI → merge → teardown | Manual |
| Global shutdown | `from: "*" → stopped` on `stop` | None |
| Cost ceiling | Timeout = implicit $/run cap | Unbounded within iteration limit |

This confirms the FSM-as-conductor thesis: the FSM provides lifecycle guarantees that the graph cannot. The graph provides reasoning quality that the FSM cannot. They're complementary, not competitive.

## Trap

`gate_checks_shape_not_substance` — the demos validate that the *shape* of plan-judge-enforce works (agent can produce structured output following a process). They don't validate the *substance* (different models catching different errors, recovery from failure, external quality verification). The shape passes the demo-gate CI check (output captured, demo runs). The substance requires the full FSM orchestration.

Also `mock_escape_hatch` — the demo uses `type: agent` (transparent, bounded) as a stand-in for `type: copilot` (opaque, unbounded). They exercise the same logical flow but different computational mechanisms. A test that passes on the demo doesn't prove the production pipeline works — the failure modes are different (iteration exhaustion vs timeout, tool-not-found vs tool-escape, self-reported success vs gate-verified success).

## Heuristic

**The demo proves the reasoning; the FSM proves the system.** Don't conflate demo success with production readiness. The gap between them is exactly the error recovery, cost control, and quality verification that makes production systems trustworthy. When evaluating "does the pipeline work?" — ask: which layer is being tested? The agent's reasoning ability (demo), or the system's failure recovery (FSM + gates)?

## Seed

The demo trilogy exists at exactly the right abstraction level for a different purpose than production: **onboarding and development.** A developer building a custom plan-judge-enforce pipeline for their domain starts with the demo pattern (portable, any provider, no FSM dependency), then graduates to the FSM-orchestrated pattern when they need error recovery and cost control. The graduation path is: `type: agent` → `type: copilot` → FSM wrapping. Is that path documented? Is it obvious that the demo is a stepping stone, not a destination?
