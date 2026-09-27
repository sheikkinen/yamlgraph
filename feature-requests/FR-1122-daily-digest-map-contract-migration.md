# Feature Request: Daily digest map node on the FR-1073 contract

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced (2026-09-27) — digest PR #5 merged 1b130e62; merge gated on the first PyPI release carrying FR-1073/FR-939 (judgement C-2; v0.6.1 tagged 2026-09-27) (see [Implementation record](#implementation-record))
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

### S-4: The runner reports the verdict as typed data (R-1)

The runtime stores a `MapVerdict` at `_map_verdict.<name>` and
`MapFailure` records in the failures channel
(`yamlgraph/compile/map_contract.py`, `yamlgraph/models/map_results.py`).
The runner validates them at its boundary and reads attributes; a
missing verdict is a loud failure, never a `?`:

```python
from yamlgraph.models.map_results import MapFailure, MapVerdict

verdict_raw = (result.get("_map_verdict") or {}).get("analyze_all")
if verdict_raw is None:
    raise RuntimeError("analyze_all map verdict is missing")
verdict = MapVerdict.model_validate(verdict_raw)
failures = [
    MapFailure.model_validate(item)
    for item in (result.get("analysis_failures") or [])
]
print(f"Analysed {verdict.succeeded} of {verdict.dispatched} - {len(failures)} skipped")
for failure in failures:
    print(f"  skipped #{failure.index}: {failure.error_type}: {failure.message[:120]}")
```

This block runs after FR-1121's post-invoke error guard (R-4). Skips are
reported, never fatal. An untolerated failure raises
`MapCompletenessError` at the join and never returns a result, so it
reaches neither this block nor FR-1121's guard; it propagates non-zero
on its own. The test exercises actual `MapVerdict` and `MapFailure`
instances as the runtime returns them.

### S-5: Files, sequencing and the smoke (R-3, R-4, R-5)

**Surface.** Every implementation path below is in the external
`sheikkinen/yamlgraph-daily-digest` repository: `graph.yaml`,
`prompts/rank_stories.yaml`, `run_digest.py`,
`.github/workflows/digest.yml`, and focused tests under `tests/`. No
digest checkout, nested repository, generated bulletin or database is
ever committed into this YAMLGraph repository (the boundary FR-903 and
FR-905 imposed). This repository owns: the committed authoring brief
`feature-requests/authoring-briefs/fr-1122-daily-digest-map-contract-migration-brief.md`,
this FR and its judgement, the implementation record, and the Distill
entry. A changelog fragment exists in the digest repository only if
that repository's policy requires one; this repository gets none,
because no code here changes.

**Authoring.** The canonical route runs from this YAMLGraph checkout
with `AUTHOR_WORKDIR` set to the digest checkout; the verified
transient report lives at that target's `tmp/draft-authoring-report.md`
and its validation outcomes are copied into this FR's implementation
record.

**Dependency (R-4).** The FR-1122 digest PR is based on the merged
FR-1121 digest changes: `rank_stories` already carries `on_error: fail`
and `list[dict]`, and `run_digest.py` already has the post-invoke error
guard, when this work starts. If the two must stack, the stacked PR
records the shared `prompts/rank_stories.yaml` and `run_digest.py`
resolution, and tests prove the FR-1121 guard runs before the typed
verdict report while raised map joins propagate non-zero.

**Release readiness versus deployment observation (R-4).** Before
merge: the workflow floor names the exact published minimum yamlgraph
release carrying FR-1073 and FR-939 (no placeholder), and an isolated
installation of that release passes AC-03 through AC-08. After merge:
the next ordinary scheduled run records its run id and its
`Analysed N of M` line as an operational witness. That witness never
makes the PR unmergeable.

**Q-1, answered (R-5).** The operator authorised, on 2026-09-27, one
manual `workflow_dispatch` against the exact target release, including
provider spend and the digest's normal archive and email side effects.
It runs after merge, from GitHub Actions; its run id and verdict line
are recorded in the implementation record (AC-13). The ordinary next
06:00 UTC run needs no further decision.

### Not in scope

