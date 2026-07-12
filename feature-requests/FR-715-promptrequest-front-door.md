# Feature Request: FR-715 PromptRequest — One Object Through the Front Door

**Priority:** HIGH (highest knowledge-per-line refactor available; every new knob currently costs 3 edits)
**Type:** Enhancement (refactor — API-shape consolidation)
**Status:** Judged (2026-07-12) — scope frozen NARROWER than proposed (F1: prepare_messages descoped); authority granted
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

- [ ] AC-01 RED: `inspect.signature(execute_prompt)` parameter names ==
      `PromptRequest` field names, derived from ONE source — fails today
      (no PromptRequest); keeps failing if either side drifts (F3)
- [ ] AC-02 jscpd reports 0 clones in executor.py
- [ ] AC-03 Public API unchanged: existing `execute_prompt(...)` calls
      in examples/ and tests pass unmodified
- [ ] AC-04 (deleted by Judgement F1 — prepare_messages out of scope)
- [ ] AC-05 Net line delta ≤ 0 in yamlgraph/ (promotion test);
      `prepare_messages_async` deleted if F2 verification allows
- [ ] Changelog fragment (REQ under CAP-04 prompt execution); diary

## Judgement (2026-07-12)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | The FR claimed prepare_messages "threads the same ~12 kwargs" — FALSE: it threads 8, is already C901-confessed, and has 5 callers including race_node/router_race. Changing its signature drags the race paths into a clone-kill that lives entirely in executor.py | **Descoped.** `prepare_messages` keeps its kwargs signature untouched. PromptRequest covers `execute_prompt` → `PromptExecutor.execute` (+ the executor_async mirror). AC-04 (prepare_messages CC) DELETED — out of scope |
| F2 | `prepare_messages_async` (executor_base.py:296) is a pure delegation shim — duplicates the 8-param signature and calls the sync version | Purge candidate IN scope (Commandment 8): verify callers at enforce time; if all callers can call `prepare_messages` directly, delete it in this FR's PR with a witness |
| F3 | AC-01's RED is vacuous as written (fails on ImportError, not on the claim) | Amended: RED = assert `inspect.signature(execute_prompt)` parameter names == `PromptRequest` dataclass field names, single source — fails today because PromptRequest does not exist AND stays failing if a field is added to one side only |

AC list amended per F1/F3: AC-04 deleted; AC-01 rewritten. Sequence:
this FR lands before FR-716 (both touch executor_async; smaller first).

## Alternatives Considered

- `**kwargs` passthrough — rejected: deletes the clone but also deletes
  the contract; typos become runtime surprises (Commandment 5).
- Break the public signature to take the object — rejected: needless
  churn for every consumer; the wrapper is one function, not a shim
  (it IS the public API).
