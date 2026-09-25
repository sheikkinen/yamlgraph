# Feature Request: Host-independent default for `max_concurrency`

**Priority:** MEDIUM
**Type:** Bug
**Status:** Rejected — [judgement](FR-1068-default-max-concurrency.judgement.md); no implementation authority. Research and human default-risk decision required.
**Effort:** 0.25 days
**Requested:** 2026-09-25
**First consumer / first event:** the next `innovation_matrix` run on any
machine: on 2026-09-24 (12 CPUs) LangGraph's pool opened 16 simultaneous
requests; on a 28-CPU host the same graph opens 32.
**Research:** in-body dispositioned alternatives table below, plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.2 and §2 D6
(1 of 202 graphs sets `max_concurrency`) and the FR-985 run table (Azure quota
bore width 2; width 12 lost 100 of 259 rows to 429).
The FR-890 research route was not run.
**Prior art:** [FR-984-map-fan-out-max-concurrency.md](FR-984-map-fan-out-max-concurrency.md)
(Enforced) — added `config.max_concurrency` and `--max-concurrency`; left the
default unset, so the width is still `min(32, cpu + 4)`. This FR sets the
default and changes nothing else.
[FR-030](030-map-concurrency-control.md) (Won't Fix) — per-map concurrency
"belongs in the provider"; FR-984's judgement already distinguished the
run-level setting; this FR does not add a per-map field.

## Summary

When neither `--max-concurrency` nor `config.max_concurrency` is set, the run
config gets a fixed default (`YAMLGRAPH_MAX_CONCURRENCY`, default 8) instead of
LangGraph's host-derived pool size.

## Value Statement

The same graph opens the same number of provider requests on every machine.

## Problem

`graph_run_helpers.py#L146-L150` sets `config["max_concurrency"]` only when a
value is given; otherwise LangGraph uses Python's thread-pool default,
`min(32, os.cpu_count() + 4)`.

## Ideal Result

Fan-out width is a declared property of the run, never of the host.

## Proposed Solution

- Resolution order: `--max-concurrency` → `config.max_concurrency` →
  `YAMLGRAPH_MAX_CONCURRENCY` (validated positive integer; garbage raises) →
  8.
- The executor-level entry points (`run_graph`, `run_graph_async`) apply the
  same default so API callers match the CLI.

## Acceptance Criteria

- [ ] RED: patch `os.cpu_count` to 64; the run config's `max_concurrency` is 8.
- [ ] Each level of the resolution order overrides the next (four tests).
- [ ] Non-integer or non-positive env value raises at startup.
- [ ] `reference/development-operations.md` env-var table lists `YAMLGRAPH_MAX_CONCURRENCY`.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Leave unset (status quo) | Rejected: D6, host-dependent behavior. |
| Default 2 (the width the FR-985 Azure quota bore) | Rejected as a global default: one deployment's quota; the graph sets it. |
| Default 16 | Rejected: the 2026-09-24 run at 16 timed out 7 of 16 first-wave requests. |

### Questions for the judge

- Default value: recommended 8; any fixed value satisfies the Ideal Result.

## Related

- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §7 D
