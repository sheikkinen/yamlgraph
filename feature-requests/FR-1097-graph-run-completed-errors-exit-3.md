# Feature Request: `graph run` exits 3 when a completed run recorded untolerated errors

**Priority:** HIGH
**Type:** Bug
**Status:** Approved with revisions ([judgement](FR-1097-graph-run-completed-errors-exit-3.judgement.md)); R-1 and R-2 folded 2026-09-26; in enforcement.
**Effort:** 1 day
**Requested:** 2026-09-26
**First consumer / first event:** any script or CI job running
`yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml`. On
2026-09-24 that run lost four of 25 map branches, recorded all four in
`state.errors`, printed its success output and exited 0
([docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.2 items 4–7).
**Research:** skipped by operator decision (2026-09-25); the substitute is
FR-1083's
[Alternatives Considered](FR-1083-exit-code-reflects-errors.md#alternatives-considered),
found substantive by its judgement. The chosen class is unchanged.
**Prior art:**
- [FR-1083](FR-1083-exit-code-reflects-errors.md) +
  [judgement](FR-1083-exit-code-reflects-errors.judgement.md) (**SPLIT**).
  This FR is its deliverable D-1 with R-1..R-6 applied; D-2 is
  [FR-1098](FR-1098-stream-error-event-exit-status.md).
- [FR-1066](FR-1066-exit-code-reflects-errors.md) (**Rejected**). Its
  objections were answered by FR-1083; its operator decision stands: "exit 3
  is a hard stop. Shell callers must not continue past it unless they handle
  it explicitly."
- [FR-1073](FR-1073-map-result-contract.md) (merged 2026-09-25, PR #702;
  judgement C-3 met). It owns the map failure channel: a non-tolerated branch
  failure adds exactly one `PipelineError` with `node=_map_<name>_sub`
  (`yamlgraph/compile/map_contract.py#L95-L102`), a tolerated one adds none,
  and an unmet `min_success` raises `MapCompletenessError` at the join
  (`map_contract.py#L213-L216`; FR-1073 items 3, 6, 7). This FR changes none
  of that; it reads the final `state.errors` the map leaves behind.
- [FR-677](FR-677-verification-first-class-dsl.md) (Done), disposition
  carried from FR-1083: a graph may opt in to
  `verify: check: "state.errors | length == 0"`, but no census graph does, and
  `on_fail: halt` raises `GuardHaltError`
  (`yamlgraph/utils/guard_runtime.py#L240-L241`) before output and exports,
  exiting 1 like a crash. Opt-in and output-destroying; not a substitute.

## Summary

When a non-stream `graph run` completes and this invocation added at least one
error to `state.errors` that the author did not tolerate, the CLI exits 3
after all output and exports are written. A crash, a raised failure or a CLI
refusal stays exit 1. An LLM/copilot pre-guard `on_fail: halt` that returns a
`GuardViolation` is a completed run with an untolerated error: exit 3
(decision 4). Errors from `on_error: skip`, guard `on_fail: skip` and guard/verify
`on_fail: warn` are marked tolerated where they are built and do not cause
exit 3. The `--json` stdout object and the `run_end` route-log event carry the
same two counts; exported state does not.

## Value Statement

A script or CI job can tell a clean run (0) from a run that finished but lost
work (3) and from a crash (1) without parsing output; under `set -e` a lossy
run stops the pipeline instead of feeding partial output onward.

## Problem

- `cmd_graph_run` never reads `result["errors"]`: it emits output
  (`yamlgraph/cli/graph_commands.py#L230-L236`), runs exports (`#L238-L244`)
  and returns, so the process exits 0.
- Text output hides the list: `_display_result` skips `errors`
  (`yamlgraph/cli/graph_run_helpers.py#L60-L63`).
- `run_end` carries only `run_id`, `ended_at`, `dropped_events`
  (`yamlgraph/utils/route_log.py#L191-L198`).
- `state.errors` is an `add`-reducer list
  (`yamlgraph/models/state_builder.py#L71`); many paths append and continue
  (FR-1083 [Reachable paths](FR-1083-exit-code-reflects-errors.md#reachable-paths),
  P1–P15, carried by reference; P13/P14 now run through FR-1073's
  `map_contract.py`).
- `PipelineError` cannot say "the author chose to tolerate this"
  (`yamlgraph/models/schemas.py#L31-L43`).
- **Double counting (source reading).** `build_skip_error_state` copies the
  existing `state.errors` and appends one entry
  (`yamlgraph/error_handlers.py#L249-L264`); under the `add` reducer this
  re-appends every earlier error. The verify node shows the intended rule:
  "return only the new deltas" (`guard_runtime.py#L242-L243`).
- **Historical errors.** `--import-state` loads a prior export as raw JSON
  (`yamlgraph/storage/export.py#L116-L126`, via
  `yamlgraph/cli/helpers.py#L133-L163`) and merges it into the initial state
  (`graph_commands.py#L141-L147`); an existing `--thread` checkpoint keeps
  that thread's earlier errors. A naive count of the final list charges this
  run for its predecessors' losses.

## Ideal Result

The exit status of a non-stream `graph run` is a complete, typed statement
about this invocation: 0 means nothing was lost, or every loss was one the
author declared tolerable; 3 means the graph finished, all output and exports
exist, and at least one untolerated error was created by this run, named on
stderr (including a returned LLM/copilot guard halt); 1 means the run crashed,
raised, was refused by the CLI, or left a malformed error entry. `--json` stdout and `run_end`
carry the same two numbers, exported state carries graph state only, and every
scripted caller either stops on 3 or handles it by name.

## Proposed Solution

1. **Typed tolerance at construction.** Add `tolerated: bool = False` to
   `PipelineError` (`schemas.py#L31-L43`; `GuardViolation` inherits it,
   `#L96`). Set `True` only where the author's own configuration chose to
   continue:
   - LLM `on_error: skip` (`yamlgraph/node_factory/llm_execution.py#L144`);
   - `build_skip_error_state` (python / shell / agent skip,
     `error_handlers.py#L230-L264`);
   - race `on_error: skip` (`yamlgraph/node_factory/race_node.py#L413-L428`);
   - router race fallback when `cfg.on_error == ErrorHandler.SKIP`
     (`yamlgraph/node_factory/router_race_node.py#L102-L115`);
   - `_build_guard_violation` when the rule's `on_fail` is `skip` or `warn`
     (`guard_runtime.py#L60-L84`) — covers pre-guard skip and node-level warn
     (`llm_nodes.py#L200`, `#L250`; `copilot_node.py#L302`, `#L364`);
   - verify `on_fail: warn` entries (`guard_runtime.py#L233-L239`).

   Every other constructor keeps `False`, including guard `halt` that returns
   instead of raising (`llm_nodes.py#L214-L221`) and FR-1073's map entry.
   Nothing inspects message text.
2. **Delta-only skip update.** `build_skip_error_state` returns only the new
   entry.
3. **Historical baseline (decision 3).** One boundary in `cmd_graph_run`:
   after `_build_run_config` returns and the `--stream` early return
   (`graph_commands.py#L178-L185`), before `use_async` / `_setup_timeout`
   (`#L187-L190`). At that point the imported state is merged
   (`#L147`), the thread id is in `config` (`graph_run_helpers.py#L136`), and
   the compiled `app` holds its checkpointer (`graph_commands.py#L174-L175`).
   There:
   - every entry of `initial_state["errors"]` (any origin, normally
     `--import-state`) is validated with `PipelineError.model_validate` and
     replaced by the model; a malformed entry prints
     `❌ invalid initial state errors[i]: …` and exits 1 before any node
     runs (R-1: the merged initial state may also come from graph data, a
     var file or CLI variables);
   - if a checkpointer is set and a thread id is present,
     `app.get_state(config).values.get("errors", [])` gives the retained
     entries;
   - `baseline = len(retained) + len(imported)`.

   The `add` reducer appends checkpoint ⊕ input ⊕ node deltas in order, so
   `result["errors"][baseline:]` is exactly this invocation's entries (item 2
   makes that true for skips). Interrupt resumes inside the same invocation
   stay above the baseline.
4. **One tally.** `ErrorTally {error_count, tolerated_error_count,
   first: list[PipelineError]}` is computed once from
   `result["errors"][baseline:]`: untolerated count, tolerated count, and up to
   three untolerated entries in list order. **R-1:** every suffix entry is
   first normalized with `PipelineError.model_validate` (a Python node can
   return arbitrary dicts into the `add`-reducer channel); the normalized list
   lives in the tally only — `result` and exports are not mutated. A malformed
   entry prints `❌ invalid result errors[i]: …` (absolute final-list index plus
   validation detail) and exits 1 before success output, exports or a tally
   line.
5. **Exit status.** 0: completed, `error_count == 0`. 3: completed,
   `error_count > 0`. 1: every existing crash/refusal path, unchanged
   (`graph_commands.py#L120-L138`, `#L171-L172`, `#L221-L223`, `#L249-L251`;
   JSON interrupt `graph_run_helpers.py#L209-L217`), plus item 3's malformed
   initial-state entry and item 4's malformed current-run entry. A returned
   LLM/copilot pre-guard halt violation is untolerated and exits 3
   (decision 4); a raised `GuardHaltError` (side-effect nodes, verify) stays 1. 2 stays argparse's. Empty input in the text interrupt loop stays 0
   (`graph_run_helpers.py#L224-L225`): the user ended the run.
6. **Order inside `cmd_graph_run`:**
   1. `_run_graph_until_complete` returns (`graph_commands.py#L211-L220`).
   2. Still inside the `with`, the tally is computed and its two counts are
      set on the active `RouteRun` (new fields next to `dropped_events`,
      `route_log.py#L85-L89`; the context manager already yields it,
      `#L188`), because `run_end` is written when the `with` exits
      (`#L191-L198`).
   3. The `with` exits: `run_end` carries `error_count` and
      `tolerated_error_count`.
   4. `_emit_success_output` receives the tally as a separate argument. In
      `--json` mode `_print_json_result` serializes the result
      (`graph_run_helpers.py#L71-L75`) and adds `_error_count` and
      `_tolerated_error_count` to that **serialized copy** only. `result` is
      not mutated.
   5. `_handle_optional_exports` (`graph_commands.py#L238-L244`) receives the
      untouched `result`, so neither configured exports
      (`graph_run_helpers.py#L92-L104`) nor `--export-state`
      (`storage/export.py#L97-L113`) contain the CLI keys.
   6. Trailing blank line (`graph_commands.py#L246-L247`).
   7. If either count is non-zero, stderr gets
      `⚠ completed with N errors (M tolerated)` and one `node: message` line
      per `first` entry.
   8. `sys.exit(3)` if `error_count > 0`. `SystemExit` is not an `Exception`,
      so `#L249` does not turn it into 1. An export that raises still exits 1.
7. **`--stream` unchanged.** `_run_streaming` is not modified. Message
   streaming (`yamlgraph/executor_async.py#L279-L281`,
   `stream_mode="messages"`) exposes no final state, so exit 3 is unavailable
   there; this is documented. Streaming error-event exit status is FR-1098.
8. **Callers.** Only the rows marked "handles 3" in the
   [Caller census](#caller-census) are edited.
9. **Documentation.** `reference/getting-started.md` "CLI Usage" documents
   non-stream 0/1/3, the tolerated rule (skip, warn), the history rule, the two
   JSON keys, and that message streaming has no exit 3.

`is_this_a_graph`: no — counting typed entries and choosing an exit status is
a deterministic rule at the CLI boundary (`the_one_law`).

## Caller census

Command: `grep -rln "graph run" examples scripts .github --include='*.sh'`
(29 files), the same with `*.yml`/`*.yaml`, and `"graph", "run"` in Python.
YAML hits other than the workflow are graph/prompt header comments or
descriptions, not callers. Treatments: **unchanged** (visible control flow
already gives the operator's hard-stop or failure semantics), **stops on any
non-zero**, **handles 3** (edited by this FR).

| # | Caller | Current control flow on non-zero | Treatment of 3 |
|---|---|---|---|
| 1 | `.github/hooks/scripts/checks/fr-checks.sh#L77` | comment only | unchanged (not a caller) |
| 2 | `examples/cwe-classifier/classify.sh#L39-L44` | `set -euo pipefail` (L10); `\|\| { show_result; exit 1; }` | stops on any non-zero |
| 3 | `examples/demos/demo.sh#L28` | `set -e` (L6); unguarded in `run_demo` | stops on any non-zero |
| 4 | `examples/demos/enforcer/demo.sh#L24-L25` | `set -euo pipefail` (L2); piped to python | stops on any non-zero |
| 5 | `examples/demos/hook_classifier/demo.sh#L19`, `#L26`, `#L33` | `set -e` (L6); unguarded | stops on any non-zero |
| 6 | `examples/demos/judge/demo.sh#L27-L28` | `set -euo pipefail` (L2); piped to python | stops on any non-zero |
| 7 | `examples/demos/judge/eval.sh#L80-L93` | `if timeout … \| python3` with pipefail (L4); else writes `timeout_or_crash` row (`#L108-L113`), loop continues | unchanged (any non-zero = failed eval row) |
| 8 | `examples/demos/meta/demo.sh#L28-L30` | `set -euo pipefail` (L9); piped to python | stops on any non-zero |
| 9 | `examples/demos/philosopher_book/demo.sh#L12-L13` | `set -euo pipefail` (L2); `\| tee` | stops on any non-zero |
| 10 | `examples/demos/philosopher_book/write_chapters.sh#L50-L57` | `if` → chapter failed; collected `#L77-L78`, `exit 1` `#L88` | unchanged (any non-zero = failed chapter) |
| 11 | `examples/dungeon_master/scripts/generate_and_review.sh#L47-L49` | `set -euo pipefail` (L12); unguarded | stops on any non-zero |
| 12 | `examples/ebook/run-chapters.sh#L47-L56` | `if` → `[FAIL]`, `return 1`; `xargs` pipeline `#L62` under pipefail (L8) | stops on any non-zero (after the batch) |
| 13 | `examples/icpc-2-rfe/classify.sh#L40-L45` | as row 2 (L10) | stops on any non-zero |
| 14 | `examples/image_pipeline/run_multi_provider.sh#L22-L26` | `set -euo pipefail` (L2); unguarded in loop | stops on any non-zero |
| 15 | `examples/image_pipeline/styles-batch.sh#L15-L19` | `set -euo pipefail` (L2); unguarded in loop | stops on any non-zero |
| 16 | `examples/rag/demo.sh#L33` | `set -e` (L5); last command, status propagates | stops on any non-zero |
| 17 | `examples/route_overlay_cli/demo.sh#L11-L15` | `set -euo pipefail` (L2); unguarded, before render | stops on any non-zero |
| 18 | `examples/style_convert/run.sh#L46-L49` | `set -euo pipefail` (L2); last command | stops on any non-zero |
| 19 | `scripts/author.sh#L86-L93` | `set -u` (L6); `GRAPH_RC=$?` (L90); artifact check L93–L109 decides | **handles 3** |
| 20 | `scripts/check_demo_proof.sh#L50` | echoed hint only | unchanged (not a caller) |
| 21 | `scripts/demo_coverage.sh#L72-L84` | `if` → prints `✗ (exit N)`, `return 0` | unchanged (any non-zero = failed demo) |
| 22 | `scripts/diary_census.sh#L25-L33` | `set -euo pipefail` (L4); unguarded | stops on any non-zero |
| 23 | `scripts/diary_digest.sh#L20` | `set -euo pipefail` (L4); stops before diary commit (L23–L28) | stops on any non-zero |
| 24 | `scripts/judge.sh#L85-L94` | `set -u` (L10); `GRAPH_RC=$?` (L90); artifact check L93–L94 decides | **handles 3** |
| 25 | `scripts/outsider.sh#L79-L82` | `set -u` (L14); subshell status discarded; artifact check L87–L107 decides | **handles 3** |
| 26 | `scripts/req_audit.sh#L111-L125`, `#L173` | `run_phase`: `PIPESTATUS` (L118), finalize manifest, `exit $exit_code` (L121–L124) | unchanged (exits 3 after manifest) |
| 27 | `scripts/research.sh#L71-L84` | `set -u` (L6); `GRAPH_RC=$?` (L73); artifact + schema check L76, L83–L84 decide | **handles 3** |
| 28 | `scripts/review.sh#L57-L62` | `set -u` (L6); `GRAPH_RC=$?` (L58); artifact check L61–L62 decides | **handles 3** |
| 29 | `.github/workflows/commitlint.yml#L305` | echoed hint only (L247 runs `check_changelog_req.py --skip-llm`, no graph run) | unchanged (not a caller) |
| 30 | `scripts/check_changelog_req.py#L179-L200`, `#L314-L315` | non-zero → `None` → listed "LLM unavailable"; CI and pre-commit pass `--skip-llm` | unchanged (any non-zero = no LLM verdict) |
| 31 | `yamlgraph/utils/fsm/action.py#L279`, `#L325-L332` | non-zero → FSM `error_event` | unchanged (any non-zero = `error_event`) |
| 32 | `examples/yamlgraph_gen/tools/runner.py#L24-L43` | non-zero → `valid: False` | unchanged (a run with errors is not valid) |

Rows 19, 24, 25, 27, 28 edit (decision 1): after the graph command, a
`case` on the status prints `graph completed with errors (rc=3)` to stderr on
3 and falls through to the unchanged artifact check; other codes keep today's
handling. `outsider.sh` first captures the subshell status after L82 and
writes the line to its `$log`. These are enforcement-infrastructure edits
(judgement C-5): human review required before merge.

## Acceptance Criteria

Each test runs the CLI (`cmd_graph_run` or a subprocess) on a graph with no
real LLM call (mocked LLM or python/`requires:` paths), in text and `--json`
modes unless stated. Tests are committed RED before production changes and
GREEN after, each with `@pytest.mark.req("REQ-YG-700")` (CAP-283).
The judgement's revised AC-01..AC-15 are adopted verbatim.

- [ ] AC-01: A two-item map with one success, one non-tolerated Python sub-node failure, and integer `min_success: 1` completes, retains exactly one current-invocation `PipelineError` named `_map_<name>_sub`, emits normal output and exports, and exits 3; absent `min_success` raises `MapCompletenessError`, exits 1, and emits no tally line.
- [ ] AC-02: P1 (mocked LLM call failure without `on_error`) and P5 (missing LLM `requires:` key) each exit 3 in text and JSON modes; stderr names the node and message; JSON reports `_error_count: 1`.
- [ ] AC-03: One graph with a failing LLM `on_error: skip` node and a failing Python `on_error: skip` node exits 0, reports `_error_count: 0` and `_tolerated_error_count: 2`, and retains exactly two entries. Guard and verify `on_fail: warn` each exit 0 and increment only the tolerated count.
- [ ] AC-04: A graph with one P5 error and one Python skip failure exits 3, reports counts 1 and 1, and lists only the P5 entry in stderr details.
- [ ] AC-05: Top-level Python default/fail and LLM `on_error: fail` exceptions exit 1 with no tally line; a configured export failure exits 1.
- [ ] AC-06: JSON interrupt exits 1; a text interrupt resumed to a P5 completion exits 3; ending the text interrupt prompt with empty input exits 0.
- [ ] AC-07: For a completed P5 error with configured export, `--export`, and `--export-state`, stdout and both files exist before exit 3. Stdout JSON contains both tally keys; neither export contains either key.
- [ ] AC-08: With route logging enabled, `run_end.error_count` and `run_end.tolerated_error_count` equal the JSON projection for untolerated, tolerated, mixed, and clean completed runs.
- [ ] AC-09: One P5 error followed by one Python skip failure leaves exactly two `state.errors` entries, proving that `build_skip_error_state` returns only its delta.
- [ ] AC-10: Imported and checkpoint-retained historical errors do not affect this invocation's status: clean second runs exit 0, and second runs adding one P5 error exit 3 with `_error_count: 1`. Malformed initial-state entries exit 1 before node execution and identify their index.
- [ ] AC-11: A valid serialized `PipelineError` dictionary created during this invocation is normalized and tallied; malformed current-run entries with a missing `node` and an unknown `type` each exit 1 before success output and exports, identify the final-list index, and emit no completed-run tally line.
- [ ] AC-12: The operator-selected LLM/copilot pre-guard halt policy is asserted in text and JSON modes; the raised side-effect/verify `GuardHaltError` path remains exit 1.
- [ ] AC-13: Caller-census rows 19, 24, 25, 27, and 28 explicitly report rc 3 and continue to the unchanged artifact verdict. Shell assertions prove pass with a valid artifact and exit 65 without one. No other caller is edited.
- [ ] AC-14: `reference/getting-started.md` documents non-stream 0/1/3, skip/warn tolerance, the selected guard-halt rule, invocation-only history, malformed-error behavior, both JSON keys, and the absence of exit 3 in message streaming.
- [ ] AC-15: A capability file defines the new requirement; all new tests carry its `@pytest.mark.req` marker; RED and GREEN commits are separate; strict requirement coverage and the full unit suite pass; changed historical expectations are listed in the FR implementation record; the changelog fragment and diary entry with **Seed:** are committed.

## Human decisions

Recorded 2026-09-26 by explicit operator answer (judgement R-2, C-2):

1. **Artifact-verified adapters** (`author.sh`, `judge.sh`, `research.sh`,
   `review.sh`, `outsider.sh`): explicitly accept exit 3 and continue to their
   existing artifact-validation verdict. Edits and citations in the
   [Caller census](#caller-census) rows 19, 24, 25, 27, 28. Judgement C-5
   applies: these are enforcement-infrastructure changes and need explicit
   human review.
2. **Guard / verify `on_fail: warn`**: tolerated. Exit 0; counted in
   `tolerated_error_count` in stderr, JSON and `run_end` (Proposed Solution
   item 1; AC-03).
3. **Historical errors**: exit status reflects only errors created by this
   invocation. Baseline captured once, at `graph_commands.py` between
   `#L185` and `#L187` (Proposed Solution item 3); imported entries validated
   there (AC-10).
4. **Returned LLM/copilot guard halt** (judgement R-2, answered 2026-09-26):
   completed-error semantics. A pre-guard `on_fail: halt` that returns an
   untolerated `GuardViolation` completes the run and exits 3 after normal
   output and exports; exit 1 is reserved for CLI refusals and raised failures.
   Guard execution semantics are unchanged (AC-12).

## Scope

Judgement deliverable **D-1**: non-stream `graph run` completed-result tally,
typed tolerance, truthful 0/1/3 status, stderr summary, JSON projection,
`run_end` counts, delta-only skip update, historical baseline, the named
caller migration, documentation, tests, changelog, implementation record and
diary.

Not authorized (judgement "Scope is frozen"): `--stream` behavior (FR-1098);
exit 3 in streaming mode; OTel `yamlgraph.run.outcome` changes
(`yamlgraph/observability/otel.py`); map failure-channel, naming, retry or
`min_success` changes (FR-1073); changing LLM/copilot guard-halt semantics;
creating `PipelineError` records for `tool_call` failure envelopes (FR-778);
graph-level error thresholds; mutating final graph state or exports with CLI
tally keys; editing callers not marked "handles 3"; CI, hook, judge-doctrine
or review-doctrine changes.

## Related

- Split from: [FR-1083](FR-1083-exit-code-reflects-errors.md) (judgement SPLIT)
- Sibling: [FR-1098](FR-1098-stream-error-event-exit-status.md) (D-2, streaming error-event exit)
- Refiles: [FR-1066](FR-1066-exit-code-reflects-errors.md) (Rejected)
- Prerequisite (met): [FR-1073](FR-1073-map-result-contract.md), PR #702
- Composes with: [FR-677](FR-677-verification-first-class-dsl.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D4, §7 B
