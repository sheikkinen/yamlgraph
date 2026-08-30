# Feature Request: Research Route Failure Must Cite the Recorded Cause

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
**Effort:** 0.25 days
**Requested:** 2026-08-30
**First consumer / first event:** the next agent whose research run fails a persona node — at the moment it reads the CLI failure output to decide what to fix
**Research:** [FR-926.research.md](FR-926.research.md) — the committed evidence (run 2026-08-30, 5 personas, unanimous pursue, 4/5 convergent on boundary-enforcement at the gather step). The brief filename recorded in that artifact (`fr-926-error-surfacing-problem-brief.md`) is a run-log label, not a committed path; the brief was consumed at run time and is not cited as an artifact (R-3).
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

The formatter must handle the error shape the retry path actually
records (R-1): `error_handlers.py` stores `PipelineError.from_exception(...)`
Pydantic objects, whose fields are `type`, `message`, `node`, and
`details={"exception_type": ...}` — not dicts. Both object and dict
forms are normalized through one accessor; malformed entries are
ignored rather than rendered as invented detail.

```python
def gather_findings(state):
    missing = [key for key in PERSONA_KEYS if key not in state]
    if missing:
        detail = _format_recorded_errors(state.get("errors"))
        raise ValueError(
            f"missing persona findings: {', '.join(missing)}"
            + (f"\nrecorded node errors:{detail}" if detail else "")
        )
    ...
```

Each recorded line carries node, error category, human message, and
`details.exception_type` when present.

Operator-facing witness (R-2): the enriched text must survive the
wrapper. `scripts/research.sh` runs the graph without capturing its
output, then fails the artifact contract; the witness is a
deterministic subprocess test using a fake `YAMLGRAPH_BIN` stub that
emits the enriched `gather_findings` failure text and exits without
writing `tmp/draft-alternatives.md`, asserting the missing key and the
recorded node/type/message appear in the combined operator-facing
output ahead of the wrapper's exit-65 contract failure. No LLM, no API
keys, no tokens.

Scope boundaries (from the brief's constraints, all frozen):

- Schema hard caps (reject, never truncate) unchanged.
- Retry semantics and the error-channel state shape unchanged — this
  reads the contract, it does not alter it.
- The run remains a hard failure; no partial artifact.

## Acceptance Criteria

Revised per judgement (`FR-926-research-failure-cites-recorded-cause.judgement.md`):

- [x] AC-01: A direct unit test calls `gather_findings` with at least
      one missing `PERSONA_KEYS` entry and a populated `state["errors"]`
      containing a `PipelineError`; the raised `ValueError` contains the
      missing state key, recorded node, error category, human validation
      message, and exception type from `details.exception_type`.
- [x] AC-02: A direct unit test calls `gather_findings` with a missing
      persona key and an empty or absent error channel; the raised
      message remains exactly `missing persona findings: <keys>`.
- [x] AC-03: Dict-form error entries in `state["errors"]` are handled
      without type assertions or casts; malformed/non-structured entries
      are ignored rather than inventing details.
- [x] AC-04: `gather_findings` success behavior is unchanged: with all
      five persona keys present it returns the same `{"findings": [...]}`
      shape and still normalizes each persona finding.
- [x] AC-05: `scripts/research.sh` operator output preserves graph
      failure details: a deterministic subprocess test using a fake
      `YAMLGRAPH_BIN` stub observes the enriched failure text before the
      existing artifact-contract failure.
- [x] AC-06: Existing FR-890/FR-896 research-route tests continue to
      pass without weakening graph topology, schema caps, retry config,
      artifact verification, or librarian citation checks.
- [x] AC-07: The FR and research record no longer contain a dangling
      cited brief path.
- [x] AC-08: Changelog fragment in `changelog/unreleased/`, FR
      implementation-status update, and diary reflection.

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

## Implementation Record

Enforced 2026-08-30 within the frozen scope of
`FR-926-research-failure-cites-recorded-cause.judgement.md`.

- **D-1** — R-1/R-2/R-3 folded into this FR before implementation (C-1).
  R-3 resolved by correcting the FR header only: the promoted record
  `FR-926.research.md` is sha256-pinned to `feature-requests/research-runs.jsonl`
  (`research_preflight.py --verify-promotion` returns matching), so editing
  it to repair the label would break provenance. The brief filename there
  is a run-log label, not a cited artifact.
- **D-2** — `examples/demos/research-route/nodes/research_tools.py`:
  `_as_error_record` (duck-typed `model_dump` → dict normalization, no
  isinstance-on-`PipelineError` coupling from a demo to the framework),
  `_format_recorded_errors`, and the enriched raise in `gather_findings`.
  No topology, schema-cap, retry-config, or error-channel-shape change (C-2).
- **D-3/D-4** — `tests/unit/test_fr926_recorded_cause_witness.py`: real
  `PipelineError` object (C-3), dict form with malformed entries dropped
  (C-4), absent/empty channel preserving the terse message, success path
  unchanged.
- **D-5** — same file: `scripts/research.sh` subprocess witness with a fake
  `YAMLGRAPH_BIN` emitting the enriched text and writing no artifact; the
  operator sees the cause before the exit-65 contract failure (C-5).
- **D-6** — changelog fragment `changelog/unreleased/fr-926-research-failure-cites-recorded-cause.md`;
  diary `docs/diary/diary-2026-08-30-the-cause-one-key-away.md`.

Verification: `tests/unit/test_fr926_recorded_cause_witness.py` plus
`test_fr890_research_route.py` and `test_fr896_precedent_traceability.py`
— 53 passed, no existing test modified (AC-06).

RED commit `94b78d5e` precedes the fix; both witnesses failed on the
symptom-only message before the change.

## Related

- FR-925 (`feature-requests/FR-925-lane-delivery-agent-context.md`) —
  sibling incident whose diagnosis paid the witnessed cost.
- FR-890 — the research sole route this hardens.
- `examples/demos/research-route/nodes/research_tools.py`
  (`gather_findings`) — the raise site.
- Scripture: `read_raw_output_first`, Commandment 6 (no hidden faults).
