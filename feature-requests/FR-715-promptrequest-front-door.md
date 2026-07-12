# Feature Request: FR-715 PromptRequest — One Object Through the Front Door

**Priority:** HIGH (highest knowledge-per-line refactor available; every new knob currently costs 3 edits)
**Type:** Enhancement (refactor — API-shape consolidation)
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-07-12
**Spawned by:** docs/2026-07-12-review-refactoring.md P2.1; jscpd (the codebase's only real clone: `executor.py` 38–80 vs 185–220, 172 tokens)
**Related:** FR-223 (`LLMNodeConfig` — the identical cure applied to llm_nodes, precedent and pattern), `executor.py`, `executor_base.py::prepare_messages` (C 14), `executor_async.py`

## Summary

`execute_prompt()`, `PromptExecutor.execute()`, and `prepare_messages()`
hand-thread the same ~12 keyword parameters. Replace the copied
signature with one frozen `PromptRequest` dataclass; the three functions
take the object.

## Value Statement

The prompt-execution signature is the framework's front door; today
every new parameter (max_tokens, thinking_budget were the last two) is
added in three places with three copied docstrings — the clone detector
flags it, and drift between the copies is a silent-default bug waiting
(a parameter accepted at one layer and dropped at the next).

## Problem

- 16-parameter public signature duplicated across `executor.py` (twice —
  module fn + method, the jscpd clone) and mirrored in
  `prepare_messages` / async paths.
- `prepare_messages` is C(14) partly from unpacking/re-validating the
  same arguments.
- Three docstrings describe the same contract; they already disagree in
  small ways (thinking_budget wording).

## Proposed Solution

- `PromptRequest` frozen dataclass in `executor_base.py`: prompt_name,
  variables, output_model, temperature, provider, model, graph_path,
  prompts_dir, prompts_relative, state, max_tokens, thinking_budget.
  Defaults live ONCE on the dataclass.
- `execute_prompt(**kwargs)` keeps its exact public signature as a thin
  constructor wrapper (it is the documented public API — README,
  examples, and prompts reference it); internally builds `PromptRequest`
  and delegates. `PromptExecutor.execute(request)` and
  `prepare_messages(request, ...)` take the object.
- Async path (`executor_async`) consumes the same object — one contract,
  both colors.
- FR-223 is the pattern: config resolver → frozen dataclass → phases.

## Deletion Ledger

| Deleted | Why |
|---|---|
| jscpd clone executor.py 38–80 / 185–220 | one signature, one docstring |
| duplicated kwarg-threading in prepare_messages callers | object passed whole |
| 2 of 3 copied docstrings | the dataclass is the doc |

## Acceptance Criteria

- [ ] AC-01 RED: witness that `execute_prompt` kwargs and
      `PromptExecutor.execute` accept identical parameter sets derived
      from ONE source (dataclass fields) — currently fails because the
      sets are maintained by hand
- [ ] AC-02 jscpd reports 0 clones in executor.py
- [ ] AC-03 Public API unchanged: existing `execute_prompt(...)` calls
      in examples/ and tests pass unmodified
- [ ] AC-04 `prepare_messages` CC drops below 10 or the remainder is
      confessed with cause
- [ ] AC-05 Net line delta ≤ 0 in yamlgraph/ (promotion test)
- [ ] Changelog fragment (REQ under CAP-04 prompt execution); diary

## Alternatives Considered

- `**kwargs` passthrough — rejected: deletes the clone but also deletes
  the contract; typos become runtime surprises (Commandment 5).
- Break the public signature to take the object — rejected: needless
  churn for every consumer; the wrapper is one function, not a shim
  (it IS the public API).
