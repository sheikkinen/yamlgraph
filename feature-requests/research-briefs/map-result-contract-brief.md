# Problem brief: a map node's output does not say which items failed or whether the set is complete

**Prior art:** FR-1064 (SPLIT; this brief covers its map-result half only —
provider retry ownership is a separate problem), FR-957 (judged, its
`error_handler` design disproved for concurrent branches), FR-936 (SPLIT
parent; D-1 FR-955, D-2 FR-939, D-3 FR-956 stay outside this problem),
FR-985 (Shelved census coverage floor), FR-408 (Rejected runtime repair
metadata), FR-677 (opt-in `verify:` block), FR-944 (map-to-map barrier join).

## Problem statement

A `type: map` node fans a list out with LangGraph `Send`, runs one sub-node
per item concurrently, and merges each branch's output into one `collect`
list through a reducer (`yamlgraph/compile/map_compiler.py`,
`wrap_for_reducer`). When a branch fails, the wrapper catches the exception
and returns `{_map_index, _error}` into the same `collect` list as real
results. Downstream nodes cannot tell 25 results from 21 results plus four
error strings, and no node after the map checks how many items were
dispatched versus how many came back.

Three facts from the 2026-09-24 investigation (`docs/issues-2026-09-24.md`
§1, §2, §4, §5, witnesses in its appendix):

1. **Error rows reach content.** In `examples/demos/innovation_matrix/pipeline.yaml`
   four of 25 branches timed out; `synthesize` received 21 expansions plus
   four stringified `PipelineError` reprs under a prompt that says "25 cell
   expansions", and produced a confident ranking. Census over 202 graphs and
   67 maps: 26 in-graph consumers read map output; 13 LLM nodes render it
   into prompts, 11 downstream maps fan out over it; one consumer
   (`examples/demos/corpus_census/tools.py`) filters `_error` rows by hand.
2. **`on_error: fail` does not fail.** A sub-node with `on_error: fail`
   raises; the wrapper's `except Exception` turns it into an `_error` row.
3. **Letting exceptions escape loses finished work.** Probed on LangGraph
   1.2.11: when two or more `Send` branches run in one step and one raises,
   the whole step raises; node-level `error_handler` fires only when the step
   has a single task; the finished branches' results are not in the returned
   state. `update_state(as_node=...)` repair discards pending writes.

The wrapper has three error paths producing three row shapes (one lacks
`_error_type`); all record the node as `map_subnode`. Its error check tests
key presence (`"errors" in result`), so a successful update carrying
`errors: []` is recorded as a failure.

A map compiles to an edge function returning `Send`s plus one sub-node; the
edge out of the map is `sub_node → target`. There is no node after the
branches, and an edge function cannot write state, so the dispatched count
is not recorded anywhere.

## Classification

judgement/analysis/generation

## Constraints

- **Finished work survives.** A failure in 1 of 100 branches must not discard
  the 99 finished results or require re-running them.
- **Downstream consumers must not silently receive an incomplete set as
  complete.** FR-985's shelving shows census briefs tolerated 57–92%
  coverage; it does not show that every consumer (an LLM prompt saying "all
  25") may consume partial output without being told.
- **Identity, not only count.** The dispatched set can change if a branch
  mutates state that `over` depends on; two maps may write the same `collect`
  channel; the same map may run more than once in a loop; zero items is
  legal. Completeness must be defined against what was actually dispatched.
- **Item identity is needed downstream.** A later resumable-map
  investigation (FR-1065) needs a stable per-item identifier on every result
  and every failure; `_map_index` is positional only.
- **Retry is out of scope.** Three retry layers (provider SDK, executor loop,
  node `on_error: retry`) already exist; which layer owns which error class is
  a separate problem. This problem must be solvable with Python sub-nodes
  alone.
- **Scope fence.** FR-939 (overflow), FR-955 (branch input projection),
  FR-956 (timeout threads) stay separate (FR-936 judgement R-1).
- **No compat shims** (Commandment 8); migrate the one in-repo consumer that
  reads `_error` rows.
- **Three-layer architecture**: map semantics live in `yamlgraph/compile/`;
  graph authors express policy in YAML.

## Witnessed incidents

- 2026-09-24, `innovation_matrix/pipeline.yaml` on haiku, 12 CPUs: 25
  dispatched, 21 succeeded, 4 `APITimeoutError` after ~91 s each;
  `synthesize` output ranked "top 5 of 25"; exit 0.
- Appendix witness D2: a Python sub-node raising under `on_error: fail`
  returns `{'results': [{'_map_index': 7, '_error': 'on_error=fail raised
  inside branch', '_error_type': 'RuntimeError'}], 'errors': [PipelineError(...)]}`.
- Appendix witness §4.1: 100 `Send` branches, item 99 raises → the run raises;
  `len(out["results"]) == 0`, `next == ()` — the 99 finished results are gone.
- `examples/demos/corpus_census/tools.py`: hand-filters `_error` rows from
  `collect` before reducing.
