# Feature Request: Watcher Pipeline FSM Simplification

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-05-02
**Judged:** 2026-05-02

## Summary

Collapse the 20+ state watcher pipeline FSM into 6 operational states with an enforce⇄validate loop, leveraging copilot session continuations (FR-105) for fix iterations.

## Value Statement

Pipeline maintainers get a state machine that fits in one's head, with fewer failure modes and simpler context propagation, while retaining full audit-trail commits and the TDD workflow.

## Problem

The current `watcher-pipeline.yaml` has 20+ states with complex context threading across subprocess boundaries. Each enforce sub-step (implement, test, critique, changelog, finalize) runs as a separate cold-start LLM invocation, losing context between iterations. CI remediation spawns yet another subprocess with no memory of what was already attempted.

Key pain points:
1. **Context loss** — Each `yamlgraph_async` action is a new process; the LLM re-discovers the codebase every time
2. **Fragile context propagation** — `{placeholder}` interpolation across 20+ states means any missing key crashes as a bash error, not a type error
3. **Debugging difficulty** — Failures in state 15 of 20 require tracing back through the entire chain
4. **Over-modeled commits** — Individual FSM states for each `git commit` add orchestration cost without proportional value

## Proposed Solution

### New FSM: 6 States

```
plan → commit_plan → judge →(approve)→ enforce → validate → done
  ↑                  revise               ↑        │
  └─────────────────────┘                 └────────┘ (fix_needed, resumes session)
                                           │
                                           ▼ (max retries)
                                        failed
```

### State Definitions

| State | Action | Session |
|-------|--------|--------|
| `plan` | Single copilot node — worktree setup, FR drafting, research | New session (model A, e.g. claude-sonnet) |
| `commit_plan` | `git_commit` — all planning artifacts (FR + research) in one commit | N/A |
| `judge` | Copilot node — reads FR + research artifacts, renders APPROVE/REVISE/REJECT | New session, **different model** (model B, e.g. gpt-5.3-codex) — fresh eyes + different reasoning biases |
| `enforce` | Copilot node, `allow_all_tools: true` — TDD: write tests, verify-red, implement, commit | New session on first entry; resumes own `session_id` on re-entry from validate |
| `validate` | Bash — runs `pre-commit run --all-files` + `pytest tests/ --no-cov -x` | N/A (no LLM) |
| `done` | Bash — push, create PR, wait CI, merge, cleanup. CI failure → `failed` | N/A |

### Design Principle: Session & Model Independence

Plan and judge MUST use:
1. **Different sessions** — no shared context, no anchoring
2. **Different models** — different reasoning biases catch different flaws

The judge evaluates only the committed artifacts (FR + research), not the planner's internal reasoning. A different model ensures the judge isn't pattern-matching against the planner's style.

### `enforce` Design

First entry: starts a fresh copilot session. Reads the approved FR, writes acceptance tests, verifies RED, implements to GREEN, generates changelog fragment, commits.

Re-entry (from validate failure): resumes its own session via `resume: session_id`. The LLM already knows what it implemented and can read the pre-commit/pytest errors passed in context. Fixes and commits.

Session ID capture: the copilot action uses `--share` flag; the FSM action config includes `capture_keys: [session_id]` to store it in context for subsequent `resume` on re-entry.

### `validate` Design

Pure bash — no LLM. Runs:
1. `pre-commit run --all-files`
2. `pytest tests/ --no-cov -x`

If both pass → `pass` event → `done`.
If either fails → `fix_needed` event → back to `enforce` (which resumes session).
Tracks `validate_attempt` in context (max 5). If exceeded → `error` → `failed`.

Timeout at FSM level (900s) on enforce is the additional safety net.

All bash states (`validate`, `done`) use internal command timeouts (120s per command) to prevent hangs.

### Transitions

