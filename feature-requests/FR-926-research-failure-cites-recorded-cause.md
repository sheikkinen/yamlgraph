# Feature Request: Research Route Failure Must Cite the Recorded Cause

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-08-30
**First consumer / first event:** the next agent whose research run fails a persona node — at the moment it reads the CLI failure output to decide what to fix
**Research:** [FR-926.research.md](FR-926.research.md) (brief: `research-briefs/fr-926-error-surfacing-problem-brief.md`, run 2026-08-30, 5 personas, unanimous pursue, 4/5 convergent on boundary-enforcement at the gather step)
**Prior art:** FR-925 is the sibling incident (same session) — its diagnosis paid the cost this FR removes; distinguished: FR-925 fixes hook delivery, this fixes pipeline failure diagnostics. CAP-08 (error handling) defines the error-channel contract this FR reads, not changes.

## Summary

When a persona node exhausts retries, `gather_findings` fails the run
with only `missing persona findings: <key>` while the recorded cause —
node, exception type, full validation message — sits in
`state["errors"]` one key away. Surface the recorded errors in the
raise message so diagnosis is possible from the run's own output.

## Value Statement

Turns a multi-step tracing-backend investigation into a one-read
diagnosis for every future research-route failure (Commandment 6: bear
witness of thy errors).

## Problem

Witnessed 2026-08-30, three consecutive runs of the FR-925 brief:

- CLI and log said only `missing persona findings:
  yamlgraph_native_finding`.
- The actual cause — `ValidationError: rationale … string_too_long`,
  retried and re-failed identically — was recorded in
  `state["errors"]` by the framework's retry handler each time, and
  appeared nowhere in the failure output.
- Root-cause recovery required a throwaway LangSmith drill script
  traversing 47 child runs to read information the graph possessed at
  raise time.

A failure record that exists but is never surfaced is equivalent to no
record at the moment of diagnosis.

## Proposed Solution

Research convergence (4/5 on boundary-enforcement at the gather step;
the librarian's error_handler-node rewiring dispositioned below): read
the adjacent error channel and enrich the existing raise —

```python
def gather_findings(state):
    missing = [key for key in PERSONA_KEYS if key not in state]
    if missing:
        recorded = [
            e for e in (state.get("errors") or [])
            if isinstance(e, dict)
        ]
        detail = "".join(
            f"\n  {e.get('node')}: {e.get('type')}: {e.get('message')}"
            for e in recorded
        )
        raise ValueError(
            f"missing persona findings: {', '.join(missing)}"
            + (f"\nrecorded node errors:{detail}" if detail else "")
        )
    ...
```

Scope boundaries (from the brief's constraints, all frozen):

- Schema hard caps (reject, never truncate) unchanged.
- Retry semantics and the error-channel state shape unchanged — this
  reads the contract, it does not alter it.
- The run remains a hard failure; no partial artifact.

## Acceptance Criteria

- [ ] AC-01: a research run whose persona node exhausts retries fails
      with a message containing both the missing state key AND the
      recorded node, exception type, and validation message from
      `state["errors"]` — asserted by a unit test feeding a state with
      a missing key and a populated error channel.
- [ ] AC-02: with an empty/absent error channel, the message is
      unchanged from today (symptom only) — no invented detail.
- [ ] AC-03: existing research-route tests pass unmodified; no change
      to graph topology, schema caps, or retry config.
- [ ] AC-04: the enriched message reaches the operator-facing surface
      (visible in `research.sh` failure output), not only the raise.
- [ ] Changelog fragment in `changelog/unreleased/`.
- [ ] Diary entry.

## Alternatives Considered

Dispositioned in [FR-926.research.md](FR-926.research.md):

- **Enrich the raise at the gather boundary** (os-infra, data-process,
  native-planner, subtractionist — convergent ×4): chosen; the record
  exists, only witness is missing; single-point read-and-emit.
- **LangGraph error_handler node rewiring** (librarian): structurally
  correct but medium-effort topology change for information already
  present in state; rejected as over-machinery for a visibility defect
  (`callsite_fix` — fix at the specific consumer, not the framework).
- **Retry-with-error-feedback** (raised during triage, not by the
  route): persona sees why attempt 1 failed and can self-correct.
  Real, larger scope, first-witness only — deferred until recurrence
  (`graduation` rule).

## Related

- FR-925 (`feature-requests/FR-925-lane-delivery-agent-context.md`) —
  sibling incident whose diagnosis paid the witnessed cost.
- FR-890 — the research sole route this hardens.
- `examples/demos/research-route/nodes/research_tools.py`
  (`gather_findings`) — the raise site.
- Scripture: `read_raw_output_first`, Commandment 6 (no hidden faults).
