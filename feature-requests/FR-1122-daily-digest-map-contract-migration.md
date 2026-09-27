# Feature Request: Daily digest map node on the FR-1073 contract

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-27
**First consumer / first event:** the `sheikkinen/yamlgraph-daily-digest`
scheduled run on the first morning after PyPI ships the first yamlgraph
release after 0.6.0, at the moment `_map_analyze_all_join` evaluates
`min_success` for the day's articles. Without this FR, that morning the
first article whose analysis raises fails the whole run with
`MapCompletenessError`, because the digest's tolerance policy sits on a
key the compiler never reads. Second consumer: `run_digest.py`'s job
log, which will report analysed and failed article counts from the map
verdict instead of only raw and filtered counts.
**Research:** [FR-1122.research.md](FR-1122.research.md)
**Prior art:** [FR-1073](FR-1073-map-result-contract.md) defined the
contract and its migration census row 10 named
`examples/daily_digest/graph.yaml` for decision H-2 (move the map-level
`on_error` into the sub-node); the example was migrated, the standalone
digest repository was outside the census's edit surface, and this FR is
that row applied there plus the consumer changes the contract implies.
[FR-939](FR-939-map-overflow-policy.md) made the fan-out cap a typed
policy; this FR declares the digest's policy explicitly.
[FR-984](FR-984-map-fan-out-max-concurrency.md) exposed
`config.max_concurrency`; this FR declares it to bound provider
concurrency, no new mechanism. [FR-1113](FR-1113-meta-map-demo.md) is
the reference graph for the full feature set; this FR uses the subset a
one-level LLM map needs and no subgraph. [FR-1119](FR-1119-lint-map-owned-state-fields.md)
means the failures key needs no `state:` declaration. FR-052
(`flatten_output`) flattens the `_map_<name>_sub` wrapper after the fact;
this FR removes the wrapper at its source with a sub-node `state_key`
instead. [FR-904](FR-904-slot-bound-digest-collection.md) made the
collector a slot; nothing here names a source. [FR-905](FR-905-ranked-story-boundary-validation.md)
guards the ranker's answer; this FR keeps failed analyses from ever
reaching the ranker. The ranker's own defect is
[FR-1121](FR-1121-daily-digest-ranker-schema-loud-failure.md), not this
FR.

## Summary

The digest's `analyze_all` map was written against the pre-FR-1073 map
contract. It declares `on_error: skip` where the compiler does not read
it, collects each article's analysis under a compiler-internal
`_map_analyze_all_sub` key that the ranker prompt then reaches into,
declares no cap policy, timeout or failures key, and never reports how
many analyses failed. On yamlgraph 0.6.0 a failed branch becomes a
titleless item in the ranker's input; on the next release it becomes a
run-killing `MapCompletenessError`. This FR declares the tolerance
where it is read, flattens the collected item with `state_key`, declares
the FR-939 overflow policy and a per-branch timeout, and has the runner
report the map verdict.

## Value Statement

The digest's operator gets a map stage whose declared tolerance is the
tolerance that runs, and a job log that says how many articles were
analysed and how many were dropped, before the release that would
otherwise turn the first bad article into a red morning.

## Problem

Three assumptions in `graph.yaml` no longer hold on main:

1. **Map-level `on_error: skip` is unread.** The reference says so, and
   `map_compiler.py` reads `on_error` only from the sub-node config. On
   0.6.0 a raised sub-node exception writes `{_map_index, _error,
   _error_type}` into `collect`, and that row reaches the ranker prompt,
   where `item._map_analyze_all_sub.title` renders empty. On main
   (FR-1073) the same exception is an untolerated `MapFailure`;
   `min_success` defaults to strict; the join raises.
2. **The sub-node has no `state_key`.** `compile_map_node` falls back to
   `"result"`, finds no such key in the LLM node's update dict, and
   collects the whole dict, so each item is
   `{"_map_index": n, "_map_analyze_all_sub": {...}}`. The ranker prompt
   is coupled to a generated internal name.
