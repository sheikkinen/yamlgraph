# Feature Request: FR-1163 Keep what succeeded and what it cost when a strict map fails

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
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

```yaml
probes:
  - "read _print_json_result and the --json failure path — decides the JSON error shape"
  - "check how LangGraph re-raises a node exception under invoke, ainvoke (--async) and stream — confirms the same exception object (with attributes) reaches the CLI on all three"
branches:
  - "LangGraph wraps or copies the exception on a path → read attributes from __cause__ on that path, with a test per path"
  - "--stream path does not raise to graph_commands → print the summaries in the streaming handler's error branch too"
delegations:
  - "research.sh: 1 run (done)"
  - "judge.sh: 1 run"
waits:
  - "judge"
commands:
  - scripts/judge.sh
  - pytest tests/unit/test_fr1163_map_failure_report.py tests/unit/test_fr1073_map_result_contract.py tests/unit/test_fr1161_cached_map.py
  - yamlgraph graph run examples/demos/cached_map/graph.yaml
```

## Proposed Solution

1. `MapCompletenessError(map_name, verdict, collected=None, failures=None)`:
   two new attributes, `collected: list` (the map's `collect` list at the
   join, in index order) and `failures: list[MapFailure]` (this dispatch's
   failure records). The message is unchanged.
2. `make_join_node(name, collect_key, failures_key)` reads both from state
   and passes them on raise. `map_compiler` and `cached_map_compiler` pass
   their keys.
3. CLI (`graph_commands.py`, `graph_run_helpers.py`):
   - initialise `tracker = timing_tracker = None` before the `try`;
   - extract the token and timing print from `_emit_success_output` into
     `_print_usage(tracker, timing_tracker, stream)`, called by the success
     path (unchanged output) and by the error path;
   - on `MapCompletenessError` (text mode): after the existing error line,
     print one line per failure (`#<index> <error_type>: <message>`, message
     cut at 200 characters), then `<n> succeeded results in '<collect>'`;
     with `--full`, print the collected results with the existing result
     display;
   - on any exception after the invoke starts, call `_print_usage` before
     `sys.exit(1)`;
   - `--json`: stdout gets one object
     `{"status": "failed", "error": str, "map": {"name", "verdict", "collected", "failures"}, "token_usage": {...}}`
     (`map` only for `MapCompletenessError`, `token_usage` only when
     tracked); exit 1.
4. Downstream nodes, exports and `--export` files are not produced: the
   FR-1073 block stands.

## Acceptance Criteria

- [ ] AC-01: a map of 3 Python sub-node items where index 1 raises, no
  `min_success`: `MapCompletenessError.collected` holds the 2 succeeded
  results in index order and `.failures` holds one record with index 1.
  Same for `cached_map`.
- [ ] AC-02: `graph run --token-usage` on a graph whose map fails (fake
  LLM with usage metadata) prints `Token usage:` and the failure line for
  index 1, and exits 1.
- [ ] AC-03: with `--full` the succeeded results are printed; without it
  only the count line.
- [ ] AC-04: `--json`: stdout parses as one JSON object with
  `status == "failed"`, `map.collected` of length 2, `token_usage` present;
  exit 1.
- [ ] AC-05: a non-map exception after invoke start (Python node raising)
  with `--token-usage` still prints `Token usage:`; exit 1.
- [ ] AC-06: no node after the join runs and no export file is written
  (existing FR-1073 tests green, plus one assertion on `--export`).
- [ ] AC-07: success-path output is byte-identical to before for the
  existing CLI tests.
- [ ] AC-08: RED commit precedes GREEN; unit suite and `req_coverage
  --strict` pass.

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

## Related

- [FR-1163.research.md](FR-1163.research.md)
- [FR-1073](FR-1073-map-result-contract.md), [FR-1161](FR-1161-cached-map-warm-first.md)
