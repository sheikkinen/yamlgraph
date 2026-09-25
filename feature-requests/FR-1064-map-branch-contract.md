# Feature Request: Map branch contract — item key, failure channel, completeness at the fan-in, one job per retry layer

**Priority:** HIGH
**Type:** Bug
**Status:** SPLIT — [judgement](FR-1064-map-branch-contract.judgement.md); map results and provider-wide retry require independently judged FRs. No implementation authority.
**Effort:** 2 days
**Requested:** 2026-09-25
**First consumer / first event:** the next `innovation_matrix` run on haiku
(`examples/demos/innovation_matrix/pipeline.yaml`), where on 2026-09-24 four of
25 branches timed out and `synthesize` received 21 results plus four
stringified `PipelineError` reprs under a prompt claiming 25; then every
`corpus_census` consumer, which today filters `_error` rows out of `collect`
by hand (`examples/demos/corpus_census/tools.py#L243`).
**Research:** in-body dispositioned alternatives table below, plus the
committed investigation record
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 (D1–D3), §4
(failure model and LangGraph probes, witnesses in its appendix), §5 (census of
error handling in 202 graphs and 67 maps), §6 (root cause). The FR-890 research
route was not run.
**Prior art:**
[FR-957-map-branch-native-retry-policy.md](FR-957-map-branch-native-retry-policy.md)
(APPROVED WITH REVISIONS, not enforced) — **superseded by this FR**: its
design lets branch exceptions reach LangGraph so `RetryPolicy` retries and
`error_handler` handles the final failure; the §4.1 witness shows
`error_handler` fires only when a step has a single task, so with two or more
branches the whole step raises and finished branches are lost.
[FR-936-map-node-hardening.md](FR-936-map-node-hardening.md) (SPLIT) — this FR
takes over row D-4's surface (sub-node exception ordering) and couples it to
the failure channel, which the §4.1 witness makes inseparable; D-1 (FR-955),
D-2 (FR-939), D-3 (FR-956) stay separate.
[FR-985-census-coverage-floor-and-population-header.md](FR-985-census-coverage-floor-and-population-header.md)
(Shelved) — a fail-closed coverage floor defaulting to 1.0 was shelved because
three real census runs at 57–92% coverage produced equivalent briefs; this FR
therefore defaults to *record, do not raise* and makes raising an explicit
per-map opt-in.
[FR-408-runtime-repair-metadata.md](FR-408-runtime-repair-metadata.md)
(Rejected) — rejected a repair-code registry and a programmatic threshold
relaxation; this FR adds no repair actions and never lowers a declared
threshold: it only separates failures from results and counts them.
[FR-031](031-native-retry-policy.md) (Proposed) — graph-wide `RetryPolicy`;
untouched.

## Summary

Make a map return what it did: successes in `collect`, failures in a separate
channel carrying the item key, and a completeness check at the fan-in. Give
each of the three existing retry layers one job so they stop multiplying.

## Value Statement

Graph authors and downstream prompts stop receiving error text as content, and
a census knows exactly which items failed and why without hand-filtering.

## Problem

- **D1.** A failed branch becomes `{_map_index, _error}` in the same list as
  real results; three error paths in `wrap_for_reducer` produce three shapes
  (one without `_error_type`); all record `node="map_subnode"`.
- **D2.** `on_error: fail` on a sub-node is caught by the wrapper's
  `except Exception` and returned as data.
- **D3.** 26 in-graph consumers receive the error rows: 13 LLM nodes render
  them into prompts, 11 downstream maps fan out over them.
- The wrapper's error-in-result check tests key presence (`"errors" in
  result`), so a successful update carrying `errors: []` is recorded as a
  failure (source reading, `map_compiler.py#L193`).
- An LLM sub-node has three nested retry layers: the provider SDK
  (`max_retries=2`), the executor loop (`MAX_RETRIES=3`, backoff,
  `is_retryable`), and the node handler (`on_error: retry` → `handle_retry`,
  `max_retries` default 3, no backoff, every error). `is_retryable` treats
  `APITimeoutError` as transient and matches `"rate"` as a substring of any
  exception class name.
- A map has no node after its branches: the edge out of a map is
  `sub_node → target`, so there is nowhere to count results against dispatch.

## Ideal Result

After a map, state holds exactly the successful results in `collect`, one
typed failure record per failed item in `failures`, and a verdict saying
whether `results + failures == dispatched` and whether the declared
`min_success` was met. No error text is ever in `collect`. Each failed LLM
request was retried by exactly one layer for transient errors and re-asked by
exactly one layer for validation errors.

## Proposed Solution

Lands after [FR-1063](FR-1063-map-compiler-package-split.md) (package split).

```yaml
judge_items:
  type: map
  over: "{state.items}"
  as: item
  key: "{state.item.id}"            # optional; default _map_index
  node: { type: llm, prompt: judge_item, state_key: judgement, on_error: retry }
  collect: judgements               # successes only
  failures: judgement_failures      # optional; default "<collect>_failures"
  min_success: 0.98                 # optional; absent = record only, never raise
```

1. **Key.** Optional `key:` expression, resolved per item at fan-out and
   carried in the `Send` payload; default `_map_index`. Duplicate keys raise
   at fan-out, naming both indices.