```yaml
transitions:
  - from: plan
    to: commit_plan
    event: plan_done

  - from: commit_plan
    to: judge
    event: committed

  - from: judge
    to: enforce
    event: approve

  - from: judge
    to: plan
    event: revise

  - from: judge
    to: failed
    event: reject

  - from: enforce
    to: validate
    event: enforce_done

  - from: validate
    to: done
    event: pass

  - from: validate
    to: enforce
    event: fix_needed

  - from: validate
    to: failed
    event: error

  - from: enforce
    to: failed
    event: error

  - from: plan
    to: failed
    event: "timeout(600)"

  - from: judge
    to: failed
    event: "timeout(600)"

  - from: enforce
    to: failed
    event: "timeout(900)"

  - from: validate
    to: failed
    event: "timeout(120)"

  - from: done
    to: failed
    event: "timeout(300)"

  - from: "*"
    to: stopped
    event: stop
```

### Files to Create

| File | Purpose |
|------|---------|
| `.chaplain/config/watcher-pipeline-v2.yaml` | Simplified FSM config |
| `.chaplain/graphs/watcher-plan/step-plan-unified.yaml` | Combined plan graph |
| `.chaplain/graphs/watcher-enforce/enforce.yaml` | Copilot node for TDD enforce step |
| `.chaplain/prompts/enforce.yaml` | Prompt for the enforce copilot node |

### Files to Retire (after validation)

| File | Replaced by |
|------|-------------|
| `.chaplain/graphs/watcher-enforce/step-implement.yaml` | `enforce.yaml` |
| `.chaplain/graphs/watcher-enforce/step-test-demo.yaml` | `enforce.yaml` |
| `.chaplain/graphs/watcher-enforce/step-critique.yaml` | `enforce.yaml` |
| `.chaplain/graphs/watcher-enforce/step-ci-remediate.yaml` | `enforce.yaml` |
| `.chaplain/graphs/watcher-enforce/step-finalize.yaml` | `enforce.yaml` |

## Scope Freeze

- 6 operational states + 2 terminals (failed, stopped). No more.
- Dispatcher unchanged.
- statemachine-engine unchanged.
- CI remediation out of scope (CI failure in `done` → `failed`).

## Implementation Order

1. Create `watcher-pipeline-v2.yaml` (FSM config — validate structure)
2. Create `enforce.yaml` graph + prompt (the novel piece)
3. Create `step-plan-unified.yaml` graph (consolidation)
4. Wire dispatcher to invoke v2 config (flag-gated)
5. Validate on test topic
6. Retire old graphs after 3 successful runs

## Acceptance Criteria

- [x] `watcher-pipeline-v2.yaml` validates with `statemachine` CLI
- [x] `plan` state produces FR + research in one invocation (no tests)
- [x] `judge` uses fresh session, **different model**, and routes to approve/revise/reject
- [x] `revise` loops back to plan
- [x] `enforce` performs full TDD (write tests → RED → implement → GREEN → commit)
- [x] `enforce` resumes own session on re-entry from validate with error context
- [ ] `validate` runs pre-commit + pytest, loops back to enforce on failure (max 5)
- [x] `done` state pushes, creates PR, and merges
- [x] Old pipeline remains available as fallback
- [x] Tests added for FSM transition correctness
- [ ] Dispatcher integration on test topic (stretch)

## Alternatives Considered

1. **Keep 20+ states, add session resume to each** — Retains granular visibility but doesn't solve the context-loss problem between enforce sub-steps. Rejected: complexity without benefit.

2. **Collapse to 2 states (plan, enforce)** — Too coarse; no commit checkpoint between planning and enforcement means a failed enforce loses all planning work. Rejected: no audit trail.

3. **Use LangGraph subgraph for enforce loop** — Would work but adds a framework layer between FSM and copilot. The copilot node with `allow_all_tools` already has terminal access to run tests itself. Rejected: unnecessary indirection.

## Related

- FR-105: Copilot session continuations (the `resume` mechanism)
- FR-273: Copilot session chain with shell steps
- FR-274: Session ID extraction from share files
- FR-290: Watcher FSM Phase 0 configs
- FR-291: Watcher FSM Phase 1 action wiring
- FR-292: Pipeline path alignment
- FR-295: Phase 2 single worker validation
- `.chaplain/config/watcher-pipeline.yaml` (current implementation)
- `.chaplain/graphs/copilot/graph.yaml` (session continuation pattern)