3. **No cap, overflow, timeout or failures declaration.** Today's source
   returns 25 to 40 articles, under the default cap of 100; a wider
   window on a slower source (FR-904's stated use) crosses it and,
   under FR-939's default, raises before any branch runs. A hung
   article fetch or model call has no per-branch bound. The runner
   never reads `_map_verdict`, so a day with half the analyses failed
   logs identically to a clean day.

`yamlgraph graph lint` against main reports W013 (no `max_items`),
W017 and W022 (map-level `on_error: skip`), and E601 (the `gate`
passthrough declares no `output`). The graph compiles on main with the
FR-1073 account and join nodes present.

## Ideal Result

The digest's map declares its policy in the keys the compiler reads,
and every consumer downstream reads the contract's outputs: the ranker
sees only successful analyses as flat items, the runner prints the
verdict, and a tolerated skip is visible in the failures list and the
log. The graph lints clean on the release it targets. The change lands
before that release reaches the unattended run, and nothing about it
names a source or adds a threshold the digest has not earned.

## Proposed Solution

All `graph.yaml` and `prompts/*.yaml` edits go through
`scripts/author.sh` with a committed brief under
`feature-requests/authoring-briefs/` (FR-767; FR-1073 H-2 named this
route for every moved graph).

### S-1: The map node

```yaml
  analyze_all:
    type: map
    over: "{state.articles_with_content}"
    as: article
    max_items: 100
    on_overflow: truncate      # a digest samples; log one WARNING, keep the first 100
    timeout: 120               # per branch; a timeout is never tolerated (FR-069)
    failures: analysis_failures
    collect: analyzed
    node:
      type: llm
      prompt: analyze_article
      state_key: analysis      # collected item is the ArticleAnalysis dict, flat
      on_error: skip           # read here; a skipped article is tolerated (FR-1073)
      variables:
        title: "{state.article.title}"
        url: "{state.article.url}"
        content: "{state.article.content}"
        topics: "{state.topics}"
```

`min_success` stays at the strict default. Tolerated skips count toward
it, so a day where every analysis is skipped still passes the join with
an empty `analyzed`; the ranker then answers with an empty list and the
FR-905 boundary raises `InvalidRankedStoriesError`. Loudness is
preserved without a threshold, per FR-1073 H-1: no witnessed failure
history justifies a fraction, and the retained Actions logs show no
branch failure to date.

```yaml
config:
  max_concurrency: 8           # FR-984; bounds Anthropic concurrency explicitly
```

### S-2: The ranker prompt reads flat items

```jinja
{% for item in analyzed %}
- {{ item.title }} (relevance: {{ item.relevance_score }})
  Summary: {{ item.summary }}
  URL: {{ item.url }}
{% endfor %}
```

No reference to `_map_analyze_all_sub` remains anywhere in the digest
repository.

### S-3: The gate passthrough declares its output

```yaml
  gate:
    type: passthrough
    output:
      digest_status: "{state.digest_status}"
```

Same runtime value, and E601 no longer fires; the graph must lint clean
on the release it targets (AC-6).

### S-4: The runner reports the verdict

After `compiled.invoke(...)` in `run_digest.py`:

```python
verdict = (result.get("_map_verdict") or {}).get("analyze_all") or {}
failures = result.get("analysis_failures") or []
print(f"✓ Analysed {len(result.get('analyzed', []))} of {verdict.get('dispatched', '?')}"
      f" — {len(failures)} skipped")
for f in failures:
    print(f"  · skipped #{f['index']}: {f['error_type']}: {f['message'][:120]}")
```

Skips are reported, never fatal; an untolerated failure never reaches
this line because the join raises first and FR-1121's error guard
catches anything that does.

### S-5: Sequencing against the release

1. Land the edits behind a workflow floor bump to the first release that
   carries FR-1073 and FR-939. Until that release exists on PyPI, the PR
   stays open with the floor named `>=0.6.1` placeholder and AC-7
   unchecked; the FR's implementation record names the exact version
   when it ships.
2. Interim safety (no release yet) is FR-1121: with `on_error: fail` on
   the ranker and the runner's error guard, a titleless item on 0.6.0
   produces a ranker drop or a raise, not a silent day.
3. After merge, one `workflow_dispatch` run is the smoke; the next
   06:00 UTC run is the production witness, and its log must carry the
   new "Analysed N of M" line.

### Not in scope

- Any threshold (`min_success` fraction): H-1, no witnessed need.
- `flatten_output`: superseded by `state_key` at the source.
- A second digest binding, a source change, or any edit to
  `sources/*.tool.yaml`.
- The ranker's schema and error policy: FR-1121.
- Framework changes of any kind: FR-1123 or later.

## Acceptance Criteria

- [ ] AC-1: `analyze_all` carries `max_items`, `on_overflow`, `timeout`
  and `failures`; its `node:` carries `state_key: analysis` and
  `on_error: skip`; no map-level `on_error` remains. A test asserts
  each key by reading `graph.yaml`.
- [ ] AC-2: `prompts/rank_stories.yaml` contains no `_map_` token; a
  test renders the template with two flat `ArticleAnalysis` dicts and
  asserts both titles appear.
- [ ] AC-3: on the target release, a stubbed sub-node that raises for
  one of three articles yields `analyzed` of length 2,
  `analysis_failures` of length 1 with `tolerated: true`, and no raise
  from the join; on the same stub with `on_error` removed from the
  sub-node, the join raises `MapCompletenessError`. (This is the
  H-2 witness: the declaration is read where it is placed.)
- [ ] AC-4: the runner prints the "Analysed N of M — K skipped" line
  from `_map_verdict` and lists each skip; a test with a stubbed result
  proves it.
- [ ] AC-5: `gate` declares `output`; `yamlgraph graph lint graph.yaml`
  on the target release reports no E601, no W013, no W017, no W022.
- [ ] AC-6: `config.max_concurrency: 8` is declared and the compile
  check on the target release passes with the collector bound.
- [ ] AC-7: the workflow floor names the exact release that carries
  FR-1073; the first scheduled run on it logs the verdict line; run id
  and lines recorded in the implementation record.
- [ ] AC-8: every graph and prompt edit has a committed authoring brief
  and adapter report; changelog fragment; FR implementation record;
  Distill diary entry with a `**Seed:**`.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| `min_success: 0.5` so a half-failed day still publishes | Rejected. FR-1073 H-1: thresholds need a witnessed failure history; the logs show none. Tolerated skips already pass strict. |
| Keep map-level `on_error` and guard the prompt with `{% if item.title %}` | Rejected. Leaves a declared policy that does nothing; the guard hides the unread key. |
| `flatten_output: true` (FR-052) instead of `state_key` | Rejected. Flattens after collection; `state_key` removes the wrapper where it is created and is what FR-1113 does. |
| Migrate now, valid on both 0.6.0 and the next release | Rejected. On 0.6.0 a sub-node skip collects `{"value": None}` into `analyzed`; the contract-valid shape needs FR-1073's classifier. Gate on the release. |
| Fork a digest-specific graph for the new contract | Rejected. FR-904: a second digest is a binding, never a fork. |
| Put the verdict report in a graph node instead of the runner | Considered; `is_this_a_graph` answer below. |

`is_this_a_graph`: the pipeline is one, and the map is already the
graph's mechanism. The verdict report is presentation of state the graph
already holds, so it belongs in the runner (the presentation layer), not
a new node.

## Related

- `reference/graph-yaml.md` map section (FR-1073, FR-939 semantics).
- `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/map_contract.py`
  (`classify_result`, `branch_failure`).
- Digest lint output and compile check, 2026-09-27, in the research
  record's witnessed incidents.
- FR-1121 (ranker), FR-1123 (framework gate).
