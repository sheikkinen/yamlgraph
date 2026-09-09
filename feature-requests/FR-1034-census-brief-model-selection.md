# Feature Request: FR-1034 independent model selection for the census brief

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.25 days
**Requirement:** REQ-YG-675 (new), added to **CAP-250 corpus-census synthesize
tail**, which already owns this stage and lists `examples/demos/corpus_census`
in `modules`.
**Requested:** 2026-09-09
**First consumer / first event:** the CLAUDE.md corpus census, at the run of
2026-09-09 that classified 150 files on `mercury-2.5` for $0.04 and then lost
its brief because the same model was forced on the synthesis call.
**Research:** in-body solution-class table below (FR-889 style).
**Prior art:** [FR-895](FR-895-census-synthesize-tail.md) — introduced the
synthesize tail and the wording this FR corrects;
[FR-1028](FR-1028-graph-run-provider-model-override.md) — added
`graph run --provider/--model`, a *graph-wide* override; this FR is per-stage
and complements it. [FR-1033](FR-1033-markdown-corpus-census-adapters.md) — the
binding whose live run produced the evidence.

## Summary

Let the census synthesis call use a different provider and model from the
per-item judgement. One new optional pair of variables and a small resolver;
absent them, every existing invocation behaves exactly as today.

## Value Statement

The two LLM stages of a census have opposite shapes — many tiny classifications
versus one long structured synthesis — and today they are forced onto one
model. That makes the cheap-model economics unusable: choosing a cheap model
for the 150 calls that want it also imposes it on the one call that cannot take
it.

## Problem

`judge_items` and `synthesize` both read the same state:

```yaml
judge_items:  provider: "{state.provider}"   model: "{state.model}"   # :95-96
synthesize:   provider: "{state.provider}"   model: "{state.model}"   # :119-120
```

Neither prompt pins a model independently. There is exactly one knob.

**Measured, 2026-09-09.** A 150-file census run with
`--var provider=inception --var model=mercury-2.5`: the map stage classified
150 files correctly for roughly $0.04; the synthesis call then returned
`429 output token limit exceeded`, and `render_brief` raised
`claims must be a dict`. The ledger survived because it is written first. The
brief was simply lost, and there is no invocation that avoids this without
also paying a large-model price for all 150 judgements.

**A related documentation defect.** `README.md:24` calls the tail "one pinned
`claude-haiku-4-5` call" and `:82` describes the chain as
`anthropic` / `claude-haiku-4-5`. The graph parameterises both. Those lines
describe the **defaults** at `graph.yaml:11-12`, not a pin — and the difference
is exactly what the run above hit: a pin would have survived the override.

## Ideal Result

An operator picks the cheapest model that can do each stage. A cheap map and a
capable synthesis are one invocation, not a choice between them. An operator
who names nothing gets today's behaviour byte for byte, and the README says
what is true.

## Proposed Solution

Only the synthesis stage needs to differ; the map already works. Two new
optional variables and one resolver keep the surface at half the obvious size.

- New optional state: `brief_provider: str`, `brief_model: str`.
- New shared tool `resolve_brief_llm` in `tools.py`, returning
  `{"provider": ..., "model": ...}` — each field the caller's value when
  non-empty, otherwise the existing `provider` / `model`.
- New node `resolve_brief_llm` placed between `prepare_brief_input` and
  `synthesize`, `state_key: brief_llm`.
- `synthesize` reads `provider: "{state.brief_llm.provider}"` and
  `model: "{state.brief_llm.model}"`.

Dotted access into a dict-valued state key is existing behaviour, not an
assumption: `judge_items` already reads `{state.judged_content.value}` and
`{state.judged_content._map_index}` (`graph.yaml:100-101`).

A resolver node rather than a template fallback because **no fallback
mechanism exists**: the state schema has no default support
(`yamlgraph/compile/state_builder.py` — no `default` handling), and no graph in
the repository expresses `{state.x or state.y}`. Verified, not assumed.

`README.md` is corrected in the same change: "pinned" becomes "default", with
the override named.

**Material `graph.yaml` change**, so enforcement goes through the sole
graph-authoring route and retains its authoring report.

## Acceptance Criteria

Test surface: `tests/unit/test_census_brief_model_selection.py`, every test
tagged `@pytest.mark.req("REQ-YG-675")`.

1. `resolve_brief_llm` with neither variable set returns exactly the existing
   `provider` and `model`.
2. With both set, it returns those; with only one set, the other falls back —
   both directions tested independently.
3. An empty or whitespace-only value is treated as unset, not as a model named
   `""`.
4. Missing `provider` or `model` in state raises rather than returning `None`
   in either field.
5. The compiled graph's `synthesize` node resolves its provider and model from
   `brief_llm`, and `judge_items` still resolves from `provider`/`model` —
   asserted against the loaded graph, not against the YAML text.
6. End-to-end over the committed three-file Markdown fixture with a stubbed LLM
   boundary: the judge stage and the synthesis stage receive **different**
   model identifiers when the brief pair is supplied, and identical ones when
   it is not.
7. `README.md` no longer describes the synthesis model as pinned; a test or
   grep-based witness asserts the corrected wording, since the false claim is
   the defect.
8. Wiring: `REQ-YG-675` added to `CAP-250` and `ARCHITECTURE.md`; `FR-1034`
   added to CAP-250's `fr:` list; changelog fragment; FR implementation record;
   authoring report for the `graph.yaml` change; diary distillation.

**Not authorized:** per-stage selection for any node other than `synthesize`;
changes to `judge_items`, the reducer, the ledger, or the citation boundary;
new CLI flags; retry or fallback logic on provider errors; touching the
adapters.

## Research: solution classes

`is_this_a_graph`? **Yes, and it exists** — this modifies one node and adds one
resolver to `corpus_census`. It adds no per-item model call.

| # | Class | Evidence | Disposition |
|---|---|---|---|
| 1 | **Optional `brief_provider`/`brief_model` + resolver node** | Dotted dict access already used at `graph.yaml:100-101` | **Chosen.** Smallest surface; defaults byte-identical; no framework change. |
| 2 | Template fallback `{state.brief_model or state.model}` | No `default` handling in `state_builder.py`; no such expression anywhere in the repo | Rejected: the mechanism does not exist. |
| 3 | Four new vars, one pair per stage | — | Rejected: the map stage has no defect. Doubling the surface for a stage nobody has complained about is speculative. |
| 4 | Re-pin `synthesize` to `claude-haiku-4-5`, matching the README | `README.md:24` | Rejected: makes the docs true by removing a capability, and forfeits the cheap-map economics entirely. Worth naming because it is the one-line change. |
| 5 | Run the census twice — map cheap, then synthesise separately | Possible today | Rejected: two invocations, two provenance records, and the second has no access to the first's frozen state. |
| 6 | Retry/fallback to a larger model on a provider error | The observed failure was a 429 | Rejected: treats a design constraint as a transient fault, and would silently change which model produced a committed brief. |

**Preserved disagreement.** Class 4 is genuinely defensible: pinning the tail to
a known-good model removes a whole class of operator error, and the README
already claims it. The counter is that it makes the census's model policy
un-tunable at exactly the point where cost differs by 50×. Class 3 may become
right if a future consumer wants an expensive judge and a cheap brief; nothing
observed asks for that yet.

## Related

- FR-895 synthesize tail; FR-940 judgement normalisation; FR-1033 the binding.
- [docs/diary/2026-09-09-reflection-fr-1033-fail-closed-is-the-same-rule-three-times.md](../docs/diary/2026-09-09-reflection-fr-1033-fail-closed-is-the-same-rule-three-times.md)