- Any threshold (`min_success` fraction): H-1, no witnessed need.
- `flatten_output`: superseded by `state_key` at the source.
- A second digest binding, a source change, or any edit to
  `sources/*.tool.yaml`.
- The ranker's schema and error policy: FR-1121.
- Framework changes of any kind: FR-1123 or later.

## Acceptance Criteria

The judgement's revised list is binding; it replaces the original
AC-1..AC-8.

- [ ] AC-01: The external graph's `analyze_all` declares `max_items: 100`, `on_overflow: truncate`, `timeout: 120`, `failures: analysis_failures`; its nested node declares `state_key: analysis` and `on_error: skip`; no map-level `on_error` remains.
- [ ] AC-02: The external `prompts/rank_stories.yaml` contains no `_map_` token; rendering it with two flat `ArticleAnalysis` dictionaries includes both titles and accesses no generated wrapper.
- [ ] AC-03: A compiled consumer-graph fixture with three articles and one nested LLM skip returns two flat `analyzed` rows, one `MapFailure(tolerated=true)`, and a met verdict; removing nested `on_error` makes the same branch untolerated and raises `MapCompletenessError`.
- [ ] AC-04: A compiled consumer-graph fixture with one branch exceeding the configured timeout records `MapFailure(tolerated=false)` and raises `MapCompletenessError` even though the nested node declares `on_error: skip`.
- [ ] AC-05: A compiled consumer-graph fixture with 101 inputs under `max_items: 100` and `on_overflow: truncate` runs exactly the first 100 and emits exactly one warning naming `analyze_all`, 101, and 100.
- [ ] AC-06: The runner validates actual `MapVerdict` and `MapFailure` instances, prints `Analysed N of M - K skipped`, lists each failure through typed attributes, and raises loudly when the `analyze_all` verdict is absent.
- [ ] AC-07: `gate` declares `output`; on the exact target release, `yamlgraph graph lint graph.yaml` reports no E601, W013, W017, or W022.
- [ ] AC-08: Loading the real external graph retains `config.max_concurrency == 8`; its compile check passes with the collector bound.
- [ ] AC-09: The external workflow names the exact published minimum yamlgraph release carrying FR-1073 and FR-939; an isolated installation of that release passes AC-03 through AC-08 before merge.
- [ ] AC-10: FR-1121 is merged beneath this change or the stacked PR records the shared `prompts/rank_stories.yaml` and `run_digest.py` resolution; tests prove the FR-1121 error guard runs before normal post-invoke reporting, while raised map joins propagate non-zero.
- [ ] AC-11: The committed FR-1122 authoring brief names the external checkout and artifacts; the canonical route produces a non-empty target-local report with the required headings and exact lint/smoke outcomes.
- [ ] AC-12: RED and GREEN are separate commits; focused external tests pass; the FR records final status, decisions, deviations, exact target version, commit/PR identity, and artifact ownership; the Distill entry contains `**Seed:**`.
- [ ] AC-13: Q-1 authorised (2026-09-27): one manual workflow run records its run ID and relevant verdict line. After merge, the next ordinary scheduled run records its run ID and `Analysed N of M` line; this post-merge witness does not gate the merge commit.

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

## Judgement fold (2026-09-27)

[Judgement](FR-1122-daily-digest-map-contract-migration.judgement.md):
APPROVED WITH REVISIONS. Folded the same day:

- **R-1** → S-4: the runner validates `MapVerdict` and `MapFailure`
  with Pydantic and reads attributes; a missing verdict raises.
- **R-2** → AC-03..AC-05, AC-08: overflow (101 → 100, one warning),
  timeout (untolerated despite nested skip), skip versus strict, and
  parsed `max_concurrency == 8` are compiled-graph witnesses, not YAML
  reads.
- **R-3** → S-5 Surface: every implementation path is in the external
  repository; nothing from it is committed here; the brief
  `fr-1122-daily-digest-map-contract-migration-brief.md` is committed
  and names the external checkout as `AUTHOR_WORKDIR`; artifact
  ownership per repository is stated.
