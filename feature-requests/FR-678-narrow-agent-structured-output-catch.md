# Feature Request: Narrow bare exception catch in agent structured-output fallback

**Priority:** HIGH
**Type:** Bug
**Status:** Judged
**Effort:** 0.5 days
**Requested:** 2026-07-04

## Summary

The structured-output fallback in `yamlgraph/tools/agent.py` (~line 50)
catches bare `except Exception:` around the cheap JSON-parse attempt. This
swallows every failure class — including programming errors unrelated to
JSON parsing — and silently escalates to the expensive LLM re-invoke path,
discarding the original exception. Narrow the catch to the exceptions the
parse path can actually raise.

## Value Statement

Agent-node debugging sessions stop chasing ghosts: a genuine defect in
content normalization or model validation surfaces immediately instead of
being masked by (and billed as) an LLM retry.

## Problem

```python
# yamlgraph/tools/agent.py — structured output extraction (FR-448/FR-456)
try:
    parsed = extract_json(text)
    if isinstance(parsed, dict):
        return output_model.model_validate(parsed).model_dump()
except Exception:  # ← catches everything
    logger.debug("JSON parse failed for structured output, retrying with LLM")
```

Two failure modes:

1. **Masked defects.** A `TypeError` from a bad `output_model`, an
   `AttributeError` from a normalization bug, or any future regression in
   `extract_json` is logged at DEBUG (invisible by default) and converted
   into an LLM re-invoke. If the re-invoke then fails, the *original* error
   is gone — the reported failure is downstream of the real one. This is
   the `downstream_fix` trap materialized in error handling.
2. **Cost amplification.** Every swallowed non-parse error pays for an
   extra LLM round trip that cannot succeed if the defect is in our code.

Scripture, Commandment 6: "Thou shalt not hedge with silent fallbacks."
The fallback itself is legitimate (FR-448); the breadth of the catch is not.

## Proposed Solution

Catch only what the parse-and-validate path is specified to raise. Current
`extract_json()` catches `json.JSONDecodeError` internally and returns the
original string when no JSON is found, so the only expected exception from the
cheap successful-dict path is Pydantic validation failure:

```python
from pydantic import ValidationError

try:
    parsed = extract_json(text)
    if isinstance(parsed, dict):
        return output_model.model_validate(parsed).model_dump()
except ValidationError as parse_exc:
    # Schema mismatch in extracted JSON is a legitimate
    # "content wasn't parseable for this schema" signal that warrants fallback.
    logger.warning(
        "Structured output parse failed (%s), retrying with LLM",
        type(parse_exc).__name__,
    )
```

- Keep the no-JSON path explicit: if `extract_json(text)` returns a non-dict,
  the LLM fallback still triggers, but not via exception handling.
- Log at `warning` (not `debug`) when the fallback re-invoke is triggered,
  including the exception class name — the fallback costs money and should
  be observable (Commandment 9).

## Acceptance Criteria

- [ ] RED: test where `output_model.model_validate` raises `TypeError`
  (simulated defect) — asserts the exception propagates instead of
  triggering the LLM fallback
- [ ] Test: malformed JSON content still falls back to LLM re-invoke
  because `extract_json()` returns non-dict content (existing behavior
  preserved without exception swallowing)
- [ ] Test: `ValidationError` on schema mismatch falls back to LLM re-invoke
- [ ] Test: `ValueError` raised by a mocked `extract_json()` propagates; it is
  not treated as a normal JSON parse miss unless the real callee contract
  changes
- [ ] Fallback trigger logged at `warning` with exception class name
- [ ] Grep confirms no other bare `except Exception:` immediately preceding
  an LLM re-invoke remains in `yamlgraph/tools/`
- [ ] Tests tagged `@pytest.mark.req(...)` (existing agent/structured-output
  REQ; no new capability)
- [ ] Changelog fragment in `changelog/unreleased/` (type: fix)

## Alternatives Considered

1. **Keep broad catch, log at error level** — rejected: still converts
   programming errors into paid LLM calls; observability without
   enforcement.
2. **Re-raise original exception if the LLM fallback also fails** (exception
   chaining) — good, but secondary; narrowing the catch makes most of the
   masked cases impossible, which is cheaper. Chaining can ride along if
   trivial (`raise ... from parse_exc`).

## Related

- FR-448 — structured output fallback (introduced this path)
- FR-456 — lenient construction on response_format rejection
- FR-676 — the same parse-fallback pattern exists in
  `utils/llm_factory_async.py` and `executor.py`; FR-679 consolidates those
  copies — apply the narrowed tuple in the shared helper there
- Scripture: Commandment 6 (no silent fallbacks), `plausible_wrong_answer`

## Judgement

**APPROVED WITH REQUIRED AMENDMENTS FOLDED IN.** The defect is real:
`_try_structured_output()` currently catches `Exception` around
`extract_json()` plus `output_model.model_validate()`, logs only at debug, and
then pays for a structured LLM re-invoke. That can mask programming defects in
the parser/model path and make the reported failure downstream of the cause.

The original proposed tuple was too broad. `extract_json()` does not expose
`json.JSONDecodeError`/`ValueError` as part of its normal contract; it returns
the original string when it cannot extract JSON. Therefore the approved fix is
to catch `pydantic.ValidationError` for schema mismatch only, let `TypeError`,
`AttributeError`, and mocked `ValueError` defects propagate, and keep the
non-dict parse result as the explicit trigger for fallback.

**Verdict:** Approved. This is a narrow bug fix and should land before or with
FR-679 so the shared fallback helper inherits the corrected exception boundary.