2. **Failure channel.** One helper builds
   `{_map_index, key, error_type, error_class, attempts, node}` for all three
   error paths and writes it to `failures` and to `state.errors` with the
   real sub-node name. Nothing is written to `collect` for a failed branch.
   The presence check becomes "non-empty `errors`".
3. **Join node.** `_map_{name}_join` (FR-944 barrier-join precedent) re-resolves
   `over` from merged state (an edge function cannot write the dispatched
   count), asserts `len(collect) + len(failures) == dispatched` (raise on
   mismatch: that is a framework defect), and writes
   `_map_verdict.<name> = {dispatched, succeeded, failed, min_success, met}`.
4. **`min_success`.** Count or fraction. Absent: verdict recorded, run
   continues (FR-985 evidence). Present and not met: the join raises
   `MapCompletenessError` after all branches finished; the checkpoint keeps
   the finished branches. `on_error: fail` on the map means
   `min_success: 1.0`.
5. **Retry layers, one job each.**
   - SDK retries off (`max_retries=0` in `llm_bounds.py`) — this affects every
     LLM call, not only maps.
   - Executor loop owns transient errors. `is_retryable` becomes an explicit
     per-provider mapping: connection errors, HTTP 5xx and 429 (honouring
     `Retry-After`) are transient; validation, other 4xx and non-streaming
     timeouts are permanent (a timeout cannot tell long from stuck; D7).
     The substring match is removed.
     Consequence: a response that is merely slow now fails once instead of
     three times. The knob is `LLM_REQUEST_TIMEOUT` (global, FR-708); the
     2026-09-24 run had a 27 s median against the 30 s default, so the
     `innovation_matrix` rerun AC sets it explicitly. Streaming responses, so
     the timeout bounds the gap between chunks, is the real cure and is not
     filed (no consumer beyond this demo).
   - Node handler `on_error: retry` keeps only re-asking with validation
     feedback and does not re-run errors the executor classified.
   - The final exception is typed (`BranchFailed`, carrying `attempts` and
     `error_class: transient | permanent`); the wrapper turns it into the
     failure record. [FR-1065](FR-1065-resumable-map-investigation.md) uses
     `error_class` to decide which failures are remembered across runs.
6. **Migrate** `corpus_census/tools.py#L243` from `_error` rows to `failures`.

The attempt count per branch observed on 2026-09-24 (about 91 s, 3 × 30 s)
does not match the nesting's arithmetic (up to 27 attempts). Enforcement
starts by establishing which layers ran (RED 5 below) before claiming a count.

## Acceptance Criteria

- [ ] RED 1: the D2 witness (appendix of the plan) — a raising sub-node yields no `collect` entry and one failure record with the sub-node's name.
- [ ] RED 2: each of the three error paths produces the identical record shape including `error_type`.
- [ ] RED 3: a successful sub-node update containing `errors: []` is collected as a result.
- [ ] RED 4: a 95/4/1 fixture (100 items; 4 transient-then-succeed; 1 permanent) — healthy items called once, transient items retried only by the executor loop, the permanent item not retried, `collect` has 99 entries, `failures` has 1, the verdict reads `dispatched=100 succeeded=99 failed=1`.
- [ ] RED 5: a witness recording the attempt count per layer for one timed-out request before and after the change.
- [ ] Duplicate keys raise at fan-out; `min_success` unmet raises only after every branch has finished (assert the finished branches are in the checkpoint).
- [ ] `APITimeoutError` on a non-streaming call is not retried; a class named `GenerateError` is not retryable.
- [ ] `corpus_census` consumer migrated; no graph in the repo reads `_error` from a map `collect` (grep witness).
- [ ] `innovation_matrix` rerun: `synthesize` input contains no error text.
- [ ] New REQ IDs in `ARCHITECTURE.md`, tests tagged; `reference/graph-yaml.md` map section documents `key`, `failures`, `min_success`.
- [ ] When this FR is judged: FR-957 status set to Superseded by this FR; FR-936 row D-4 points here (notes added at filing).

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| FR-957: exceptions reach LangGraph, `RetryPolicy` + `error_handler` | Rejected: `error_handler` does not fire for concurrent branches (plan §4.1 witness); the step raises and finished work is lost. |
| Any failed branch raises by default | Rejected: discards 99% of finished work over 1% bad items; FR-985 evidence says consumers tolerated 8–43% missing rows. |
| Keep errors in `collect`, add a lint that consumers filter `_error` | Rejected: 26 consumers, `downstream_fix`. |
| Add a fourth retry layer in the wrapper | Rejected: three layers already exist; the defect is their overlap. |
| `update_state(as_node=...)` to repair failed branches | Rejected: discards pending writes of finished branches (plan §4.1 witness). |

### Questions for the judge

- Should consumers be forced to acknowledge failures (e.g. lint warning when a
  node reads `collect` of a map with `failures` it never reads)? Recommended:
  no; the `innovation_matrix` repair ([FR-1070](FR-1070-innovation-matrix-repair.md))
  shows the per-consumer fix, and B ([FR-1066](FR-1066-exit-code-reflects-errors.md))
  makes failures visible at exit.

## Related

- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §7 A
- Depends on: [FR-1063](FR-1063-map-compiler-package-split.md)
- Consumed by: [FR-1065](FR-1065-resumable-map-investigation.md), [FR-1066](FR-1066-exit-code-reflects-errors.md), [FR-1070](FR-1070-innovation-matrix-repair.md)
