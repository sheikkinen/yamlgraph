# Feature Request: FR-169 — Enforce Pipeline Reflexion Loop

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-03-09

## Summary

Insert a critique → refine reflexion loop between `test_and_demo` and `precommit_check` in the enforce pipeline, with automatic diary reflection distillation on loop exit.

## Value Statement

The enforce pipeline gains autonomous quality improvement, catching design and correctness issues before human review — reducing PR revision cycles and producing richer diary reflections.

## Problem

The enforce pipeline (`examples/enforce/graph.yaml`) is a linear four-phase chain:

```
implement → test_and_demo → precommit_check → submit_pr
```

Once tests pass in Phase 2, the pipeline proceeds directly to pre-commit and PR submission. There is no self-evaluation step that asks: "Does this implementation actually satisfy the FR's acceptance criteria? Is the code clean? Are there edge cases missed?"

This means:

1. **Quality issues survive to PR review** — the pipeline trusts green tests as sufficient proof of quality, but tests can pass while the implementation is suboptimal, incomplete, or misaligned with the FR's intent.
2. **Diary reflections are stubs** — `scripts/finalize_merge.sh` creates placeholder reflections (Trap/Heuristic/Seed sections) that must be filled manually. The enforce pipeline has the context to generate a meaningful first draft but discards it.
3. **The reflexion pattern already exists** — `examples/demos/reflexion/graph.yaml` demonstrates Draft → Critique → Refine with score-gated looping and `loop_exits`. The enforce pipeline should use this proven pattern.

## Proposed Solution

Insert a reflexion loop between `test_and_demo` and `precommit_check`. The loop uses copilot nodes that critique the implementation against the FR's acceptance criteria, then optionally refine. After the loop exits, a diary reflection draft is distilled from the critique findings.

### Prerequisite: loop_exits (resolved)

The original design identified that `_loop_limit_reached` in `routing.py` unconditionally returned `END`, which would skip post-loop nodes. This was resolved by FR-172 (Configurable loop exit target), which added `loop_exits` support to `make_expr_router_fn` and `edge_compiler.py`. FR-169 is **unblocked**.

### Graph changes (`examples/enforce/graph.yaml`)

#### New state fields

```yaml
state:
  # ... existing fields (fr_path, branch, implement_result, test_result, precommit_result, pr_result) ...
  critique_result: dict     # Critique output with score + feedback
  refine_result: dict       # Refinement output (separate from test_result)
  reflection_draft: dict    # Diary reflection content
```

#### New nodes

```yaml
nodes:
  # ... existing implement, test_and_demo ...

  # Phase 2b: Critique implementation against FR acceptance criteria
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
    timeout: 300

  # Phase 2c: Refine if critique score below threshold
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
    state_key: refine_result
    timeout: 300

  # Phase 2d: Distill diary reflection from critique context
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
    timeout: 300

  # ... existing precommit_check, submit_pr ...
```

#### Updated edges

```yaml
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

loop_exits:
  critique: distill_reflection
```

The `loop_exits` config ensures that when `critique` exhausts its 3-iteration limit, the router returns `distill_reflection` instead of `END`, preserving the post-loop pipeline stages.

#### State key separation (Issue 3 resolution)

`refine` writes to `refine_result`, NOT `test_result`. This preserves Phase 2 verification output. `submit_pr` can reference both `test_result` (original verification) and `refine_result` (refinement summary) for PR body context.

### New prompts (`examples/enforce/prompts/`)

**`enforce-critique.yaml`** — Evaluate implementation against FR acceptance criteria:
- Read the FR file and extract acceptance criteria
- Review every changed file (`git diff`)
- Check: tests cover all criteria, code is minimal, no dead code, patterns honored
- Output structured score (0.0–1.0) and specific feedback items

**`enforce-refine.yaml`** — Apply critique feedback:
- Address each feedback item from the critique
- Re-run affected tests
- Report what was changed and why

