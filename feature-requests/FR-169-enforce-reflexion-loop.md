# Feature Request: FR-169 Enforce Pipeline Reflexion Loop

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-03-09
**Prerequisite:** FR-170 (loop_exit target support — see Issue 1 resolution)

## Summary

Add a reflexion (critique → refine) loop after the test-and-demo phase of the enforce pipeline so the implementation is self-evaluated and improved before pre-commit checks and PR submission. On completion, distill a diary reflection automatically.

## Value Statement

The enforce pipeline gains autonomous quality improvement, catching design and correctness issues before human review — reducing PR revision cycles and producing richer diary reflections.

## Problem

The current enforce pipeline (`examples/enforce/graph.yaml`) is a linear four-phase chain:

```
implement → test_and_demo → precommit_check → submit_pr
```

Once tests pass in Phase 2, the pipeline proceeds directly to pre-commit and PR submission. There is no self-evaluation step that asks: "Does this implementation actually satisfy the FR's acceptance criteria? Is the code clean? Are there edge cases missed?"

This means:
1. **Quality issues survive to PR review** — the pipeline trusts green tests as sufficient proof of quality, but tests can pass while the implementation is suboptimal, incomplete, or misaligned with the FR's intent.
2. **Diary reflections are stubs** — `finalize_merge.sh` creates placeholder reflections that must be filled manually. The enforce pipeline has the context to generate a meaningful first draft but discards it.
3. **The reflexion pattern already exists** — `examples/demos/reflexion/` demonstrates Draft → Critique → Refine with score-gated looping. The enforce pipeline should use this proven pattern.

## Proposed Solution

Insert a reflexion loop between `test_and_demo` and `precommit_check`. The loop is a copilot node that critiques the implementation against the FR's acceptance criteria, then optionally refines. After the loop exits, a diary reflection draft is distilled from the critique findings.

### Amendments from Judgement (2026-03-09)

Three issues were raised and resolved:

**Issue 1 (Loop limit exit route):** The `_loop_limit_reached` mechanism in `routing.py` unconditionally returns `END`, which would skip `distill_reflection`, `precommit_check`, and `submit_pr`. **Resolution: Option (a)** — File prerequisite FR-170 to extend `make_expr_router_fn` with a configurable `loop_exit` target per node. The graph config gains a `loop_exits` section:

```yaml
loop_exits:
  critique: distill_reflection
```

When critique hits its loop limit, the router returns `distill_reflection` instead of `END`. This is a ~15-line change in `routing.py` and `edge_compiler.py`. FR-169 is blocked on FR-170.

**Issue 2 (Timeout budget):** Original worst case was 65 min; AC stated ≤ 30 min. **Resolution:** Reduce all node timeouts to 300s (5 min). Worst case: 3×300 (critique) + 2×300 (refine) + 300 (distill) = 1800s = **30 min exactly**. 5 min per copilot execution is adequate for focused, scoped tasks (critique reads diff + FR; refine applies specific feedback; distill writes one diary file).

**Issue 3 (Refine overwrites test_result):** **Resolution: Option (b)** — Use separate key `refine_result` for the refine node. `test_result` (Phase 2 output) is preserved. `submit_pr` can reference both `test_result` (original verification) and `refine_result` (refinement summary) for PR body context.

### Graph changes (`examples/enforce/graph.yaml`)

```yaml
state:
  # ... existing fields ...
  critique_result: dict     # NEW: Critique output with score + feedback
  refine_result: dict       # NEW: Refinement output (separate from test_result)
  reflection_draft: dict    # NEW: Diary reflection content

nodes:
  # ... existing implement, test_and_demo ...

  # NEW Phase 2b: Critique implementation against FR acceptance criteria
  critique:
    type: copilot
    prompt: enforce-critique
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    variables:
      fr_path: "{state.fr_path}"
    state_key: critique_result
    timeout: 300  # 5 min per iteration

  # NEW Phase 2c: Refine if critique score below threshold
  refine:
    type: copilot
    prompt: enforce-refine
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    variables:
      fr_path: "{state.fr_path}"
      feedback: "{state.critique_result.feedback}"
    state_key: refine_result  # Separate key — does NOT overwrite test_result
    timeout: 300  # 5 min per iteration

  # NEW Phase 2d: Distill diary reflection from critique context
  distill_reflection:
    type: copilot
    prompt: enforce-distill
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    variables:
      fr_path: "{state.fr_path}"
    state_key: reflection_draft
    timeout: 300  # 5 min

  # ... existing precommit_check, submit_pr ...

edges:
  - from: START
    to: implement
  - from: implement
    to: test_and_demo
  - from: test_and_demo
    to: critique

  # Reflexion loop: critique → refine → critique (max 2 refine iterations)
  - from: critique
    to: refine
    condition: critique_result.score < 0.85
  - from: refine
    to: critique

  # Exit loop when quality threshold met
  - from: critique
    to: distill_reflection
    condition: critique_result.score >= 0.85

  - from: distill_reflection
    to: precommit_check
  - from: precommit_check
    to: submit_pr
  - from: submit_pr
    to: END

loop_limits:
  critique: 3
  refine: 2

# NEW: Custom exit targets when loop limits hit (requires FR-170)
loop_exits:
  critique: distill_reflection
```

