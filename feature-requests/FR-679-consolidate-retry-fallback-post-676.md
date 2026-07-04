# Feature Request: Consolidate retry/fallback policy duplicated by FR-676

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged
**Effort:** 1 day
**Requested:** 2026-07-04

## Summary

FR-676 achieved sync/async retry parity by **copying** the retry loop,
exponential backoff, and FR-464 structured-output fallback from
`executor.py::PromptExecutor._invoke_with_retry` into
`utils/llm_factory_async.py::invoke_async`. Parity by duplication is
parity with an expiry date. Extract the shared attempt policy into
`executor_base.py` so both paths consume one implementation.

## Value Statement

The next retry-policy change (backoff tuning, new retryable error class,
fallback prompt wording) lands in exactly one place and cannot silently
diverge between sync graph runs and async/streaming runs.

## Problem

**Note on FR-672:** that FR proposed this extraction on 2026-07-03 and was
correctly REJECTED — at that time `executor_async.py` had no retry logic and
the duplication did not exist. The rejection predates FR-676's enforcement,
which *created* the duplication this FR now removes. New evidence:

| Concern | Sync | Async |
|---|---|---|
| Retry loop + attempt counting | `executor.py::_invoke_with_retry` (~157–216) | `llm_factory_async.py::invoke_async` (~76–145) |
| `is_retryable()` + last-attempt check | executor.py ~207 | llm_factory_async.py ~137 |
| Exponential backoff | `time.sleep(delay)` ~216 | `await asyncio.sleep(delay)` ~145 |
| FR-464 fallback: schema hint + re-invoke + `extract_json` | executor.py ~186–192 | llm_factory_async.py ~114–120 |

The fallback block is near-verbatim in both files, down to the
`retry_msgs = list(messages) + [HumanMessage(content=schema_hint)]`
construction. `executor_base.py` already exists for exactly this sharing
(`is_retryable`, `build_schema_hint`, `prepare_messages` live there).

Additional dead weight in the same files:
- `executor.py::_build_schema_hint` (~line 40) is a deprecated zero-caller
  wrapper around `executor_base.build_schema_hint` — delete it in this FR
  (it exists only to be one more thing that can drift).

## Proposed Solution

Extract the single-attempt-with-fallback into a sync helper in
`executor_base.py`; keep the loop/sleep in each caller (the only genuinely
divergent parts are `time.sleep` vs `await asyncio.sleep`):

```python
# executor_base.py
def attempt_structured_invoke(llm, messages, output_model):
    """One invocation attempt with FR-464 structured-output fallback.

    Raises on retryable errors — the caller owns the retry loop and
    backoff (sync: time.sleep, async: asyncio.sleep).
    """
    ...
```

- `executor.py::_invoke_with_retry` becomes: loop + backoff +
  `attempt_structured_invoke`.
- `llm_factory_async.py::invoke_async` becomes: loop + async backoff +
  `attempt_structured_invoke` (the inner invoke is already sync per FR-676's
  design — LangChain `llm.invoke` inside async wrapper).
- Delete `executor.py::_build_schema_hint`.
- Import-linter: `utils/llm_factory_async` already imports
  `executor_base.build_schema_hint` and `is_retryable`, but helper placement is
  still a boundary decision. Verify with `lint-imports` during RED phase; if
  `executor_base` is judged Layer-2-only, house the helper in a Layer-3-safe
  shared module and update this FR with the decision.

## Constraints

- Behavior-preserving refactor: no changes to retry counts, backoff timing,
  delay jitter, or fallback prompt content.
- Existing FR-676 parity tests must pass unmodified — they are the
  regression suite proving the consolidation preserved semantics.
- If FR-678 (narrowed exception catch) lands first, the shared helper
  adopts its narrowed tuple. If this lands first, include FR-678's narrowed
  exception behavior in the extracted helper so the consolidation does not
  preserve an overbroad catch.

## Acceptance Criteria

- [ ] `attempt_structured_invoke` (or equivalently named) exists in exactly
  one module; sync and async paths both call it
- [ ] Fallback logic (`build_schema_hint` + re-invoke + `extract_json`)
  appears exactly once in the codebase — grep proves no second copy
- [ ] Shared fallback helper catches only the FR-678-approved exception class
  for parse/schema mismatch; broad `except Exception` does not wrap JSON
  extraction and model validation
- [ ] All existing FR-676 parity tests pass unmodified
- [ ] `executor.py::_build_schema_hint` deleted; grep shows zero references
- [ ] `lint-imports` passes (layer contract kept)
- [ ] Changelog fragment in `changelog/unreleased/` (type: refactor → use
  `fix` or omit gate per fragment rules; no behavior change)

## Alternatives Considered

1. **Full async-native retry loop shared via `asyncio.to_thread`** —
   rejected: over-engineering; the loop bodies differ only in the sleep
   primitive, and the sync-first convention keeps the invoke sync.
2. **Leave as-is, rely on parity tests** — rejected: tests prove today's
   parity, not tomorrow's; the `partial_remediation` trap says fix all
   occurrences while the duplication is fresh.
3. **Extract the whole loop including backoff** (single function with a
   `sleeper` callable) — considered; adds indirection for ~6 lines of loop.
   Judge may upgrade to this if the helper boundary feels arbitrary.

## Related

- FR-672 — prior proposal, rejected on then-correct grounds (duplication
  did not exist yet); this FR supersedes it with post-FR-676 evidence
- FR-676 — created the duplication while fixing parity (explicitly deferred
  extraction as out-of-scope)
- FR-464 — the structured-output fallback being consolidated
- FR-678 — narrows the exception tuple this helper will contain
- Scripture: `partial_remediation`, Commandment 8 (kill entropy)

## Judgement

**APPROVED WITH REQUIRED AMENDMENTS FOLDED IN.** The post-FR-676 duplication is
real: `PromptExecutor._invoke_with_retry()` and `utils.llm_factory_async.invoke_async()`
now both contain the same response-format fallback shape: `with_structured_output`,
schema hint, re-invoke, `normalize_content`, `extract_json`, and model validation.
`executor.py::_build_schema_hint` is also a zero-caller wrapper around
`executor_base.build_schema_hint` and should be deleted in the same refactor.

The refactor must not turn a behavior-preserving consolidation into a layer
violation. `llm_factory_async` already imports `executor_base`, so the proposed
location is plausible, but `lint-imports` remains the deciding check. The shared
helper must also absorb FR-678's narrowed exception boundary; otherwise this FR
would centralize a bug instead of removing it.

**Verdict:** Approved. Land after FR-678 if possible; if ordering is reversed,
include the FR-678 exception-boundary tests in this FR.
