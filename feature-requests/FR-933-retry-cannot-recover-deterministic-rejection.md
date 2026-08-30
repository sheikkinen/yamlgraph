# FR-933: Retry Cannot Recover a Deterministic Schema Rejection

**Priority:** HIGH
**Type:** Defect
**Status:** Proposed (not yet judged)
**Effort:** 0.5 day
**Requested:** 2026-08-30
**First consumer:** `scripts/research.sh` — the research sole route, currently
failing every run.
**Prior art:** `feature-requests/FR-896-research-route-precedent-traceability.md`
froze `max_length=400` with "rejection never truncation" and is the contract this
defect lives inside; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`
established the persona schema; `feature-requests/FR-926-research-route-error-surfacing.md`
built the error channel that made this diagnosable at all. None of the three
addresses retry semantics, so none is a duplicate.

## Summary

`on_error: retry` re-issues a byte-identical request. At `temperature: 0.0` a
schema validation failure is therefore retried into the same failure, and
`max_retries: 2` buys nothing but latency.

## Escalated from

FR-932 enforcement. Its AC-10 (a live `scripts/research.sh` run) could not be
satisfied: five consecutive runs failed, across two briefs and four distinct
persona/field combinations, every one on `String should have at most 400
characters`. A counterfactual run at pre-FR-932 code failed the same way, so the
route is red independently of that FR — but red is red, and it belongs to
whoever finds it.

## Traces

| run | brief | persona | field |
|---|---|---|---|
| 1 | fr-932-prior-art-precedent | os_infra_primitivist | rationale |
| 2 | fr-932-prior-art-precedent | os_infra_primitivist | rationale |
| 3 | fr-932-prior-art-precedent | os_infra_primitivist | rationale |
| 4 | fr-929-local-diary-existence | librarian_structure | rationale |
| 5 (pre-FR-932 code) | fr-929-local-diary-existence | yamlgraph_native_planner | candidate |

Run 5 is the counterfactual: `examples/demos/research-route/{graph.yaml,nodes/research_tools.py}`
checked out at `13feeeac`, which is the unmodified pre-FR-932 state.

## Violated objective

CAP-248 claims a working research sole route. The route currently cannot
complete, so the capability is a phantom claim.

## Root cause

`yamlgraph/node_factory/llm_execution.py`:

```python
if cfg.on_error == ErrorHandler.RETRY:
    nr = handle_retry(
        node_name,
        lambda: attempt_execute(cfg.provider),   # identical request
        cfg.max_retries,
    )
```

The retry closure captures no attempt index and varies no input. Retry is a
correct strategy for *transient* faults — timeouts, 429s, connection resets —
and a no-op for *deterministic* ones. A structured-output schema rejection at
temperature 0 is deterministic by construction. The graph declares
`on_error: retry, max_retries: 2` on all five persona nodes and receives three
identical failures.

The prompts are not the lever. Every field in
`examples/demos/research-route/prompts/*.yaml` already states "hard cap 400
characters; over-length output is rejected, never truncated", and there is a
`BREVITY IS MECHANICALLY ENFORCED` block. This is `two_strike_split` at its
fifth strike: the level is mechanizable, so it belongs in code.

## Proposed constraint

Retry must either vary the request or decline the job. Two candidate
mechanisms, to be settled at judgement:

1. **Feed the violation back.** On a `ValidationError`, append the pydantic
   message to the next attempt's input so the model is told which field
   overran and by how much. This keeps FR-896's rejection-never-truncation
   rule intact — the model repairs its own output; the framework never
   silently truncates.
2. **Classify before retrying.** Treat `ValidationError` as non-retryable and
   let it surface immediately, so `max_retries` stops buying latency it cannot
   convert into success.

(1) is preferred: it fixes the route, and it is the boundary reconciliation
`two_strike_split` prescribes — treat the model's output as a claim, reconcile
it against the schema, repair within a bounded number of attempts.

## Acceptance criteria (draft, for the Judge to sharpen)

- **AC-01** A unit test proves the current retry re-issues an identical
  request: a stub provider records its inputs, and today all attempts are equal.
- **AC-02** After the fix, a `ValidationError` retry carries the violated
  constraint into the next attempt, asserted on the recorded inputs.
- **AC-03** Transient-error retry behaviour is unchanged, witnessed by the
  existing retry tests.
- **AC-04** A live `scripts/research.sh` run completes and appends its
  provenance line — the evidence FR-932 AC-10 could not produce.

## Out of scope

Changing `max_length=400`; changing rejection-never-truncation; changing the
persona prompts; anything in the FR-932 frozen scope.
