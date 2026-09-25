# Feature Request: `graph run` rejects `--var` keys the graph's state cannot hold

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-25
**First consumer / first event:** the next
`yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml --var domain=@brief.md`;
on 2026-09-24 `domain` never reached state, `{state.domain}` resolved to
`None`, and all 25 cells were built on domain-free dimensions.
**Research:** in-body dispositioned alternatives table below, plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.1 and §2 D5.
The FR-890 research route was not run.
**Prior art:** [FR-677-verification-first-class-dsl.md](FR-677-verification-first-class-dsl.md)
— lint E007 reports the undeclared reference, but `graph run` gates on lint
only with `--gate`; FR-677's text says E-level findings block execution, which
contradicts that behavior. This FR does not change the lint gate: it refuses
the input at the boundary where it enters. Resolving the FR-677 text
contradiction is recorded there, not here.
REQ-YG-069 (E007) — static; this FR is the runtime counterpart for CLI input.

## Summary

Before invoking the graph, `graph run` compares the `--var` / `--var-file`
keys against the compiled graph's state channels and refuses unknown keys,
listing the ones the graph accepts.

## Value Statement

A mistyped or undeclared input fails in one second with the accepted names,
instead of producing a plausible run on `None`.

## Problem

LangGraph drops input keys that are not channels of the state schema. The CLI
merges `--var` values into `initial_state` (`graph_commands.py`, `cli_vars`)
and passes them on without checking. The loss is silent.

## Ideal Result

Every `--var` key either reaches state or the run is refused before any token
is spent, with a message naming the accepted keys.

## Proposed Solution

- After `graph.compile()`, read the compiled graph's input channels. For each
  key in `file_vars` and `cli_vars` (not `imported_state`, which is a prior
  run's full state) that is not a channel: print
  `❌ --var 'domain' is not a state key of <graph>; declare it under state: or use one of: …`
  and exit 1.
- Out of scope: making a missing `{state.X}` raise instead of resolving to
  `None`. Larger blast radius; needs its own FR and a census of graphs that
  rely on `None`.

## Acceptance Criteria

- [ ] RED: `innovation_matrix/pipeline.yaml --var domain=x` exits 1 with the message; no LLM call made (mock witness).
- [ ] After the graph declares `domain` ([FR-1070](FR-1070-innovation-matrix-repair.md)), the same command passes the check.
- [ ] Census witness: every `graph run … --var` invocation in `README.md`, `reference/`, `examples/**/README.md` and `examples/demos/demo.sh` passes the check (list committed with the test); any that fail are fixed in the same PR or listed as defects.
- [ ] `--import-state` keys are not checked.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Always gate `graph run` on lint | Rejected here: changes every run's behavior on any E-level finding; FR-677's scope. |
| Warn instead of refuse | Rejected: a warning in a long log is how D5 happened (Commandment 6). |
| Check against E007's "known state" set | Rejected: an approximation of the schema; the compiled channels are the truth. |

## Related

- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §7 C
