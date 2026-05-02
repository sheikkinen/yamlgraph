# Feature Request: Watcher Pipeline FSM Simplification

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-05-02

## Summary

Collapse the 20+ state watcher pipeline FSM into 5 operational states by leveraging copilot session continuations (FR-105) for the enforce→evaluate loop.

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

### New FSM: 5 States

```
plan → commit_plan → judge →(approve)→ enforce_session → done
                       ↑ revise                │ timeout
                       └────────┘              ▼
                                            failed
```

### State Definitions

| State | Action | Session |
|-------|--------|---------|
| `plan` | Single copilot node — worktree setup, FR drafting, research, acceptance tests, verify-red | New session (captures `session_id`) |
| `commit_plan` | `git_commit` — all planning artifacts in one commit | N/A |
| `judge` | Copilot node with `resume: session_id` — renders APPROVE/REVISE/REJECT | Continues plan session |
| `enforce_session` | Copilot node with `resume: session_id`, `allow_all_tools: true` — implement + pre-commit + pytest loop within one invocation | Continues same session |
| `done` | Bash — push, create PR, wait CI, merge, cleanup | N/A |

### `enforce_session` Design

Uses the existing copilot node `resume` feature (FR-105). The prompt instructs copilot to:
1. Read acceptance tests as specification
2. Implement the FR
3. Run `pre-commit run --all-files`
4. Run `pytest tests/ --no-cov -x`
5. If failures: read errors, fix, re-run (iterate within session)
6. Generate changelog fragment
7. Commit when green

The entire implement→evaluate→fix loop runs **inside one copilot session** — no FSM transitions for retries. The LLM retains full context of errors and attempted fixes.

Timeout at FSM level (900s) is the safety net.

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
    to: enforce_session
    event: approve

  - from: judge
    to: plan
    event: revise

  - from: judge
    to: failed
    event: reject

  - from: enforce_session
    to: done
    event: pass

  - from: enforce_session
    to: failed
    event: error

  - from: plan
    to: failed
    event: "timeout(600)"

  - from: judge
    to: failed
    event: "timeout(600)"

  - from: enforce_session
    to: failed
    event: "timeout(900)"

  - from: "*"
    to: stopped
    event: stop
```

### Files to Create

| File | Purpose |
|------|---------|
| `.chaplain/config/watcher-pipeline-v2.yaml` | Simplified FSM config |
| `.chaplain/graphs/watcher-plan/step-plan-unified.yaml` | Combined plan graph |
| `.chaplain/graphs/watcher-enforce/enforce-session.yaml` | Single copilot node for enforce+evaluate |
| `.chaplain/prompts/enforce-session.yaml` | Prompt for the enforce copilot node |

### Files to Retire (after validation)

| File | Replaced by |
|------|-------------|
| `.chaplain/graphs/watcher-enforce/step-implement.yaml` | `enforce-session.yaml` |
| `.chaplain/graphs/watcher-enforce/step-test-demo.yaml` | `enforce-session.yaml` |
| `.chaplain/graphs/watcher-enforce/step-critique.yaml` | `enforce-session.yaml` |
| `.chaplain/graphs/watcher-enforce/step-ci-remediate.yaml` | `enforce-session.yaml` |
| `.chaplain/graphs/watcher-enforce/step-finalize.yaml` | `enforce-session.yaml` |

## Acceptance Criteria

- [ ] `watcher-pipeline-v2.yaml` validates with `statemachine` CLI (valid FSM config)
- [ ] `plan` state produces FR + acceptance tests + commit in one invocation
- [ ] `judge` resumes plan session and routes to approve/revise/reject
- [ ] `revise` loops back to plan (integration test with mock)
- [ ] `enforce_session` runs implement→evaluate loop in single copilot session
- [ ] `enforce_session` handles pre-commit + pytest failures with in-session fixes
- [ ] `done` state pushes, creates PR, and merges
- [ ] Dispatcher invokes v2 pipeline successfully on a test topic
- [ ] Old pipeline remains available as fallback until v2 is validated in production
- [ ] Tests added for FSM transition correctness

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
