# FR-183: Simplify Enforce Pipeline

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-10

## Summary

Reduce the enforce pipeline from 7 nodes to 4 by merging critique+distill into one step, merging precommit+submit into one step, and removing the refine loop entirely.

## Value Statement

Pipeline maintainers get a simpler, faster enforce pipeline with fewer session continuations and less surface area for failure, while preserving all essential outputs (diary reflection, PR submission).

## Problem

The current enforce pipeline (`examples/enforce/graph.yaml`) has 7 nodes across 4 phases:

```
implement → test_and_demo → critique → [refine loop] → distill_reflection → precommit_check → submit_pr
```

Three problems:

1. **The refine loop is already dead code.** The reflexion loop (FR-169) is disabled because copilot nodes return strings, not structured objects with `.score` fields (see graph.yaml line 143–145). The `refine` node and `loop_limits`/`loop_exits` config exist but are never reached. Dead code violates Commandment 8.

2. **Critique and distill are two session continuations for one cognitive act.** Critique evaluates the implementation; distill writes a diary entry from that evaluation. Both run in the same session context. Merging them into a single prompt eliminates one session handoff and keeps the evaluation context fresh for reflection.

3. **Precommit and submit are two session continuations for one mechanical act.** Run hooks, fix failures, commit, push, create PR — this is a single "finalize and ship" step. Splitting it across two nodes adds a session continuation with no benefit.

## Proposed Solution

Reduce to 4 nodes with a linear flow:

```
implement → test_and_demo → critique_and_distill → finalize
```

### Graph changes (`examples/enforce/graph.yaml`)

```yaml
version: "1.0"
name: enforce-pipeline
description: |
  End-to-end feature enforcement in isolated worktree.
  Four phases: implement → test/demo → critique+distill → finalize.
  All phases chain via session continuations (FR-105).

state:
  fr_path: str
  branch: str
  implement_result: dict
  test_result: dict
  critique_result: dict
  finalize_result: dict

nodes:
  implement:
    type: copilot
    prompt: enforce-implement
    # ... unchanged

  test_and_demo:
    type: copilot
    prompt: enforce-test-demo
    # ... unchanged

  critique_and_distill:
    type: copilot
    prompt: enforce-critique-and-distill
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    variables:
      fr_path: "{state.fr_path}"
    state_key: critique_result
    timeout: 600  # 10 min

  finalize:
    type: copilot
    prompt: enforce-finalize
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    variables:
      branch: "{state.branch}"
      fr_path: "{state.fr_path}"
    state_key: finalize_result
    timeout: 1800  # 30 min

edges:
  - from: START
    to: implement
  - from: implement
    to: test_and_demo
  - from: test_and_demo
    to: critique_and_distill
  - from: critique_and_distill
    to: finalize
  - from: finalize
    to: END
```

### New prompts

**`enforce-critique-and-distill.yaml`** — Single prompt that:
1. Reads FR, extracts acceptance criteria
2. Runs `git diff main` to evaluate changes
3. Produces structured critique (score, feedback, criteria status)
4. Writes diary reflection to `docs/diary/YYYY-MM-DD-reflection-fr-NNN.md`

Critique feedback is captured in the diary entry rather than feeding an autonomous refine loop. Issues are addressed during PR review.

**`enforce-finalize.yaml`** — Single prompt that:
1. Runs `pre-commit run --all-files`
2. Fixes failures iteratively until clean
3. Stages, commits (Conventional Commits + FR ref), pushes
4. Creates PR via `gh pr create`

### Files to delete

- `enforce-critique.yaml` (merged into critique-and-distill)
- `enforce-distill.yaml` (merged into critique-and-distill)
- `enforce-refine.yaml` (removed — dead code)
- `enforce-precommit.yaml` (merged into finalize)
- `enforce-submit-pr.yaml` (merged into finalize)

### State changes

Remove unused state keys:
- `refine_result` (refine node removed)
- `reflection_draft` (merged into critique_result)
- `precommit_result` (merged into finalize_result)
- `pr_result` (merged into finalize_result)

Remove `loop_limits` and `loop_exits` sections (no loops).

## Acceptance Criteria

- [ ] AC-1: Graph has exactly 4 nodes: `implement`, `test_and_demo`, `critique_and_distill`, `finalize`
- [ ] AC-2: Graph has exactly 5 edges forming a linear chain (START→implement→test_and_demo→critique_and_distill→finalize→END)
- [ ] AC-3: No `loop_limits` or `loop_exits` in graph config
- [ ] AC-4: `enforce-critique-and-distill.yaml` prompt exists and covers both critique evaluation and diary reflection writing
- [ ] AC-5: `enforce-finalize.yaml` prompt exists and covers pre-commit fixes, commit, push, and PR creation
- [ ] AC-6: Old prompts deleted: `enforce-critique.yaml`, `enforce-distill.yaml`, `enforce-refine.yaml`, `enforce-precommit.yaml`, `enforce-submit-pr.yaml`
- [ ] AC-7: State schema has no orphaned keys (`refine_result`, `reflection_draft`, `precommit_result`, `pr_result` removed)
- [ ] AC-8: `yamlgraph graph lint examples/enforce/graph.yaml` passes
- [ ] AC-9: End-to-end test: `scripts/enforce_worktree.sh` completes successfully with simplified pipeline
- [ ] AC-10: Graph header comments updated to reflect 4-phase pipeline

## Alternatives Considered

1. **Keep refine loop, fix structured output.** Rejected — copilot nodes inherently return strings. Structured output would require a new node type or copilot protocol change (FR-TBD). The refine loop has never run in practice; removing it is pragmatic.

2. **Merge only critique+distill, keep precommit and submit separate.** Rejected — the inbox request explicitly asks for "pre-commit and PR in single step." Precommit→submit has no conditional branching and shares the same session; merging is safe.

3. **Merge all post-test nodes into one.** Rejected — critique+distill and finalize serve different purposes (evaluation vs. mechanical shipping). Keeping them separate preserves clear phase boundaries.

## Out of Scope

- Restoring the reflexion loop (FR-169 remains partially reversed; a future FR can re-introduce it with proper structured output)
- Changes to `scripts/enforce_worktree.sh` (already a thin wrapper that delegates to the graph)
- Changes to `implement` or `test_and_demo` nodes

## Related

- FR-106: Parallel Worktree Pipeline (foundation)
- FR-128: YAMLGraphication of Enforcer (created current 7-node graph)
- FR-169: Enforce Reflexion Loop (partially reversed by this FR — refine loop removed)
- FR-172: Configurable Loop Exit Target (no longer needed — no loops)
