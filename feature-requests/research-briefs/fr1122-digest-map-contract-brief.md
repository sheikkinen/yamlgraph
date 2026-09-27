# Problem brief: a production map node written against a map contract the framework has since replaced

**Prior art:** FR-1073
(`feature-requests/FR-1073-map-result-contract.md`, Enforced, merged
2026-09-25 after v0.6.0, unreleased on PyPI) is the map result contract:
failures leave `collect`, land in a typed `failures` list, every
dispatched index is accounted, `min_success` defaults to strict, and the
join raises `MapCompletenessError` below threshold. Its migration census
row 10 names `daily_digest/graph.yaml` for decision H-2, moving an unread
map-level `on_error: skip` into the LLM sub-node; the repository example
was migrated, the standalone digest repository was not. FR-939
(`feature-requests/FR-939-...`, merged 2026-09-26, unreleased) made the
fan-out cap a typed policy: over-cap lists raise unless `on_overflow:
truncate` is declared. FR-984 exposed `config.max_concurrency`. FR-1113
(`examples/demos/meta_map/`) is the reference graph that uses the whole
feature set together. FR-1119 taught the linter the state fields a map
creates. FR-052 introduced `flatten_output` for map results. FR-908,
FR-903, FR-904 and FR-905 are the digest's own lineage; FR-904 made the
collector a slot so a second digest is a binding, not a fork. No
REJECTED FR was found in this territory.

## Problem statement

The `analyze_all` node in `sheikkinen/yamlgraph-daily-digest/graph.yaml`
is a `map` over the day's articles with an `llm` sub-node and
`collect: analyzed`. It was written under the map contract that yamlgraph
0.5.x and 0.6.0 ship, and it carries three assumptions that the
framework on main no longer honours.

First, it declares `on_error: skip` at the map level. The map compiler
has never read a map-level `on_error`; under 0.6.0 a failed branch is
written into `collect` as a row carrying `_error` and `_error_type`, and
those rows flow into the ranker prompt as articles with no title.
Under the FR-1073 contract on main the same declaration is still unread,
but the failure is now untolerated: `min_success` defaults to strict, so
one article whose analysis raises fails the whole run with
`MapCompletenessError`. The digest's stated intent is the opposite, that
one bad article should never sink the day.

Second, the sub-node declares no `state_key`. The collected item is
therefore the sub-node's whole update dict, keyed by the generated name
`_map_analyze_all_sub`, and the ranker prompt reaches into it with
`item._map_analyze_all_sub.title`. That couples a prompt template to a
compiler-internal name that FR-1073's account and join nodes now sit
beside.

Third, the map declares no `max_items`, no `on_overflow`, no `timeout`
and no `failures` key. Today the source binding returns about fifty
articles a day, under the default cap of one hundred, so the FR-939
policy is dormant; a wider recency window on a slower source, which
FR-904 explicitly designed for, crosses the cap and raises before any
branch runs. The runner prints article counts from `raw_articles` and
`filtered_articles` but never reads the map verdict, so a day on which
half the analyses failed is indistinguishable in the job log from a day
on which none did.

