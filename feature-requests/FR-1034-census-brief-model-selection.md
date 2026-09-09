# Feature Request: FR-1034 independent model selection for the census brief

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented (2026-09-09)
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
absent them, both calls receive the same pair as before and brief content
and provenance are unchanged.

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
who names nothing gets the same provider and model on both calls as before,
with unchanged brief content and provenance — not byte-identical returned
state, since the resolver necessarily adds `brief_llm`. Every governed document
says what is true, and a brief records the model that actually wrote it.

## Proposed Solution

Only the synthesis stage needs to differ; the map already works. Two new
optional variables and one resolver keep the surface at half the obvious size.

- New optional state: `brief_provider: str`, `brief_model: str`.
- New focused module `examples/demos/corpus_census/brief_model_selection.py`
  holding `resolve_brief_llm`, returning exactly
  `{"provider": str, "model": str}` — each field the caller's trimmed value
  when non-empty, otherwise the existing `provider` / `model`, and raising when
  either base value is absent or blank. **Not** `tools.py`: that file is
  already exactly 450 lines, the repository's hard maximum, and FR-1033 set the
  precedent of splitting rather than exceeding it.
- New node `resolve_brief_llm` placed between `prepare_brief_input` and
  `synthesize`, `state_key: brief_llm`.
- `synthesize` reads `provider: "{state.brief_llm.provider}"` and
  `model: "{state.brief_llm.model}"`.

Dotted access into a dict-valued state key is existing behaviour, not an
assumption: `judge_items` already reads `{state.judged_content.value}` and
`{state.judged_content._map_index}` (`graph.yaml:100-101`).

A resolver node rather than a template fallback because no fallback mechanism
exists in the state schema, and no graph in the repository expresses
`{state.x or state.y}`. Omitted brief-specific variables are nonetheless valid
because the generated state TypedDict is `total=False`
(`yamlgraph/models/state_builder.py:174-213`).

*Correction:* an earlier draft cited `yamlgraph/compile/state_builder.py`. That
file does not exist; the empty grep that produced the claim was evidence of a
missing path, not of a missing feature. The conclusion survives, the evidence
did not.

**Truthful brief provenance (R-2).** `render_brief` currently stamps
`run_meta["model"]` from `state.model` — the *map* model
(`tools.py:443-444`). Left alone, a successful override would write false
provenance and break CAP-250's existing requirement that the brief carry the
effective model. So one call-site change is in scope: `render_brief` reads the
resolved model from `state.brief_llm.model` and writes that. A missing mapping
or a blank field fails loudly; it never reverts to the map model after
resolution. No citation-validation or `census_brief.py` change.

**Documentation (R-3).** The false "pinned" claim lives in three governed
places, not one: `README.md:18-28,75-83`,
`capabilities/CAP-250-census-synthesize-tail.yaml:4-11`, and
`ARCHITECTURE.md:3091-3101`. All three are corrected, and REQ-YG-633's claim
that judge and synthesis are selected together through one `model` variable is
revised so it stays historically accurate once REQ-YG-675 exists.

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
7. Accepted-brief provenance: with a brief override supplied, `run_meta["model"]`
   in the rendered artifact equals the effective brief model, not the map model.
8. Rejected-brief provenance: the same holds for the `*.REJECTED.md` artifact,
   which renders the supplied metadata verbatim.
9. With no override, provenance equals the existing model — the current
   behaviour is preserved, not merely unbroken.
10. `render_brief` raises when `brief_llm` is absent or either field is blank;
    it never falls back to the map model after resolution.
11. Documentation wording is asserted at each named location, not by an
    unrestricted repository grep: `README.md`,
    `capabilities/CAP-250-census-synthesize-tail.yaml`, and `ARCHITECTURE.md`
    no longer describe the synthesis model as pinned or as sharing one variable.
12. REQ-YG-633's wording is revised to stay historically accurate alongside
    REQ-YG-675.
13. Wiring: `REQ-YG-675` added to `CAP-250` and `ARCHITECTURE.md`; `FR-1034`
    added to CAP-250's `fr:` list; changelog fragment; FR implementation record;
    authoring report for the `graph.yaml` change; diary distillation.

**Not authorized:** per-stage selection for any node other than `synthesize`;
changes to `judge_items`, the reducer, the ledger, the citation boundary, or
`census_brief.py`; moving or rewriting existing `tools.py` responsibilities
beyond the one `render_brief` provenance line; new CLI flags; retry or fallback
logic on provider errors; touching the adapters.

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

## Implementation record (2026-09-09)

Enforced as filed after folding R-1..R-3. 23 witnesses, all passing; 237
related tests, no regressions.

- **graph.yaml** authored through the sole route (`scripts/author.sh` with
  `feature-requests/authoring-briefs/fr-1034-census-brief-model-brief.md`);
  report at `tmp/draft-authoring-report.md`, artifact verified, lint + compile
  + fixture smoke passed. The diff is exactly the brief: two state inputs,
  `brief_llm`, the tool declaration, the resolver node, `synthesize`'s two
  selection fields, and the edge rewire.
- **`brief_model_selection.py`** (63 lines) holds `resolve_brief_llm` and
  `resolved_brief_model`.
- **`tools.py`** ends at exactly 450 lines — see the deviation note below.
- CAP-250 gains REQ-YG-675 and FR-1034; ARCHITECTURE.md registers the
  requirement; README, CAP-250 and ARCHITECTURE.md no longer call the
  synthesis model "pinned".

**Deviations and decisions.**

- **Worktree, not main.** `capabilities/` is OS-locked read-only on the main
  checkout (FR-889), and `main_write.py` fences `chmod` against governed roots
  precisely to stop an agent unlocking it. The CAP-250 edit was therefore made
  in a worktree created by `scripts/worktree.sh new`. No lock was mutated.
- **`tools.py` was at exactly 450 lines before this change.** A first attempt
  put the provenance helper inline and reached 469. It now lives in
  `brief_model_selection.py`, reached through the function-local import pattern
  `tools.py` already uses for `census_brief`, and the newly unused
  `SYNTHESIS_MODEL` constant was removed. Net zero; the ceiling holds.
- **AC-07/08 both cover provenance**, accepted and rejected. The rejected path
  needed covering because `emit_brief` renders the same metadata into the
  `.REJECTED.md` artifact, so a false stamp would survive rejection.
- **Test-shape corrections against observed output, not guesses**:
  `load_graph_config` requires slot bindings and returns a `GraphConfig` whose
  nodes are reached as `.nodes`, not by subscript; `render_brief` returns
  `{"brief": {...}}` and requires a `ledger` mapping with `jsonl_path`.
