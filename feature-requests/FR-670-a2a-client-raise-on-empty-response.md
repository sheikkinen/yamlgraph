# Feature Request: Raise on empty A2A response instead of returning empty string

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged
**Effort:** 0.5 days
**Requested:** 2026-07-03

## Summary

`_extract_text_from_result` in the A2A client returns `""` when the task
result contains no text parts in either artifacts or status message. Silent
empty-string fallback violates Commandment 6: when a filter yields nothing,
raise — never substitute.

## Value Statement

Graph authors calling remote A2A agents get an immediate, explicit error on
malformed or empty responses instead of an empty string silently flowing
into downstream state and prompts.

## Problem

`yamlgraph/contrib/a2a_client.py:49-67`:

```python
    return "\n".join(texts) if texts else ""
```

If neither artifacts nor the status message contain text parts, the caller
receives `""`. Downstream, this empty string enters graph state, renders
into Jinja2 prompts as nothing, and produces plausible-but-wrong LLM output
(`plausible_wrong_answer` trap). The caller cannot distinguish "agent
returned empty" from "response shape unrecognized".

## Proposed Solution

```python
    if not texts:
        raise ValueError(
            f"A2A response contains no text parts "
            f"(task state: {result.get('status', {}).get('state', 'unknown')})"
        )
    return "\n".join(texts)
```

The existing `send_a2a_message` error handling (PipelineError path) will
surface this like any other node failure — no new machinery.

## Acceptance Criteria

- [ ] Failing test first (RED): result dict with no text parts in artifacts
      or status message → `ValueError` raised, message includes task state
- [ ] Existing tests with valid artifacts/status-message paths still green
- [ ] Error propagates through `send_a2a_message` as `PipelineError`
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

- **Return `None` and let caller decide** — rejected: pushes the check
  downstream of the boundary; every caller must remember to handle it.
- **Log a warning and return `""`** — rejected: still a silent fallback;
  logs are not a contract.

## Related

- docs/2026-07-03-review-fable.md (Issue 3)
- yamlgraph/contrib/a2a_client.py:49-67
- Scripture Commandment 6

## Judgement

**APPROVED.** `return "\n".join(texts) if texts else ""` in
`a2a_client.py` is confirmed. Silent empty-string return violates
Commandment 6. Fix is small and correctly scoped. No amendments.