The digest installs `yamlgraph>=0.5.23` from PyPI with no ceiling. The
first release after v0.6.0 will carry FR-1073 and FR-939 and will reach
the unattended run on its next morning. The open question is what the
digest's map node should declare under the new contract, how its
consumers (the ranker prompt, the runner's report) should read map
results and failures, and how the change is sequenced against a release
the digest does not control.

## Classification

judgement/analysis/generation

## Constraints

- `graph.yaml` and `prompts/*.yaml` edits in the digest repository are
  governed authoring: `scripts/author.sh` with a committed brief under
  `feature-requests/authoring-briefs/` (FR-767, FR-1073 H-2). No manual
  edits.
- The migrated graph must lint clean under `yamlgraph graph lint` on the
  version it targets. The graph currently lints with one error (E601,
  the passthrough gate declares no `output`) and warnings W013 (map with
  no `max_items`) and W017/W022 (map-level `on_error: skip`).
- The map's tolerance policy must be declared where the compiler reads
  it. A skipped article must be *tolerated* in the FR-1073 sense, visible
  in the failures list, and counted in the runner's report; it must never
  reach the ranker as an item.
- The change must not break the digest on the version it runs today. The
  digest cannot pin a version that does not exist on PyPI; the research
  must say whether the migration waits for the release, ships in a form
  valid on both contracts, or pins the workflow to the exact release that
  carries FR-1073 once it exists.
- FR-1073 H-1 forbids thresholds on repository maps without a witnessed
  need; a `min_success` fraction for the digest needs a stated reason
  drawn from the digest's own failure history, not a default.
- FR-904's slot design (a second digest is a binding plus a topics list,
  never a fork) must survive; nothing in the map migration may name a
  source.
- No new framework feature rides along; if the digest needs something
  the map contract lacks, that is a separate judged scope.
- `is_this_a_graph`: the pipeline is one; the question is whether the
  post-map accounting (counts of analysed and failed articles in the
  runner's report) belongs in the graph as a node, in the runner, or in
  the existing formatting node.

## Witnessed incidents

- `sheikkinen/yamlgraph-daily-digest/graph.yaml` on main (commit
  61be37d, 2026-09-27): `analyze_all` declares `on_error: skip` as a
  sibling of `collect`, its `node:` block has no `state_key` and no
  `on_error`, and no `max_items`, `on_overflow`, `timeout` or `failures`
  key is present.
- `sheikkinen/yamlgraph-daily-digest/prompts/rank_stories.yaml`: the
  template iterates `analyzed` and reads
  `item._map_analyze_all_sub.title`, `.relevance_score`, `.summary` and
  `.url`.
- `examples/daily_digest/graph.yaml` in this repository (post FR-1073):
  the same map declares `on_error: skip` inside the `node:` block, per
  H-2 row 10. The standalone digest was outside the census's edit
  surface.
- `yamlgraph/compile/map_compiler.py` at tag v0.6.0, `wrap_for_reducer`:
  an exception in the sub-node returns `{collect_key: [{"_map_index":
  n, "_error": str(e), "_error_type": ...}], "errors": [...]}`; the
  error row is a member of `collect`.
- `yamlgraph/compile/map_compiler.py` on main (FR-1073):
  `branch_failure` writes the failure to `failures_key` with
  `tolerated=False` for a raised exception; `classify_result` marks a
  result `tolerated=True` only when it carries `_skipped`, which only a
  sub-node-level `on_error: skip` produces. `compile_map_node` reads
  `state_key = sub_node_config.get("state_key", "result")`.
- `reference/graph-yaml.md` on main, map section: "The map compiler does
  not read a map-level `on_error`. Put `on_error: skip` (or `retry` with
  `max_retries`) on the sub-node; a failure it skips is tolerated."
- 2026-09-27, `yamlgraph graph lint graph.yaml` in the digest checkout
  against main: E601 on `gate`, W013 on `analyze_all` (dynamic fan-out
  without `max_items`), W017 and W022 on `analyze_all` (`on_error: skip`).
- 2026-09-27, compile check of the digest graph against main with the
  collector bound: compiles; the compiled graph contains
  `_map_analyze_all_sub`, `_map_analyze_all_account` and
  `_map_analyze_all_join`.
- GitHub Actions runs 2026-09-13 through 2026-09-27 of the digest: the
  map stage dispatched between 25 and 40 articles per day and every
  `_map_analyze_all_sub` call logged HTTP 200; no branch failure has
  been witnessed in the retained logs, so the tolerance policy has never
  fired in production.
- `git tag --contains` for the FR-1073 and FR-939 merge commits on
  2026-09-27: no tag. `pyproject.toml` on main reads 0.6.0. The digest
  workflow installs `yamlgraph>=0.5.23`.