**`enforce-distill.yaml`** — Generate diary reflection draft:
- Identify the cognitive trap encountered (from Scripture's `traps:` vocabulary)
- Extract a heuristic
- Plant a Seed question
- Write to `docs/diary/YYYY-MM-DD-reflection-fr-NNN.md`

### Integration with finalize_merge.sh

`scripts/finalize_merge.sh` currently creates an empty reflection stub at `docs/diary/${DATE}-reflection-${FR_NUM}.md`. When a reflection file already exists at the expected path, skip stub creation — the pipeline already wrote a draft. The pre-commit hook (FR-144) still validates the content is non-placeholder.

### Timeout budget

All new nodes use 300s (5 min) timeout. Worst case:
- 3 × 300s (critique iterations) + 2 × 300s (refine iterations) + 300s (distill) = 1800s = **30 min**

This is bounded and predictable. 5 min per copilot execution is adequate for focused, scoped tasks (critique reads diff + FR; refine applies specific feedback; distill writes one diary file).

## Acceptance Criteria

- [ ] AC-1: `critique` copilot node added to enforce graph after `test_and_demo`
- [ ] AC-2: `refine` copilot node added with conditional edge from `critique` (score < 0.85)
- [ ] AC-3: `refine` writes to `refine_result` state key (does NOT overwrite `test_result`)
- [ ] AC-4: Reflexion loop limited to 2 refine iterations (`loop_limits: critique=3, refine=2`)
- [ ] AC-5: `loop_exits: { critique: distill_reflection }` configured (uses FR-172 mechanism)
- [ ] AC-6: `distill_reflection` copilot node writes diary reflection draft to `docs/diary/`
- [ ] AC-7: Reflection draft follows format: Context, Trap, Heuristic, Seed sections
- [ ] AC-8: `enforce-critique.yaml` prompt reads FR acceptance criteria and evaluates git diff
- [ ] AC-9: `enforce-refine.yaml` prompt addresses critique feedback and re-runs tests
- [ ] AC-10: `enforce-distill.yaml` prompt generates reflection from Scripture's trap vocabulary
- [ ] AC-11: `finalize_merge.sh` skips stub creation when reflection file already exists
- [ ] AC-12: Enforce graph still lints: `yamlgraph graph lint examples/enforce/graph.yaml`
- [ ] AC-13: Unit tests for new graph structure (edges, conditions, loop limits, loop_exits)
- [ ] AC-14: Integration test: mock copilot run through full reflexion loop
- [ ] AC-15: Total pipeline worst-case timeout increase ≤ 30 min (1800s)
- [ ] AC-16: Documentation updated in `examples/enforce/README.md`

## Alternatives Considered

### A. Post-merge reflexion only
Run critique after PR merges. **Rejected:** too late to improve the code; defeats the purpose of self-correction before review.

### B. LLM node instead of copilot node
Use `type: llm` for critique (cheaper, faster). **Rejected:** critique needs to read files, run tests, and inspect `git diff` — requires tool access that only copilot nodes provide.

### C. Single critique pass (no loop)
Critique once without a refine option. Considered viable as a simplification, but the reflexion pattern's value comes from iterative improvement. The loop limit (2 refines) keeps cost bounded.

### D. External reflexion graph
Separate `examples/enforce-reflexion/graph.yaml` called as a subgraph. **Rejected:** adds complexity; the reflexion nodes share session context with the main pipeline and benefit from session continuations (FR-105).

### E. Guard node instead of loop_exit
Add a passthrough node after critique that clears `_loop_limit_reached` and routes to `distill_reflection`. **Rejected:** the `_loop_limit_reached` flag causes the expression router to return `END` at critique's outgoing edges, so the guard node is never reached. Resolved by FR-172's `loop_exits` mechanism.

### F. Sentinel score on loop exit
Set `critique_result.score` to 0.0 when loop limit is hit. **Rejected:** the node returns `{"_loop_limit_reached": True}` before executing the prompt, so `critique_result` is never updated. Same root cause as (E).

## Scope Boundary

**In scope:**
- Three new copilot nodes (critique, refine, distill_reflection)
- Three new prompt YAML files
- Edge/loop_limits/loop_exits changes to enforce graph
- `finalize_merge.sh` skip-if-exists guard
- Unit and integration tests for new graph structure

**Out of scope:**
- Changes to `routing.py` or `edge_compiler.py` (handled by FR-172)
- Critique scoring calibration (initial threshold 0.85 is configurable via graph YAML)
- Prompt content tuning beyond first-draft correctness

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Reviewed:** 2026-03-09

**Findings:**

All 10 factual claims verified against the codebase:
- Enforce pipeline linear structure confirmed (`examples/enforce/graph.yaml`)
- FR-172 (`loop_exits`) is implemented and tested
- Reflexion demo at `examples/demos/reflexion/graph.yaml` uses identical pattern
- `finalize_merge.sh` creates diary stubs unconditionally (line 84: `cat >`)
- Copilot node type, `dict` state fields, `resume` cli_flag, and nested dict condition evaluation (`critique_result.score < 0.85`) all verified and covered by existing unit tests

**Single responsibility check:** The FR bundles the reflexion loop (quality improvement) with diary distillation (reflection generation). These are logically coupled — the distill node consumes critique output and shares session context via `resume`. Splitting would create unnecessary coordination overhead for a single post-loop node. Accepted as a single unit.

**No contradictions found.** AC-4 correctly describes loop limits (`critique: 3, refine: 2`). The worst-case timeout calculation (30 min) is arithmetically correct.

**One implementation note:** AC-11 (finalize_merge.sh skip guard) should use `if [ ! -f "$DIARY_ENTRY" ]; then ... fi` around the existing `cat >` block to avoid overwriting pipeline-generated reflections.

## Related

- **`examples/enforce/graph.yaml`** — Current enforce pipeline (FR-106, FR-128)
- **`examples/demos/reflexion/graph.yaml`** — Reflexion pattern reference implementation
- **`scripts/finalize_merge.sh`** — Post-merge finalization (FR-125)
- **`yamlgraph/routing.py`** — Expression router with `loop_exit_target` support
- **`yamlgraph/edge_compiler.py`** — Edge compilation with `loop_exits` forwarding
- **FR-105** — Copilot session continuations (threading context via `session_id`)
- **FR-128** — YAMLGraphication of enforcer (current architecture)
- **FR-144** — Diary reflection content enforcement (pre-commit gate)
- **FR-168** — Cross-graph session continuity
- **FR-172** — Loop exit target support (prerequisite, **implemented**)
- **Scripture** — `traps:` and `cures:` vocabulary for diary distillation
