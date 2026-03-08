# Feature Request: Judge SPLIT Verdict for Complex Feature Requests

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-08

## Summary

Add a fourth verdict — **SPLIT** — to the chaplain judge prompt, enabling it to decompose multi-concern feature requests into separate, focused FRs that each receive independent judgement.

## Value Statement

Chaplain pipeline operators get higher approval rates and faster enforcement cycles because each FR addresses a single responsibility, reducing scope creep and ambiguous acceptance criteria.

## Problem

The current judge prompt offers three verdicts: APPROVE, AMEND, and REJECT. When a feature request bundles multiple orthogonal concerns (e.g., a new node type *and* a CLI flag *and* a lint rule), the judge must either:

1. **APPROVE** a bloated FR — enforcement becomes complex, partial failures are hard to attribute, and PR scope explodes.
2. **AMEND** with "please split this" — but the planner receives generic feedback without structured guidance on *how* to split, leading to amend cycles that waste judge invocations.
3. **REJECT** — overly harsh for an FR whose individual parts may be valid.

Evidence from the codebase:
- FR-044 (Shared Contrib Libraries) spawned FR-044a, FR-044b, FR-044c, FR-044d as ad-hoc splits — no structured mechanism existed.
- The enforce pipeline (`examples/enforce/graph.yaml`) assumes one FR → one PR. Multi-concern FRs produce oversized PRs that are harder to review and merge.

## Proposed Solution

### 1. Add SPLIT verdict to both judge prompts

In `examples/copilot/prompts/judge.yaml` and `scripts/chaplain-prompts/judge.md`, add a fourth verdict:

```
**SPLIT:** If the FR addresses multiple orthogonal concerns.
- Identify each independent concern as a numbered sub-topic
- Write each sub-topic as a separate file in .chaplain/inbox/ (one sentence per file)
- Delete the original draft from .chaplain/drafts/
- Each sub-topic re-enters the Plan → Judge pipeline independently
```

### 2. Add scope-count criterion to evaluation

Add an eighth evaluation criterion to `scripts/chaplain-prompts/judge.md`:

```
8. **Scope Count** — Count the distinct responsibilities in the FR. If more than one
   independent concern is present (can be implemented and tested separately), verdict
   is SPLIT. A phased FR with dependent phases is acceptable; orthogonal concerns are not.
```

And add to `examples/copilot/prompts/judge.yaml` criterion list:

```
6. Does the FR address a single responsibility, or does it bundle orthogonal concerns?
```

### 3. Watch loop handles SPLIT naturally

No changes to `.chaplain/watch.sh` are needed. The SPLIT verdict writes new topic files to `.chaplain/inbox/`, which the existing polling loop picks up on the next iteration. The original draft is deleted, so no duplicate processing occurs.

## Acceptance Criteria

- [ ] `examples/copilot/prompts/judge.yaml` includes SPLIT verdict with instructions to write sub-topics to `.chaplain/inbox/` and delete the original draft
- [ ] `scripts/chaplain-prompts/judge.md` includes SPLIT verdict and the "Scope Count" criterion (criterion 8)
- [ ] SPLIT verdict documentation specifies: identify concerns, write one-sentence topic per concern to inbox, delete draft
- [ ] Existing APPROVE/AMEND/REJECT behavior is unchanged (no regressions in prompt semantics)
- [ ] `.chaplain/watch.sh` requires no code changes (SPLIT output is consumed by existing inbox polling)
- [ ] Tests: add a smoke-test topic file in `tests/` fixtures that bundles two orthogonal concerns, verifiable by manual judge invocation
- [ ] Documentation: update `feature-requests/README.md` if it describes the verdict set

## Alternatives Considered

1. **AMEND with splitting guidance** — Current approach. Relies on the planner to interpret "split this" correctly, often requiring multiple amend cycles. More expensive and less deterministic than a structured SPLIT verdict.

2. **Automatic decomposition in the plan node** — The planner could pre-split topics before drafting. Rejected because: (a) the planner lacks the adversarial perspective needed to identify orthogonal concerns, and (b) splitting is a judgement call, not a planning activity.

3. **Post-approval splitting in enforce** — Split during implementation. Rejected because it defeats the purpose: the enforce pipeline assumes a single, judged FR per worktree.

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Evaluated 2026-03-08 by Chaplain Judge.**

**Strengths:**
1. **Genuinely minimal scope.** Two prompt files modified, zero code changes. The copilot node's existing `--allow-all-tools` capability handles file I/O (write to inbox, delete draft) during execution — no graph edge changes or watch.sh modifications required.
2. **Architecturally consistent.** SPLIT follows the same pattern as APPROVE/AMEND/REJECT: all side effects occur inside the copilot node execution, downstream nodes (summarize, diary) just capture what happened. The linear graph flow (plan → judge → summarize → write_diary) needs no conditional routing additions.
3. **Real problem with evidence.** Multi-concern FRs cause oversized PRs and amend cycles. The enforce pipeline's one-FR-one-PR assumption is well-documented.
4. **Clean separation.** SPLIT is a judgement call (not planning), correctly placed in the judge stage. Alternative 2 (planner pre-splitting) was rightly rejected.

**Noted weaknesses (non-blocking):**
1. **Test criterion says "manual judge invocation"** — acceptable for a prompt-only change since LLM output is non-deterministic. The fixture file serves as documentation and integration test material.
2. **FR-044 evidence unverifiable** — no FR-044 files found in feature-requests/. May have been archived. The problem statement stands on its own merits regardless.
3. **"Scope Count" criterion relies on LLM judgment** to distinguish "independent" from "dependent" concerns. The clarification ("can be implemented and tested separately" / "phased FR with dependent phases is acceptable") is sufficient guidance.

**Scope boundary (frozen):**
- IN: Prompt text changes to `examples/copilot/prompts/judge.yaml` and `scripts/chaplain-prompts/judge.md`
- IN: Test fixture file in `tests/`
- IN: `feature-requests/README.md` update if it enumerates verdicts
- OUT: No graph.yaml edge changes, no watch.sh changes, no Python code changes

## Related

- `examples/copilot/prompts/judge.yaml` — Primary judge prompt (copilot node)
- `scripts/chaplain-prompts/judge.md` — Legacy judge prompt (7-point evaluation)
- `examples/copilot/graph.yaml` — Plan → Judge → Summarize → Diary pipeline
- `.chaplain/watch.sh` — Inbox polling loop
- FR-044 series — Historical example of ad-hoc splitting
- FR-055 — Autonomous Chaplain (established Plan → Judge flow)
- FR-068 / FR-084 — Chaplain watch loop (inbox → pipeline)