### New prompts (`examples/enforce/prompts/`)

**`enforce-critique.yaml`** — Evaluate implementation against FR acceptance criteria:
- Read the FR file and extract acceptance criteria
- Review every changed file (git diff)
- Check: tests cover all criteria, code is minimal, no dead code, patterns honored
- Output structured score (0.0–1.0) and specific feedback items

**`enforce-refine.yaml`** — Apply critique feedback:
- Address each feedback item from the critique
- Re-run affected tests
- Report what was changed and why (stored in `refine_result`, not `test_result`)

**`enforce-distill.yaml`** — Generate diary reflection draft:
- Identify the cognitive trap encountered (from Scripture's `traps:` list)
- Extract a heuristic
- Plant a Seed question
- Write to `docs/diary/YYYY-MM-DD-reflection-fr-NNN.md` as a draft (not a stub)

### Integration with finalize_merge.sh

`scripts/finalize_merge.sh` currently creates an empty reflection stub. When a reflection file already exists at the expected path (`docs/diary/${DATE}-reflection-${FR_NUM}.md`), skip stub creation — the pipeline already wrote a draft. The pre-commit hook (FR-144) still validates the content is non-placeholder.

## Acceptance Criteria

- [ ] `critique` node added to enforce graph after `test_and_demo`
- [ ] `refine` node added with conditional edge from `critique` (score < 0.85)
- [ ] `refine` writes to `refine_result` state key (does NOT overwrite `test_result`)
- [ ] Reflexion loop limited to 2 refine iterations (loop_limit: critique=3, refine=2)
- [ ] `loop_exits: { critique: distill_reflection }` configured (requires FR-170)
- [ ] `distill_reflection` node writes diary reflection draft to `docs/diary/`
- [ ] Reflection draft follows existing format: Context, Trap, Heuristic, Seed sections
- [ ] `enforce-critique.yaml` prompt reads FR acceptance criteria and evaluates git diff
- [ ] `enforce-refine.yaml` prompt addresses critique feedback and re-runs tests
- [ ] `enforce-distill.yaml` prompt generates reflection from Scripture's trap vocabulary
- [ ] `finalize_merge.sh` skips stub creation when reflection file already exists
- [ ] Enforce pipeline graph still lints: `yamlgraph graph lint examples/enforce/graph.yaml`
- [ ] Unit tests for new graph structure (edges, conditions, loop limits)
- [ ] Integration test: mock copilot run through full reflexion loop
- [ ] Total pipeline worst-case timeout increase ≤ 30 min (3×300 + 2×300 + 300 = 1800s)
- [ ] Documentation updated in `examples/enforce/README.md`

## Alternatives Considered

1. **Post-merge reflexion only** — Run critique after PR merges. Rejected: too late to improve the code; defeats the purpose of self-correction before review.

2. **LLM node instead of copilot node** — Use `type: llm` for critique (cheaper, faster). Rejected: critique needs to read files, run tests, and inspect git diff — requires tool access that only copilot nodes provide.

3. **Single critique pass (no loop)** — Critique once without refine option. Considered viable as a Phase 1 simplification, but the reflexion pattern's value comes from iterative improvement. The loop limit (2 refines) keeps cost bounded.

4. **External reflexion graph** — Separate `examples/enforce-reflexion/graph.yaml` called as a subgraph. Rejected: adds complexity; the reflexion nodes share session context with the main pipeline and benefit from session continuations (FR-105).

5. **Guard node instead of loop_exit** (Judgement Issue 1, Option b) — Add a passthrough node after critique that clears `_loop_limit_reached` and routes to `distill_reflection`. Rejected: the `_loop_limit_reached` flag causes the expression router to return `END` at critique's outgoing edges, so the guard node is never reached. The framework must support custom exit targets.

6. **Sentinel score on loop exit** (Judgement Issue 1, Option c) — Set `critique_result.score` to 0.0 when loop limit hit. Rejected: the node returns `{"_loop_limit_reached": True}` before executing the prompt, so `critique_result` is never updated. The expression router returns `END` before evaluating score conditions. Same root cause as option (b).

## Related

- `examples/enforce/graph.yaml` — Current enforce pipeline (FR-106, FR-128)
- `examples/demos/reflexion/graph.yaml` — Reflexion pattern reference implementation
- `scripts/finalize_merge.sh` — Post-merge finalization (FR-125)
- `yamlgraph/routing.py` — Expression router with `_loop_limit_reached` → END logic
- `yamlgraph/edge_compiler.py` — Edge compilation (needs `loop_exits` support)
- FR-105: Copilot session continuations (threading context)
- FR-128: YAMLGraphication of enforcer (current architecture)
- FR-144: Diary reflection content enforcement (pre-commit gate)
- FR-168: Cross-graph session continuity (potential prerequisite for session ID threading)
- **FR-170 (prerequisite):** Loop exit target support — extend expression router to accept configurable exit targets instead of hardcoded `END`
- Scripture: `traps:` and `cures:` vocabulary for diary distillation
