# Authoring brief: FR-1122 standalone digest — `analyze_all` on the FR-1073 map contract

Governing FR: feature-requests/FR-1122-daily-digest-map-contract-migration.md
(judgement D-1 and D-2; this brief closes the digest authoring run).

Repository boundary: the **external** repository
`sheikkinen/yamlgraph-daily-digest`, checked out beside this one. The
authoring route runs from this YAMLGraph checkout with
`AUTHOR_WORKDIR` set to that checkout; every path below is relative to
the digest checkout. Nothing from that checkout is committed here
(judgement R-3). This brief is applied **after** the FR-1121 digest
brief has landed (judgement R-4): `rank_stories` already carries
`on_error: fail` and `stories: list[dict]` when this run starts.

## Task

Modify **exactly two files** in the digest checkout:

1. `graph.yaml`
   - `analyze_all`: remove the map-level `on_error: skip`; add
     `max_items: 100`, `on_overflow: truncate`, `timeout: 120`,
     `failures: analysis_failures`; in its `node:` block add
     `state_key: analysis` and `on_error: skip`. `over`, `as`,
     `prompt`, `variables` and `collect: analyzed` stay as committed.
     No `min_success` (judgement: not authorised).
   - `config:` block: declare `max_concurrency: 8` (create the block
     if absent).
   - `gate`: add `output:` with the single mapping
     `digest_status: "{state.digest_status}"` (the E601 repair).
   - Every other node, edge, `defaults`, `tools` and `state` entry stays
     byte-identical. `rank_stories` is not touched.
2. `prompts/rank_stories.yaml` — in the user template's `{% for item in
   analyzed %}` loop, read `item.title`, `item.relevance_score`,
   `item.summary`, `item.url` instead of the `item._map_analyze_all_sub.*`
   paths. The schema block and the system prompt stay byte-identical.
   After the edit the file contains no `_map_` token.

Related artifacts edited by the FR's enforcement in the digest
repository, not by this run: `run_digest.py` (typed `MapVerdict` and
`MapFailure` reporting after the FR-1121 guard), `.github/workflows/digest.yml`
(the exact minimum yamlgraph release floor), and the focused FR-1122
tests under `tests/`.

## Validation

The digest's target is the exact published yamlgraph release that
carries FR-1073 and FR-939; the enforcement names it in the FR before
this brief runs, and the commands below run against an isolated
installation of that release, not against this checkout's editable
install.

- Before the edit, record the complete output of
  `yamlgraph graph lint graph.yaml` (digest checkout) in the report;
  after the edit, run the identical command and record it. After the
  edit no E601, W013, W017 or W022 may remain (judgement AC-07).
- `yamlgraph graph validate graph.yaml`
- Compile check with the collector bound:
  `yamlgraph graph info graph.yaml --tool collect=sources/hn_rss.tool.yaml`
  (or the equivalent `load_graph_config` + `compile_graph` one-liner
  the FR-1122 tests use); it must report the `_map_analyze_all_account`
  and `_map_analyze_all_join` nodes.
- `python -m pytest tests -q` in the digest checkout — the FR-1122
  witnesses (flat prompt rendering, nested skip versus strict, timeout,
  overflow, typed reporting, parsed concurrency) must pass.
- Live smoke: **not in this run.** The operator authorised one manual
  `workflow_dispatch` on 2026-09-27 (judgement Q-1, recorded in the
  FR); it runs after merge, from GitHub Actions, and its run id and
  `Analysed N of M` line go into the FR's implementation record. The
  adapter records "smoke deferred to the authorised post-merge
  workflow_dispatch" in its validation section.

**Prior art:** FR-1122 (governing FR; this brief executes its D-1 and
D-2 surfaces); FR-1073 H-2 row 10 (the same edit on this repository's
`examples/daily_digest/graph.yaml`); FR-1113 (`meta_map`, the reference
graph for the declared keys); FR-1121 digest brief (must be applied
first); FR-904 (nothing here names a source).
