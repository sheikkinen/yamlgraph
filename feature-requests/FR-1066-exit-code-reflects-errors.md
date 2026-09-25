# Feature Request: `graph run` exit code reflects `state.errors`

**Priority:** HIGH
**Type:** Bug
**Status:** Rejected — [judgement](FR-1066-exit-code-reflects-errors.judgement.md); no implementation authority. Re-file with research and reachable exit paths.
**Effort:** 0.5 days
**Requested:** 2026-09-25
**First consumer / first event:** any script or CI job running
`yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml`; on
2026-09-24 that run lost four of 25 branches, recorded all four in
`state.errors`, printed its success output and exited 0.
**Research:** in-body dispositioned alternatives table below, plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.2 (witnessed run)
and §2 D4 (census: none of 202 graphs and not the CLI reads `state.errors`).
The FR-890 research route was not run.
**Prior art:** [FR-677-verification-first-class-dsl.md](FR-677-verification-first-class-dsl.md)
(Done) — a graph may opt in to `verify: check: "state.errors | length == 0"`;
no census graph does, and an opt-in per graph leaves the default silent. This
FR changes the default at the one boundary every run crosses.
FR-827 defect 4 — worked around downstream only.

## Summary

When a run completes with a non-empty `state.errors`, the CLI exits with a
distinct code (3, "completed with errors") instead of 0, and the `run_end`
route-log event carries `error_count`.

## Value Statement

Anyone scripting yamlgraph can tell a clean run from one that recorded
failures without parsing output.

## Problem

`cmd_graph_run` (`yamlgraph/cli/graph_commands.py`) calls
`_emit_success_output` after `_run_graph_until_complete` returns and never
reads `result["errors"]`. `run_end` (`yamlgraph/utils/route_log.py#L193`) has
no failure field. The list is write-only.

## Ideal Result

Exit 0 means no recorded error; exit 3 means the graph finished but recorded
errors, which are summarised on stderr (count and first three, node names
included); exit 1 stays "crashed or refused".

## Proposed Solution

- After a completed (not interrupted) run, count `result.get("errors") or []`.
  Non-empty → print `⚠ completed with N errors` plus up to three
  `node: message` lines to stderr, then `sys.exit(3)`. JSON mode includes
  `"error_count"` in the output object.
- `run_end` gains `error_count`.
- **Tolerated errors.** `on_error: skip` appends to `errors`
  (`llm_execution.handle_error`, SKIP branch). An author who chose `skip` has
  tolerated the failure. The SKIP handler marks its `PipelineError` as
  tolerated; tolerated errors are listed but do not set exit 3.
- Map failures ([FR-1064](FR-1064-map-branch-contract.md)) are ordinary
  errors: exit 3, whether or not `min_success` was met. An unmet
  `min_success` raises and exits 1.

## Acceptance Criteria

- [ ] RED: a two-node graph whose second node fails with `on_error: fail` inside a map (after FR-1064) or a python node appending an error → exit 3, stderr names the node.
- [ ] A graph whose node fails with `on_error: skip` → exit 0, the tolerated error is listed.
- [ ] Clean run → exit 0; `--json` output carries `"error_count": 0`.
- [ ] `run_end` event carries `error_count`.
- [ ] `reference/getting-started.md` CLI section documents exit codes 0/1/3.
- [ ] Scripts in `scripts/` that call `graph run` and treat non-zero as failure are listed; each is updated or confirmed correct.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Rely on FR-677 `verify:` per graph | Rejected: opt-in; zero adopters among census graphs. |
| Exit 1 on any error | Rejected: conflates "crashed" with "finished, some items failed"; callers cannot distinguish partial success. |
| Count `on_error: skip` errors too | Rejected: punishes graphs that explicitly chose to tolerate. |

### Questions for the judge

- Exit code 3 versus another value: recommended 3 (1 = error, 2 = argparse usage).

## Related

- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §7 B
- Pairs with: [FR-1064](FR-1064-map-branch-contract.md) (map failures become errors with node names)
