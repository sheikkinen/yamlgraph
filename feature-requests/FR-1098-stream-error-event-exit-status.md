# Feature Request: `graph run --stream` exits 1 when the stream reports an error

**Priority:** HIGH
**Type:** Bug
**Status:** In enforcement without a judgement — operator decision 2026-09-26
("SIC: enforce 1098"; the judge run was declined). Scope stays deliverable D-2
as frozen by the FR-1083 judgement.
**Effort:** 0.5 day
**Requested:** 2026-09-26
**First consumer / first event:** any shell script or CI job running
`yamlgraph graph run <graph> --stream`, at the first run whose LLM call
times out or raises: today it sees exit 0 and carries on as if the run worked.
**Research:** not run; scope is deliverable D-2 frozen by the FR-1083
judgement; alternatives were weighed in FR-1083's Alternatives Considered.
**Prior art:**
- [FR-1083](FR-1083-exit-code-reflects-errors.md) +
  [judgement](FR-1083-exit-code-reflects-errors.judgement.md) (SPLIT): R-1
  moved this defect here; AC-S01/AC-S02 come from it.
- [FR-1066](FR-1066-exit-code-reflects-errors.md) (Rejected): non-stream
  path only; untouched here.
- [FR-1097](FR-1097-graph-run-completed-errors-exit-3.md) (sibling, D-1):
  owns non-stream exit 3; this FR claims no exit 3 and reads no final state.
- [FR-633](FR-633-cli-stream-flag.md): added `--stream`; this FR adds its exit status.

## Summary

When `graph run --stream` receives an error event it prints the error and
exits 0. After this change it prints the error and exits 1. A stream with no
error event still exits 0.

## Problem

`run_graph_streaming_native` catches every exception and timeout and yields
`StreamEvent(type="error")` instead of raising
(`yamlgraph/executor_async.py:327-345`). The CLI only prints it:

- `yamlgraph/cli/graph_commands.py:42` — `_run_streaming(...) -> None`.
- `graph_commands.py:53-54` — on `item.type == "error"`, print to stderr only.
- `graph_commands.py:59` — `asyncio.run(_stream())` returns normally.
- `graph_commands.py:183-185` — `cmd_graph_run` calls it and returns.
- `yamlgraph/cli/__init__.py:363` — `args.func(args)`; `main()` returns, exit 0.

The `except Exception` that exits 1 (`graph_commands.py:249-251`) never
sees it: it is already an event. `tests/unit/test_cli_stream.py:114-164`
asserts the print and a normal return — it witnesses the exit 0.

## Ideal Result

A caller can trust the exit status of `graph run --stream`: 0 means the stream
ended without an error event, 1 means it reported one. The error text is still
printed first. Nothing else about streaming changes.

## Proposed Solution

1. `_stream()` records that an error event was seen (after printing it);
   `_run_streaming` returns that flag (`-> bool`).
2. At `graph_commands.py:184`, if set, `sys.exit(1)`; else return as today.
   `SystemExit` is not an `Exception`; line 249 does not catch it.
3. No final-state read, tally or exit 3: message streaming exposes tokens,
   not a final state (judgement R-1). `interrupt` events are unchanged.
4. Document in `reference/streaming.md`: streaming exits 0 or 1 only; exit 3
   for recorded errors applies to non-stream runs (FR-1097).

## Acceptance Criteria

- [x] AC-S01: A successful message stream exits 0; a stream that emits an
      error event exits 1 after printing the error to stderr; no final-state
      count or exit 3 is claimed.
- [x] AC-S02: Documentation scopes the streaming status contract separately
      from non-stream completed-result status.
- [x] RED commit first: `test_stream_error_event_prints_to_stderr` asserts
      `SystemExit` code 1 and the stderr text; a success-stream test asserts
      normal return. Then the GREEN commit with the production change.
- [x] Tests carry `@pytest.mark.req("REQ-YG-694")`, a new requirement
      ("`graph run --stream` exits 1 on an error event, else 0") in
      `capabilities/CAP-14-graph-level-streaming.yaml`, home of the CLI
      streaming REQ-YG-480. `ARCHITECTURE.md` regenerated;
      `python scripts/req_coverage.py --strict` passes.
- [x] Changelog fragment (`type: fix`, `scope: cli`, `req: REQ-YG-694`).
- [ ] Diary entry in `docs/diary/` with a **Seed:**.

## Scope

Authorized (D-2 only): `_run_streaming` and its call site,
`tests/unit/test_cli_stream.py`, CAP-14, `reference/streaming.md`, changelog
fragment, diary. Not authorized: exit 3 in streaming; any non-stream
`graph run` change (FR-1097); OpenTelemetry outcome changes; changes to
`run_graph_streaming_native`, event shapes or interrupt handling.

## Related

- [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.2

## Implementation record (2026-09-26)

- `_run_streaming` returns `bool` (error event seen, set after the stderr
  print); `cmd_graph_run` calls `sys.exit(1)` on `True`
  (`yamlgraph/cli/graph_commands.py`). `run_graph_streaming_native`, event
  shapes and interrupt handling untouched.
- Changed historical expectation: `test_stream_error_event_prints_to_stderr`
  asserted a normal return (exit 0); it now asserts `SystemExit(1)`.
- REQ-YG-694 in CAP-14; `reference/streaming.md` "Exit status (FR-1098)";
  changelog fragment `fr-1098-stream-error-event-exit-status.md`.
- Deviation: enforced without a judgement by operator decision (see Status).