- **R-4** → S-5: FR-1121 beneath FR-1122; corrected causal claim (an
  untolerated join raises and never reaches FR-1121's guard); release
  readiness (exact PyPI version, isolated install passes) is separated
  from the post-merge observation.
- **R-5 / Q-1** → S-5: the operator authorised the manual
  `workflow_dispatch` smoke on 2026-09-27.

Scope frozen to the judgement's D-1..D-7; conditions C-1..C-8 are
gates.

## Related

- `reference/graph-yaml.md` map section (FR-1073, FR-939 semantics).
- `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/map_contract.py`
  (`classify_result`, `branch_failure`).
- Digest lint output and compile check, 2026-09-27, in the research
  record's witnessed incidents.
- FR-1121 (ranker), FR-1123 (framework gate).

## Implementation record

**Verdict folded:** R-1..R-5 and Q-1 (authorised) on 2026-09-27; enforced the same day.

### Digest repository (`sheikkinen/yamlgraph-daily-digest`, PR #5, merged 1b130e62)

| Step | Commit | Evidence |
|---|---|---|
| RED | `d0b41a3` | `tests/test_fr1122_map_contract.py`, fourteen witnesses through the real compiled graph with tools and LLM stubbed. RED log: map-level `on_error: skip` unread, the poisoned branch untolerated (`accepted 2/3 (succeeded=2, tolerated=0, failed=1)`), `MapCompletenessError` at the join; 101 items raise `on_overflow: error`; the ranker template reaches `item._map_analyze_all_sub`; lint carries E601/W013/W017/W022; the runner has no verdict line. |
| Authoring | route run 2026-09-27 16:46Z | `scripts/author.sh feature-requests/authoring-briefs/fr-1122-daily-digest-map-contract-migration-brief.md`, `AUTHOR_WORKDIR=C:/src/yamlgraph-daily-digest`. Authored paths: `graph.yaml` (sub-node `on_error: skip`, `state_key: analysis`; map `max_items: 100`, `on_overflow: truncate`, `timeout: 120`, `failures: analysis_failures`; `config.max_concurrency: 8`; `gate.output.digest_status`), `prompts/rank_stories.yaml` (flat `item.*`). Validation in the report: lint before/after, validate, `graph info` with the collector bound, the compile witness (account and join nodes present), the fourteen witnesses (14 passed). Smoke deferred to the authorised post-merge `workflow_dispatch`, by brief. Repairs: none. |
| GREEN | `668ca5e` | `run_digest.py` validates `MapVerdict`/`MapFailure` and prints `Analysed N of M - K skipped` after the FR-1121 guard; a missing verdict raises. 68 of 69 tests pass locally (CRLF note as in FR-1121). |

Lint identity sets, same command before and after: removed `E601`,
`W013`, `W017`, `W022`; remaining `W806`, `W021 rank_stories` (unchanged).

### Release gate (C-2, AC-09)

Isolated `yamlgraph==0.6.0` install against the branch: `graph validate`
passes, but the witnesses cannot even collect
(`ModuleNotFoundError: yamlgraph.models.map_results`) and `run_digest.py`
would fail on the same import after the graph completes. Merging before a
release carrying FR-1073 is therefore wrong, as the judge said.
`v0.6.1` was tagged on 2026-09-27 and contains FR-1073 (`d9cfb71c`) and
FR-939 (`4f389233`); once it is on PyPI the final commit pins
`yamlgraph>=0.6.1` in `.github/workflows/digest.yml`, the witnesses are
re-run on an isolated 0.6.1 install, and #5 merges. Record the version,
the run, and the merge SHA here.

### Q-1 smoke and production witness (AC-13)

Authorised 2026-09-27. Pending: one manual `workflow_dispatch` after #5
merges; then the next scheduled run. Record run ids and the
`Analysed N of M` lines here.

### Deviations and route defects

- Same adapter defects as FR-1121 (backslash artifact paths; report
  written under the launcher's `tmp/` for an external target; lint output
  not captured by the adapter's subprocess). Reports verified by hand and
  copied aside (`tmp/author-report-fr1122-digest.md`, transient). Filed as
  a follow-up task against `scripts/author.sh`.
- No changelog fragment in this repository: no code here changed (S-5).
- Judge rendered from the author's session via the sole route; recorded
  as in FR-1121.
