# Feature Request: FR-1163 Keep what succeeded and what it cost when a strict map fails

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced — judged APPROVED WITH REVISIONS (R-1..R-4 folded)
**Requested:** 2026-11-14
**First consumer / first event:** the next `yamlgraph graph run --token-usage`
of a graph whose `map` or `cached_map` has no `min_success` and one failing
item. Today the operator sees one error line; after this FR they see which
items failed and why, how many succeeded, the succeeded outputs (with
`--full`), and the token summary, and the exit status is still 1.
**Research:** [FR-1163.research.md](FR-1163.research.md)
(brief: `research-briefs/fr1163-strict-map-failure-loses-partial-brief.md`)
**Prior art:** FR-1073 (map result contract: the join raises
`MapCompletenessError` and blocks downstream; kept unchanged, this FR only
adds evidence to the exception and prints it). FR-1161 (`cached_map` shares
the join; covered by the same change). FR-1097 (exit 3 for completed runs
with errors; a strict map failure is not a completed run and stays exit 1).
FR-027/FR-231 (token and timing trackers; reused, not changed).
FR-1152/FR-1155 (summary fields; reused). FR-1130 (census lost a stopped
run's results; motivating incident, different stage). Retrieval hits
FR-1160 and FR-1116 (map memo, removed / corpus memo: caching across runs,
not reporting inside one), FR-1005 (research route row demotion) and
FR-962 (census PR set) are dismissed.

## Summary

When a map's `min_success` is not met, attach the collected results and the
failure records to `MapCompletenessError`, and make `graph run` print them
and the token and timing summaries before exiting 1. Any other exception
raised after the graph started also prints the token and timing summaries.

## Value Statement

An operator whose strict map fails on one item keeps the other answers and
the cost record instead of rerunning and paying again blind.

## Problem

- A map without `min_success` requires every item (`compute_verdict`,
  `yamlgraph/models/map_results.py`: missing threshold → `1.0`).
- The join raises `MapCompletenessError(name, verdict)`
  (`yamlgraph/compile/map_contract.py`); the exception carries counts only.
- `graph run` catches it in `except Exception`
  (`yamlgraph/cli/graph_commands.py`), prints one line and exits 1. The
  token summary is printed only by `_emit_success_output`
  (`yamlgraph/cli/graph_run_helpers.py`), which is never reached. The
  tracker still holds the totals.
- Without a checkpointer (the CLI default) the succeeded outputs exist only
  in in-process graph state and are lost at exit.
- Operator report 2026-11-14: "If a run requires every item to succeed and
  one item fails, the whole run stops, and the good answers and the token
  summary are lost."

## Ideal Result

A strict map failure stops the run exactly as today, and the operator's
terminal (or JSON consumer) shows everything the run already paid for:
which items succeeded with their outputs, which failed and why, and the
token and timing totals.

## Planned Operations

(Revised per judgement R-2: the open probes are replaced by a fixed
boundary; a wrapping witness is added only if a committed failing test
shows LangGraph wraps the exception.)

```yaml
probes:
  - "RED witness: real compiled map / cached_map graphs raise the completeness error under invoke and ainvoke with the attributes intact — if a path wraps it, a failing test is committed before any __cause__ handling"
branches:
  - "a committed witness shows wrapping on invoke or ainvoke → read the attributes from __cause__ on that path only"
delegations:
  - "research.sh: 1 run (done)"
  - "judge.sh: 1 run (done, APPROVED WITH REVISIONS)"
waits:
  - "CI on the PR"
commands:
  - pytest tests/unit/test_fr1163_map_failure_report.py tests/unit/test_fr1073_map_result_contract.py tests/unit/test_fr1161_cached_map.py tests/unit/test_graph_commands.py -q --no-cov
  - pytest tests/unit/ -q --no-cov -n 4
  - python scripts/req_coverage.py --strict
```

No paid run is part of acceptance (judgement R-4, C-7).

## Proposed Solution

(Revised per judgement R-1..R-3.)

1. **Exception** (`yamlgraph/models/map_results.py`):
   `MapCompletenessError(map_name, verdict, collect_key="", collected=(), failures=())`
   carries `collect_key: str`, `collected: list` (a shallow copy of the
   whole collect channel at the join, reducer order and row shapes kept;
   it is not limited to the failing dispatch, because append channels,
   shared channels and sequential reuse are supported and rows carry no
   dispatch id) and `failures: list[MapFailure]`. The message is unchanged.
   The two-argument form still works and carries empty evidence.
2. **Capture** (`map_contract.make_join_node(name, collect_key, failures_key)`):
   on an unmet verdict, select failures with
   `f.map == name and f.dispatch == verdict.dispatch`, ordered by index,
   and pass the collect channel snapshot. `map_compiler` and
   `cached_map_compiler` pass their configured keys.
3. **Text report** (`graph_commands.py`, `graph_run_helpers.py`), non-stream
   `invoke` / `ainvoke`, on `MapCompletenessError`, after the existing
   error line:
   - one line per failure: `#<index> <error_type>: <message>` (message cut
     at 200 characters in text only);
   - `<len(collected)> collected results in '<collect_key>' (<verdict.succeeded> succeeded in failing dispatch)`;
   - with `--full`, the snapshot through the existing result display.
4. **Usage on execution failure** — one reporting policy at the CLI
   boundary, never through `_emit_success_output` or an export helper:
   - non-stream execution exceptions, including the inner `TimeoutError`
     path: token and timing summaries printed exactly once, then exit 1;
     timeout teardown unchanged;
   - streaming error-event path: summaries printed once to stderr before
     its existing exit 1; already-streamed tokens kept; no partial-map
     evidence and no `StreamEvent` change (deferred);
   - on failure an enabled tracker prints its summary even with zero calls;
     disabled trackers print nothing; success output keeps its present
     positive-call-only behavior and bytes;
   - pre-execution refusals and post-success export failures are unchanged
     (no added summary, no second JSON object).
5. **JSON** (`--json`, non-stream execution failure): stdout gets exactly
   one object
   `{"status": "failed", "error": str, "map": {...}, "token_usage": {...}, "timing": {...}}`.
   `map` only for the completeness error, with `name`, `collect_key`,
   `verdict`, `collected`, `failures`; verdict and failures serialized as
   structured objects (`model_dump`), collected through the existing state
   serializer. `token_usage` / `timing` are the existing tracker summaries,
   present only when the flag enabled them (zero-call included), with all
   existing fields (reasoning, cache read/write). Human-readable text goes
   to stderr only. Successful JSON is unchanged.
6. The FR-1073 block stands: no node after the join runs, no `--export` or
   `--export-state` output is written, exit status stays 1.

## Acceptance Criteria

(Revised per judgement R-4.)

- [x] AC-01: for each of `map` and `cached_map`, a real compiled three-item
  Python-worker graph with index 1 failing and no `min_success` raises the
  completeness error, via both `invoke` and `ainvoke`, with unchanged
  message/verdict, the configured `collect_key`, two collected rows ordered
  0 then 2, and one typed index-1 failure.
- [x] AC-02: a join state holding historical and other-map failures selects
  only records matching its map and verdict dispatch; the collected
  snapshot keeps the whole channel unmutated; a fixture whose channel
  length differs from `verdict.succeeded` shows both numbers correctly
  labelled in the text.
- [x] AC-03: non-stream failure text has the original error line, the
  collect label and the index/type/message failure line; `--full` shows the
  snapshot, without it result values are absent; a long message is intact
  in exception and JSON but cut in text.
- [x] AC-04: a controlled-usage map failure with `--token-usage --timing`
  reports the expected token totals, call count, reasoning/cache totals and
  timing totals exactly once, and exits 1; with both flags off neither
  summary appears.
- [x] AC-05: JSON failure stdout parses as exactly one object; verdict and
  failures are objects, collected matches the exception, enabled summaries
  equal the controlled tracker summaries; a non-map failure omits `map`;
  disabled tracker fields are absent; nothing decorative on stdout.
- [x] AC-06: a zero-call Python-node failure prints zero-call summaries for
  enabled flags and exits 1; a run that records nonzero usage before a
  non-map exception keeps those exact summaries.
- [x] AC-07: an invocation raising `TimeoutError` exits 1 after one usage
  report with timeout cleanup done; a streaming error event exits 1 after
  one stderr usage report, keeping token stdout and adding no partial-map
  payload.
- [x] AC-08: for an unmet join a downstream sentinel never runs and neither
  `--export` outputs nor the `--export-state` file is created; an unmet
  explicit non-default threshold uses the same path; met-policy and
  completed-error exit 3 unchanged.
- [x] AC-09: deterministic success snapshots stay byte-identical for text,
  `--full`, tracked/untracked usage, JSON and streaming; configuration
  refusal and post-success export failure add no summaries and no second
  JSON object.
- [x] AC-10: a behavior-failing RED commit precedes GREEN; the targeted
  tests, unit suite, lint/format and `python scripts/req_coverage.py
  --strict` pass and are recorded here; every new test carries a
  requirement marker.

## Alternatives Considered

From the research record (five personas, three convergent on the
boundary):

- Write partial results to durable storage before the join raises
  (os-infra, data-process): needs a checkpointer the CLI does not have by
  default, or a new storage path. The exception already crosses the one
  boundary the operator sees; attaching the evidence there needs no
  storage. Rejected.
- Compile layer returns structured metadata to the CLI (yamlgraph-native):
  chosen in its exception form, since FR-1073 requires a raise.
- CLI prints tracker and checkpoint state only (subtractionist): keeps the
  token summary but not the answers when no checkpointer exists. Taken as
  the CLI half.
- AWS Step Functions Distributed Map (librarian): fail the orchestration,
  keep per-item results queryable. Same split as chosen here, in-process.
- Change the default `min_success`: changes FR-1073's contract and hides
  failures. Rejected.

## Implementation Status

RED `4de69fd4` (17 of 23 tests failing on behaviour: missing
`collect_key` attribute, old `make_join_node` arity, absent report text and
JSON object); GREEN follows on the same branch.

| Item | Where | Witness |
|---|---|---|
| Exception evidence | `models/map_results.py` `MapCompletenessError(map_name, verdict, collect_key="", collected=(), failures=())` | AC-01, AC-02 two-argument test |
| Join capture | `compile/map_contract.py` `make_join_node(name, collect_key, failures_key)`, `failures_key_of(config)`; both compilers pass their keys | AC-01 (map + cached_map, invoke + ainvoke), AC-02 |
| Text / JSON report, usage on failure | new `cli/graph_run_failure.py` (`report_execution_failure`, `map_failure_lines`, `print_usage`, line formatters); `graph_commands.py` reports once in the inner `except` and re-raises | AC-03..AC-07 |
| Success output | `_emit_success_output` calls `print_usage(on_failure=False)` | AC-09 golden + byte comparison below |
| Blocking unchanged | no change to edges/exports | AC-08; FR-1097 suite (exit 3) passes |

Verification (2026-11-14, Windows host):

- `tests/unit/test_fr1163_map_failure_report.py`: 24 passed. With the
  FR-1073, FR-1161, FR-1097 and FR-335 suites: 138 passed.
- Full unit suite `-n 4`: 328 failed / 7513 passed / 19 errors. All 327
  failing ids also fail on main `c91e862d` when the same 69 files run there
  (main: 329 failing); none is introduced here (shell, hook, ramp and Unix
  signal tests on this Windows host). CI is the authority.
- Success bytes: `tmp/fr1163_snap.py` run against main and the branch
  produced identical stdout/stderr for text tracked, `--full` tracked, text
  untracked, JSON tracked and JSON untracked.
- `python scripts/req_coverage.py --strict`: exit 0. ruff check/format clean.

Decisions and deviations:

- The RED probe found no wrapping: LangGraph re-raises the join's
  exception unchanged on `invoke` and `ainvoke`, so the `__cause__` branch
  in Planned Operations was not taken.
- Collected rows are the channel as stored, so they keep `_map_index`
  (`{"_map_index": 0, "v": "a"}`), the same rows a successful run collects.
  The RED test expected stripped rows; GREEN corrected the expectation,
  not the snapshot.
- The timeout path is merged into the generic execution handler; the
  reporter keeps the old `❌ <timeout message>` headline for
  `TimeoutError`. Reason: ruff C901 (`cmd_graph_run` 17 > 15). The same
  reason moved the streaming branch to `_stream_or_exit`. Teardown still
  runs in `finally` (asserted).
- `map_failure_lines(exc)` takes no `full` flag: `--full` prints the
  snapshot, and failure messages are always cut at 200 characters in text.
- `failures_key_of(config)` replaces the inline default in
  `map_compiler.compile_map_node` and feeds both joins. The state builder,
  codegen and linter copies are out of scope.
- `reference/module-map.md` budget 302 -> 304 for the new module (the
  FR-1124/1150/1161 precedent).
- Streaming success bytes are not separately pinned; the streaming code is
  unchanged except the error-event branch.
- CAP-11 now lists FR-1163 in `fr:`, and REQ-YG-692 names the new module
  and suite. CI's `test_no_req_collision_across_unrelated_frs` required
  this: FR-1073 and FR-1163 fragments both claim REQ-YG-692.

## Related

- [FR-1163-map-failure-keeps-evidence.judgement.md](FR-1163-map-failure-keeps-evidence.judgement.md)
- [FR-1163.research.md](FR-1163.research.md)
- [FR-1073](FR-1073-map-result-contract.md), [FR-1161](FR-1161-cached-map-warm-first.md)
