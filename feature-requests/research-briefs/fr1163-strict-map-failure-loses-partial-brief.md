# Problem brief: a strict map failure discards the succeeded answers and the token totals

**Prior art:** FR-1073 (map result contract: `MapFailure` records, `min_success`,
account node commits the verdict, join raises `MapCompletenessError`);
FR-1161 (`cached_map` reuses the same account and join); FR-1097 (`graph run`
exit 3 for completed runs with untolerated errors); FR-027 / FR-231 (token and
timing callback trackers, `--token-usage`); FR-1152 / FR-1155 (thinking and
cache token parts in the usage summary); FR-1130 (census: a stopped run kept
nothing because results were only written at the end of the judging step).

## Problem statement

A `map` or `cached_map` node without `min_success` requires every item to
be accepted (`compute_verdict` in `yamlgraph/models/map_results.py`: a
missing threshold is `1.0`). When one item fails, the account node commits
the verdict and the join node raises `MapCompletenessError`
(`yamlgraph/compile/map_contract.py`). The exception carries the map name
and the counts only.

`yamlgraph graph run` catches it in its generic handler
(`yamlgraph/cli/graph_commands.py`, `except Exception`), prints
`Error: Map node '<name>' incomplete: accepted 9/10 ...` and exits 1. It
skips the result display, the `--token-usage` summary and every export.
The token tracker object still holds the totals for every call that
completed; nothing prints them. Without a configured checkpointer the
succeeded items' outputs exist only in the in-process graph state and are
gone when the process exits. With a durable checkpointer they remain in
the last checkpoint, but the CLI does not say so.

The operator therefore pays for N-1 good answers and loses both the
answers and the record of what they cost. Blocking downstream nodes on an
incomplete map is intended (FR-1073); losing the evidence is not stated
anywhere as intended.

The question: at which boundary should a strict map failure keep what
already succeeded and what it cost visible to the operator, without
letting incomplete results flow downstream or changing the exit status?

## Classification

judgement/analysis/generation

## Constraints

- FR-1073's contract stands: an unmet `min_success` stops the run before
  any node after the join; exit status stays non-zero.
- No silent fallback (Commandment 6): nothing may make an incomplete map
  look complete to downstream nodes, exports or `--json` consumers.
- Sync, `--async` and `--stream` CLI paths, and `cached_map`, share the
  same join.
- Three-layer architecture: CLI is presentation; the compile layer must
  not print.
- The default in-memory checkpointer is not durable across processes;
  most CLI runs configure no checkpointer.
- TDD: the failing test reproduces the failure without network (fake LLM
  or Python sub-node that raises for one index).

## Witnessed incidents

- 2026-11-14 operator report: "If a run requires every item to succeed and
  one item fails, the whole run stops, and the good answers and the token
  summary are lost."
- Code read 2026-11-14 at `c91e862d`: `_emit_success_output`
  (`yamlgraph/cli/graph_run_helpers.py`) is the only place that prints the
  token summary and is reached only after a successful invoke.
- FR-1130 census (2026-09-28): a run stopped part-way kept nothing because
  the per-item results were written only when the whole judging step ended.
