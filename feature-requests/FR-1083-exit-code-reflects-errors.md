# Feature Request: `graph run` exit code reflects recorded errors

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-25
**First consumer / first event:** any script or CI job running
`yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml`. On
2026-09-24 that run lost four of 25 map branches, recorded all four in
`state.errors`, printed its success output and exited 0
([docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.2 items 4–7).
**Research:** FR-890 research route **not run, by operator decision
(2026-09-25): "refile. skip research — document as skipped"**. Substitute: the
in-body [Alternatives Considered](#alternatives-considered) section (six
solution classes, one chosen, one preserved dissent, each dispositioned, plus
an `is_this_a_graph` answer), in the form FR-1076 and FR-1079 use, plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.2 (witnessed run),
§2 D4 (census: none of 202 graphs and not the CLI reads `state.errors`) and
§7 B.
**Prior art:**
[FR-1066](FR-1066-exit-code-reflects-errors.md) (**Rejected**,
[judgement](FR-1066-exit-code-reflects-errors.judgement.md)). Same goal. This
refile answers each objection:
- *R-1 (research):* Alternatives Considered lists six solution classes, not
  three variants of one exit code, with precedent, a preserved dissent and
  `is_this_a_graph`.
- *R-2 (reachable paths):* the RED witness is no longer a raising
  `on_error: fail` node. A top-level `on_error: fail` re-raises
  (`yamlgraph/error_handlers.py#L91-L106`, called at
  `yamlgraph/node_factory/llm_execution.py#L147-L148`), the exception reaches
  `except Exception` at `yamlgraph/cli/graph_commands.py#L249-L251`, and the
  run exits 1. That stays 1. The witnesses are graphs that *complete* with
  entries in `state.errors`; [Reachable paths](#reachable-paths) lists them
  from source. Tolerance is a typed field set where the `PipelineError` is
  built, not a match on message text. JSON and `run_end` use one count
  definition.
- *R-3 (output before exit):* the order is fixed in
  [Proposed Solution](#proposed-solution) item 5; exports run before
  `sys.exit(3)`. The shell callers are listed in
  [Callers](#callers-of-graph-run). `min_success` does not make errors
  tolerated.
- *Operator decision on FR-1066 (2026-09-25, judgement R-3 / AC-04):* "exit 3
  is a hard stop. Shell callers must not continue past it unless they handle
  it explicitly." The caller table applies it.

[FR-677](FR-677-verification-first-class-dsl.md) (Done). A graph may opt in to
`verify:` with `check: "state.errors | length == 0"`. No census graph does
(plan §7 "Prior art to disposition"), and `on_fail: halt` raises before exports
(see Alternatives 3 and 4).
[FR-1073](FR-1073-map-result-contract.md) (authority active, not yet merged).
It owns the map failure channel. After it lands, a non-tolerated map failure
adds one `PipelineError` with `node=_map_<name>_sub` to `state.errors`, a
tolerated one adds none, and an unmet `min_success` raises
`MapCompletenessError` (its items 3 and 6). This FR works the same before and
after FR-1073: it only reads the final `state.errors`. FR-1073 lists "CLI exit
codes (refiled FR-1066)" as out of its scope.
[FR-827](FR-827-verify-extract-dedup.md) defect 4 — worked around downstream
only.

## Summary

When `graph run` completes and `state.errors` holds at least one error the
author did not tolerate, the CLI exits 3 ("completed with errors") after all
output and exports are written. A crash or refusal stays exit 1. Errors from
`on_error: skip` and guard `on_fail: skip` are marked tolerated when they are
built and do not set exit 3. The `--json` object and the `run_end` route-log
event carry the same two counts.

## Value Statement

A script or CI job can tell a clean run (0) from a run that finished but lost
work (3) and from a crash (1), without parsing output. With `set -e`, a run
that lost work stops the pipeline instead of feeding partial output onward.

## Problem

- `cmd_graph_run` never reads `result["errors"]`. It calls
  `_emit_success_output` (`yamlgraph/cli/graph_commands.py#L230-L236`) and
  `_handle_optional_exports` (`#L238-L244`) and returns, so the process exits 0.
- Text output hides the list: `_display_result` skips the `errors` key
  (`yamlgraph/cli/graph_run_helpers.py#L60-L63`).
- `run_end` carries only `run_id`, `ended_at` and `dropped_events`
  (`yamlgraph/utils/route_log.py#L190-L199`).
- `state.errors` is an `add`-reducer list (`yamlgraph/models/state_builder.py#L70`).
  Many paths append to it and let the graph continue; see
  [Reachable paths](#reachable-paths).
- `PipelineError` has no way to say "the author chose to tolerate this"
  (`yamlgraph/models/schemas.py#L31-L43`). A counter cannot tell a skip from a
  loss.
- **Double counting (source reading, not witnessed).**
  `build_skip_error_state` copies the existing `state.errors` and appends one
  entry (`yamlgraph/error_handlers.py#L249-L261`). Under the `add` reducer
  this re-appends every earlier error. The verify node shows the intended
  rule: "return only the new deltas" (`yamlgraph/utils/guard_runtime.py#L241-L242`).
  Any count taken today over-counts after a python, shell or agent skip.
- `--stream` exits 0 even when the graph raises: the error event is printed
  (`yamlgraph/cli/graph_commands.py#L50-L52`) and the command returns
  (`#L183-L185`).

### Reachable paths

Paths that append to `state.errors` and let the run **complete** (exit-3
candidates). "Tolerated" is the value this FR sets.

| # | Path | Where | Tolerated |
|---|---|---|---|
| P1 | LLM node, no `on_error`, call fails → `handle_default` | `llm_execution.py#L162-L163`, `error_handlers.py#L165` | no |
| P2 | LLM node `on_error: retry`, retries exhausted | `llm_execution.py#L150-L156`, `error_handlers.py#L108-L135` | no |
| P3 | LLM node `on_error: fallback`, fallback fails | `llm_execution.py#L158-L160`, `error_handlers.py#L139` | no |
| P4 | LLM node `on_error: skip` | `llm_execution.py#L136-L145` | **yes** |
| P5 | LLM node `requires:` missing (no LLM call made) | `llm_nodes.py#L314-L319`, `error_handlers.py#L183` | no |
| P6 | LLM / copilot pre-guard `on_fail: skip` | `llm_nodes.py#L202-L212`, `copilot_node.py#L303-L312` | **yes** |
| P7 | LLM / copilot pre-guard `on_fail: halt` (returns, does not raise) | `llm_nodes.py#L214-L220`, `copilot_node.py#L313-L316` | no |
| P8 | Guard `on_fail: warn`, verify `on_fail: warn` | `guard_runtime.py#L125-L127`, `#L227-L243` | see Human decision H-2 |
| P9 | python / shell node `on_error: skip`; python / shell / agent pre-guard skip | `build_skip_error_state` callers: `python_tool.py#L287`, `#L344`; `tools/nodes.py#L108`, `#L126`; `agent.py#L241` | **yes** |
| P10 | race node `on_error: skip`, all candidates failed | `race_node.py#L412-L425` | **yes** |
| P11 | router race fails, falls back to `default_route` (any `on_error` except `fail`) | `router_race_node.py#L87-L115` | yes only if `on_error: skip` |
| P12 | node `timeout:` expires | `node_timeout.py#L45-L57` | no |
| P13 | map branch raises or times out (includes a sub-node `on_error: fail`) | `map_compiler.py#L140-L173` | no |
| P14 | map branch returns `errors` (sub-node's own entries kept as built) | `map_compiler.py#L193-L202` | as built |
| P15 | python node returns an `errors` list itself | `python_tool.py#L318-L321` | no |

The witnessed run is P1 inside P14: the `expand_all` map in
`examples/demos/innovation_matrix/pipeline.yaml#L26-L27` sets no `on_error`.

Paths that **raise** and exit 1 through `graph_commands.py#L249-L251`, and
stay 1: top-level `on_error: fail` (LLM, python default at
`python_tool.py#L258`, shell default at `tools/nodes.py#L90`, tool_call
`on_error: fail` at `tool_nodes.py#L114-L115`), `GuardHaltError`
(`guard_runtime.py#L144-L156`), verify `on_fail: halt` (`#L238-L239`), and,
after FR-1073, `MapCompletenessError`.

Not visible to this FR: a `tool_call` node with its default `on_error: skip`
(`tool_nodes.py#L106`) writes a failure envelope to its `state_key` and no
`PipelineError`.

## Ideal Result

The exit code of `graph run` is a complete, typed statement about the run:
0 means nothing was lost, or every loss was one the author declared tolerable;
3 means the graph finished, all output and exports exist, and at least one
untolerated error was recorded, named on stderr; 1 means the run crashed or
was refused. The same two numbers appear in `--json` and in `run_end`, and
every scripted caller either stops on 3 or handles it by name.

## Proposed Solution

1. **Typed tolerance at construction.** Add
   `tolerated: bool = False` to `PipelineError`
   (`yamlgraph/models/schemas.py#L31-L43`). Set it to `True` only where the
   author's own configuration chose to continue:
   - P4 (`llm_execution.py#L144`);
   - P9, inside `build_skip_error_state`;
   - P10 (`race_node.py#L419-L425`);
   - P11 when `cfg.on_error == ErrorHandler.SKIP`;
   - guard violations built by `_build_guard_violation`
     (`guard_runtime.py#L60-L84`) when the rule's `on_fail` is `skip`
     (covers P6). `GuardViolation` already carries `on_fail`
     (`yamlgraph/models/schemas.py#L96`).

   Every other constructor keeps the default `False`. Nothing downstream
   inspects message text.
2. **Stop double counting.** `build_skip_error_state` returns only the new
   entry, as the verify node already does.
3. **One tally.** A typed `ErrorTally {error_count, tolerated_error_count,
   first: list[PipelineError]}` is computed once from the final result:
   - it counts only entries created by this invocation (see Human decision
     H-3);
   - `error_count` = entries with `tolerated == False`;
   - `tolerated_error_count` = entries with `tolerated == True`;
   - `first` = up to three untolerated entries, in list order.

   The exit code, the stderr summary, `--json` and `run_end` all read this
   one object.
4. **Exit codes.**
   - 0: completed, `error_count == 0`.
   - 1: crash, refusal or timeout (unchanged; `graph_commands.py#L120-L138`,
     `#L172`, `#L221-L223`, `#L249-L251`; `graph_run_helpers.py#L210-L217`).
   - 3: completed, `error_count > 0`.

   2 is left to argparse usage errors. The empty-input exit in the text-mode
   interrupt loop stays 0 (`graph_run_helpers.py#L223-L225`): the user ended
   the run, it did not complete.
5. **Order inside `cmd_graph_run`:**
   1. `_run_graph_until_complete` returns (`graph_commands.py#L211-L220`).
   2. The tally is computed inside the `with` block and attached to the
      route-log run record, because `run_end` is emitted when the `with`
      block exits (`route_log.py#L187-L199`), before output.
   3. The `with` block exits: `run_end` is written with both counts; the OTel
      span closes as today.
   4. `_emit_success_output` (`#L230-L236`). In `--json` mode the object also
      carries `_error_count` and `_tolerated_error_count`. The leading
      underscore keeps them out of the text display
      (`graph_run_helpers.py#L62`) and away from graph state keys; no graph
      under `examples/` or `graphs/` uses either name.
   5. `_handle_optional_exports` (`#L238-L244`).
   6. The trailing blank line (`#L246-L247`).
   7. If `error_count > 0` or `tolerated_error_count > 0`, print to stderr
      `⚠ completed with N errors (M tolerated)` and one `node: message` line
      per entry in `first`.
   8. `sys.exit(3)` if `error_count > 0`. `SystemExit` is not an `Exception`
      subclass, so the `except Exception` at `#L249` does not turn it into 1.

   If an export raises, the run exits 1 as today: a crash outranks 3.
6. **`--stream`.** An error event exits 1 (see Human decision H-4). Exit 3 is
   not reported in `--stream`: the stream uses `stream_mode="messages"`
   (`yamlgraph/executor_async.py#L279-L281`) and exposes no final state. No
   caller in `scripts/`, `.github/` or `yamlgraph/` passes `--stream`.
7. **Callers.** Apply the table below.
8. **Documentation.** `reference/getting-started.md` CLI section documents
   0/1/3, the tolerated rule, and the two JSON keys.

### Callers of `graph run`

Found by grep for `graph run` and `"graph", "run"` in `scripts/`,
`.github/`, `yamlgraph/`, `examples/`.

| Caller | Today on non-zero | Under exit 3 | Change |
|---|---|---|---|
| `scripts/author.sh#L89-L95` | `set -u`; rc kept in `GRAPH_RC`; artifact decides | continues to artifact check | H-1 |
| `scripts/judge.sh#L85-L96` | same | same | H-1 |
| `scripts/research.sh#L71-L76` | same | same | H-1 |
| `scripts/review.sh#L57-L62` | same | same | H-1 |
| `scripts/outsider.sh#L79-L84` | `set -u`; subshell rc not captured; artifact decides | continues | H-1 |
| `scripts/demo_coverage.sh#L72-L74` | `if …; then ✓` — non-zero marks the demo failed | demo marked failed | none (explicit) |
| `scripts/diary_census.sh#L25-L34` | `set -euo pipefail`, unguarded — script stops | stops | none (hard stop) |
| `scripts/diary_digest.sh#L20-L26` | `set -euo pipefail` — stops before the diary commit | stops | none (hard stop) |
| `scripts/req_audit.sh#L112-L126`, `#L173` | `run_phase` records the code, finalizes, exits with it | exits 3 | none (explicit) |
| `scripts/check_changelog_req.py#L184-L199`, `#L314-L315` | non-zero → `None` → listed as "LLM unavailable" | mislabelled as "LLM unavailable" | branch on 3 with its own reason |
| `yamlgraph/utils/fsm/action.py#L279`, `#L325-L332` | non-zero → FSM `error_event` | `error_event` | none (explicit) |
| `examples/yamlgraph_gen/tools/runner.py#L24-L44` | non-zero → `valid: False`, errors parsed from a traceback | `valid: False`, empty error list | parse the stderr summary lines |
| 18 shell scripts under `examples/` (list in AC-09) | not read per file | not read per file | AC-09 records each |

### Human decision needed

- **H-1 — artifact-verified adapters.** `author.sh`, `judge.sh`,
  `research.sh`, `review.sh` and `outsider.sh` verify "by artifact, never exit
  code" (NC-414). Under the operator's hard-stop rule they must handle 3 by
  name. *Suggested default:* each adds an explicit case for 3 that prints
  `graph completed with errors (rc=3)` to stderr and then runs its unchanged
  artifact check. 1 and other codes keep today's handling.
- **H-2 — `warn` guards and verify `on_fail: warn`.** *Suggested default:* not
  tolerated (exit 3). `warn` exists to tell someone; `skip` exists to go on
  quietly. The only census use of `verify:` would be the
  `state.errors | length == 0` check this FR replaces.
- **H-3 — errors from earlier runs.** `--import-state` loads a prior export
  unfiltered (`yamlgraph/cli/helpers.py#L133-L164`), and `--thread` on an
  existing checkpoint keeps that thread's earlier errors. *Suggested default:*
  count only entries whose `timestamp` (`schemas.py#L37`, set at
  construction) is at or after the CLI's run start; imported JSON entries are
  validated with `PipelineError.model_validate` first. A predecessor's errors
  already set the predecessor's exit code.
- **H-4 — `--stream` crash exit.** Today a raised graph exits 0 in `--stream`.
  *Suggested default:* exit 1 on an error event, in this FR, since it is the
  same boundary and a one-line change.

## Acceptance Criteria

Each RED test runs the CLI (`cmd_graph_run` or a subprocess) on a graph that
makes no real LLM call, in both text and `--json` mode unless stated.

- [ ] AC-01 (RED, completed non-tolerated → 3): (a) an LLM node with a
  missing `requires:` key (P5); (b) a map whose python sub-node raises (P13);
  (c) a mocked LLM node with no `on_error` that fails (P1). Each exits 3;
  stderr names the node and message; `_error_count == 1` in JSON.
- [ ] AC-02 (RED, all tolerated → 0): a mocked LLM node with `on_error: skip`
  fails (P4), and a python node with `on_error: skip` fails (P9). Exit 0;
  stderr prints the tolerated count; JSON has `_error_count: 0`,
  `_tolerated_error_count: 2`.
- [ ] AC-03 (RED, mixed → 3): one P5 and one P9 in the same graph. Exit 3;
  `_error_count: 1`, `_tolerated_error_count: 1`; stderr lists only the
  untolerated entry under `first`.
- [ ] AC-04 (uncaught → 1): a top-level python node with default
  `on_error` (`fail`) raises. Exit 1, no tally line. Same for a top-level LLM
  node with `on_error: fail`.
- [ ] AC-05 (interrupts): `--json` with an interrupt exits 1 as today; text
  mode resumed to completion with one P5 error exits 3; text mode ended with
  empty input exits 0.
- [ ] AC-06 (`--stream`): a graph that raises exits 1 (if H-4 accepted); a
  graph that completes with a P5 error exits 0 and this is documented.
- [ ] AC-07 (output before exit): for the AC-01(a) graph with `--export` and
  `--export-state PATH`, stdout carries the result (text) or the JSON object,
  the export files exist, and only then the process exits 3.
- [ ] AC-08 (telemetry): with the route log enabled, `run_end` carries
  `error_count` and `tolerated_error_count` equal to the JSON keys for
  AC-01..AC-03; a clean run carries 0 and 0.
- [ ] AC-09 (callers): the FR implementation record holds the caller table
  above with all 18 `examples/` shell scripts named and each row's treatment
  of exit 3; the scripts marked "change" are changed (with H-1's decision).
- [ ] AC-10 (double count, RED): a graph with one P5 error followed by a
  python `on_error: skip` failure ends with exactly two entries in
  `state.errors`, not three.
- [ ] AC-11 (earlier runs, per H-3): `--import-state` of an export that holds
  one error, into a clean graph, exits 0.
- [ ] AC-12: `reference/getting-started.md` documents 0/1/3, the tolerated
  rule and both JSON keys.
- [ ] AC-13: new REQ in a capability file, tests tagged,
  `python scripts/req_coverage.py --strict` passes, changelog fragment, FR
  implementation record, diary entry with **Seed:**. The full unit suite is
  green; any test that asserted exit 0 on a graph with recorded errors is
  changed and listed in the record.

## Alternatives Considered

Solution classes (chosen: 1; preserved dissent: 2):

1. **CLI reads final `state.errors`; tolerance is a typed field set at
   construction; distinct exit code 3.** Chosen. One boundary every run
   crosses; the author's `skip` is recorded where it is decided. Precedent for
   a "completed with failures" code distinct from a crash: pytest exits 1 for
   failed tests and 3 for an internal error; rsync exits 23 for a partial
   transfer.
2. **Tolerated failures append nothing to `state.errors`.** Preserved
   dissent. No schema field; the count is `len(errors)`; FR-1073 already does
   this inside maps (its item 3). It loses outside maps because it deletes the
   only record of a skipped failure, and a consumer reads that record today:
   `ocr_cleanup`'s `SkipReport` reads skips from `state.errors` (FR-1073
   census row 59, `tools/merger.py#L160`). Revisit if FR-1073's migration
   leaves no reader of tolerated entries outside maps.
3. **Per-graph opt-in with FR-677 `verify: on_fail: halt`.** Rejected:
   opt-in, zero census adopters (plan §7), and it exits 1, which conflates a
   crash with a finished run.
4. **Framework injects a default verify rule into every graph.** Rejected:
   the verify node raises `GuardHaltError` before END
   (`guard_runtime.py#L238-L239`), so `_emit_success_output` and the exports
   never run (`graph_commands.py#L249-L251`). That is the R-3 objection.
5. **Status only in a report (`run_end`, a JSON field or a status file), exit
   code unchanged.** Rejected: every caller must opt in to read it, and
   `set -e` never sees it. The operator's hard-stop decision needs the exit
   code. The report fields are kept as a complement (items 3 and 5).
6. **Graph-level threshold (`max_errors:`).** Rejected: no consumer asks for
   it, and FR-1073's `min_success` is the one partial-success policy; a second
   one would overlap it (judgement R-3: `min_success` does not make errors
   tolerated globally).

`is_this_a_graph`: no. Counting typed entries and choosing an exit code is a
deterministic rule at the CLI boundary (`the_one_law`), not a model decision.

## Out of scope

- OTel `yamlgraph.run.outcome` (`yamlgraph/observability/otel.py#L26`) stays
  `success|error|interrupted`; refused here, no consumer reads it for this.
- The map failure channel, `node="map_subnode"` naming
  (`map_compiler.py#L153-L159`, `#L172`) and `min_success` — FR-1073.
- Making LLM and copilot pre-guard `halt` raise like python's
  `GuardHaltError` (P7); refused here, it changes node semantics, not the
  exit code.
- `tool_call` failure envelopes that add no `PipelineError`; refused here, a
  different contract (FR-778).
- Exit 3 in `--stream` (item 6).

## Related

- Refiles: [FR-1066](FR-1066-exit-code-reflects-errors.md) (Rejected)
- Composes with: [FR-1073](FR-1073-map-result-contract.md), [FR-677](FR-677-verification-first-class-dsl.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D4, §7 B
