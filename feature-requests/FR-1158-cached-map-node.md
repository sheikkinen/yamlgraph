# Feature Request: FR-1158 `cached_map` Node Type: Map With a Per-Item Persistent Memo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Rejected ([judgement](FR-1158-cached-map-node.judgement.md)). Operator decision 2026-11-13: accept the contrib classification and ship the FR-1116 memo as `yamlgraph/contrib/map_memo` instead; re-filed as [FR-1159](FR-1159-map-memo-contrib.md).
**Requested:** 2026-11-13
**First consumer / first event:** the new `examples/demos/cached_map`
demo (in scope). Its second run over an unchanged item list makes zero
worker calls and returns the same `collect` list as the first run. The
next consumers are `meta_map` and `person_profile_census`. They currently
wire the memo by hand as split → map → merge tool nodes (FR-1116,
FR-1120). Migrating them is a follow-up FR, not this one.
**Research:** in-body dispositioned alternatives table (§ Alternatives Considered).
**Prior art:**
[FR-1116](FR-1116-map-memo-file-corpus.md) is the memo store this node takes
into core. FR-1116 is a pair of example-local `tool_call` nodes around a
plain map, and it cannot ship in the distribution because `examples*` is
excluded (pyproject `[tool.setuptools.packages.find]`).
[FR-1120](FR-1120-census-map-memo.md) added opaque caller versions. This FR
does not carry those over: item identity is the item's own content
(D3).
[FR-1073](FR-1073-map-result-contract.md) is the dispatch/account/join
result contract this node reuses unchanged. That covers `MapFailure`,
`MapAccounting`, `MapVerdict`, `compute_verdict`, and the account and join
node factories.
FR-032 (no file; `CacheConfig` in `yamlgraph/models/guard_schema.py`) is LangGraph's per-node `cache:` policy. It
is whole-node, in-process, and TTL-based, and it already owns the `cache:`
key, so this node's settings live under `memo:`.
[FR-232](FR-232-race-node-type.md) is the checklist precedent for adding a
node type.

## Summary

Add a standalone node type, `cached_map`. It behaves like `map`, with one
difference: an item whose result is already in a SQLite memo, for the same
computation, does not run its worker again. Its stored result is put back
into `collect` at its original position. Only the missed items fan out.
Any new successes are written to the store before the `min_success`
verdict is enforced. The verdict is computed over the whole population, so
reused items count as successes.

## Value Statement

A graph author who re-runs a map over a corpus that changes slowly pays
only for the items that changed. Today the same behaviour needs three
hand-wired example tools.

## Problem

Re-running a map over N items calls the worker N times, even when only one
item changed. FR-1116 proved a memo solves this. Its shape, though, is two
`tool_call` nodes around a map with `min_success: 0`, plus a bespoke
merge, and it is example-local. Every new consumer copies that wiring.
Because the tool lives under `examples/`, core graphs and installed users
cannot use it at all.

## Ideal Result

The author writes `type: cached_map` with a `memo: {store: ...}` block
instead of `type: map`. Unchanged items are never recomputed. Changing the
worker's configuration, its prompt file, its resolved variables, or any
declared input invalidates every entry. Changing one item invalidates only
that item. Results, failures, and the verdict are exactly what `map` would
produce if every item had been executed and the reused items had succeeded
as before.

## Planned Operations

```yaml
probes:
  - "done: Explore subagent over map_compiler/map_contract/node_compiler/state_builder/linter/map_memo"
branches:
  - "base map behaviour changes in any existing map test → stop; refactor is wrong"
  - "judge round cap reached → re-file shorter FR"
delegations:
  - "judge.sh: 1 run"
  - "author.sh: 1 run (example graph + prompt)"
waits:
  - "judge"
  - "CI"
commands:
  - python -m pytest tests/unit/test_fr1158_cached_map.py -q --no-cov
  - python -m pytest tests/unit -q --no-cov -k "map" -n auto
  - python scripts/req_coverage.py --strict
  - lint-imports
  - "clean CI-mirror container fast suite on the committed HEAD (FR-1157 recipe)"
  - yamlgraph graph lint examples/demos/cached_map/graph.yaml
  - "yamlgraph graph run examples/demos/cached_map/graph.yaml twice (second run: 0 worker calls)"
```

## Proposed Solution

```yaml
nodes:
  summarize:
    type: cached_map
    over: "{state.items}"
    as: item
    node:
      prompt: summarize_item
      state_key: summary
    collect: summaries
    min_success: 0.9
    memo:
      store: outputs/cached_map/memo.sqlite   # required; resolved against cwd
      files: [examples/demos/cached_map/rubric.md]   # optional extra signature files
      inputs: {model: "{state.model}"}         # optional; values resolved like variables
```

**Decisions (binding):**

- **D1 Standalone.** This adds a new `NodeType.CACHED_MAP`, a handler, and
  the module `yamlgraph/compile/cached_map_compiler.py`. The `map`
  compile path, edges, and state are unchanged in behaviour. The only edit
  to `map_compiler.py` is a behaviour-preserving extraction of two helpers
  that both node types call:
  - `create_map_worker(...)`: the worker-type `if/elif` block.
  - `make_item_resolver(...)`: the `over` resolution and FR-939 cap.

  Folding the memo into `map` itself is an explicit follow-up, not this FR.
- **D2 Topology.** `<name>` (lookup) → Send for each miss → `_map_<name>_sub`
  → `_map_<name>_account` → `_map_<name>_store` → `_map_<name>_join`. With
  no misses, lookup routes straight to account. Account and join are the
  unchanged FR-1073 factories, and the node returns `(router, join)`
  metadata, so the existing edge compiler routes `map`-style edges.
  - **Lookup** opens a token with `dispatched = population size`. It
    emits every hit into `collect` as `{"_map_index": i, **payload}` and
    adds a `MapAccounting(outcome="succeeded")` row for each hit.
  - **Misses** are sent with their population `_map_index`.
  - **Account** therefore sees indices `0..N-1`, so the verdict counts the
    whole population (FR-1116 population semantics).
- **D3 Item identity.**
  - The key is the SHA-256 of the item's canonical JSON (sorted keys,
    compact separators, `ensure_ascii=False`, `allow_nan=False`). If an
    item cannot be serialized to JSON, the run fails loudly.
  - `memo.item_files: true` declares that the items are file paths. The
    file's SHA-256 is then the item version, so editing a file invalidates
    that key. Otherwise the version is `""`, because the content is already
    the key.
  - A hit requires a stored row whose version and signature both equal the
    current ones.
- **D4 Signature.** The signature is the SHA-256 of canonical JSON
  containing:
  - `contract: "cached_map/1"`
  - `node`: the authored worker config
  - `prompt`: the SHA-256 of the resolved prompt file, when the worker has
    a `prompt:`
  - `files`: a `{path: sha256}` map for `memo.files`
  - `variables`: the worker's variables resolved against current state,
    excluding the item variable
  - `inputs`: `memo.inputs` resolved against state

  It is computed once per lookup. A missing signature file fails the run.
  Workers that read state outside their `variables` (python, subgraph,
  tool_call) must declare those reads in `memo.inputs`. This is documented,
  not inferred.
- **D5 Failures are not cached.** Only successes are stored. A failed or
  tolerated item misses on every run and re-executes. Its `MapFailure` and
  `errors` entry come from the current execution. Carrying cached failures
  forward (FR-1116 behaviour) is a follow-up.
- **D6 Persist before enforce.** The store node upserts this dispatch's
  executed successes in one `BEGIN IMMEDIATE` transaction and commits.
  Only then does join enforce `min_success`, so an unmet threshold still
  keeps the work done. Successes are attributed through a private append
  channel, `_map_memo_rows`, with one entry per row
  `{map, dispatch, index, key, version, payload}`. The channel is filtered
  by the verdict's dispatch token. Last upsert wins, as in FR-1116.
- **D7 Store schema.**
  - `meta(name PK, value)` with `schema_version = "cached_map/1"`.
  - `memo(key PK, version, signature, payload)`.
  - A missing or zero-byte file means every item misses.
  - Any other schema value, malformed row, or SQLite error raises
    `MapMemoStoreError`.
  - Parent directories are created on the first write.
  - This store is distinct from the FR-1116 store, so the two never share
    a file format.
- **D8 Empty population.** As in `map`, zero items means met. The store is
  not touched.
- **D9 Observability.** `_map_memo: {name: {reused, executed}}`, using a
  merge-by-key reducer, plus one INFO log line from lookup.
- **D10 Supported config.** Supported keys: `over`, `as`, `node`,
  `collect`, `failures`, `min_success`, `timeout`, `flatten_output`,
  `max_items`, `on_overflow`, and `memo`.
  - The FR-939 cap applies to the population, as in `map`.
  - `memo` is a strict Pydantic model with fields `store`, `files`,
    `inputs`, and `item_files`. Unknown keys are rejected.
  - `guards` and `loop_limits` are unsupported (the same classification
    as `map`).
- **D11 Registration surfaces.** Each of these gets a `cached_map` entry:
  - `constants.NodeType`
  - `NODE_TYPE_HANDLERS`
  - `loop_limits` (unsupported)
  - `NodeConfig` (a `memo` field, plus the map required-field check)
  - `validators` (map thresholds and failure keys)
  - linter: `checks.py` allowlist, `patterns/map.py` structural checks,
    `checks_semantic.py`, `checks_schema.py`
  - `state_builder` and `state_codegen` (the map channels plus
    `_map_memo_rows` and `_map_memo`)
  - `schemas/graph-v1.json`
- **D12 Store module.** `yamlgraph/storage/map_memo_store.py` is the
  side-effect layer: hashing, lookup, and upsert.

## Acceptance Criteria

- [ ] AC-01: For the same graph, store, and items, a second invocation in a
  fresh process makes zero worker calls. Its `collect` equals the first
  run's, and `_map_memo[name] == {reused: N, executed: 0}`.
- [ ] AC-02: Changing one item re-executes exactly that item.
  `collect` order matches population order.
- [ ] AC-03: Changing the worker's prompt file, a resolved worker
  variable, a `memo.files` file, or a `memo.inputs` value re-executes
  every item.
- [ ] AC-04: With `item_files: true`, editing one file re-executes only
  that item.
- [ ] AC-05: A failing item is not stored and re-executes on the next run.
  The verdict counts reused items as succeeded; for example, 3 reused + 1
  failed with `min_success: 0.75` is met.
- [ ] AC-06: An unmet `min_success` raises `MapCompletenessError`, and the
  store already holds this run's successes.
- [ ] AC-07: Zero items is met, and no store file is created.
- [ ] AC-08: The topology is lookup → sub → account → store → join, and
  outgoing edges leave from the join.
- [ ] AC-09: Unknown `memo` keys, a missing `memo.store`, or a missing
  map field are rejected by config validation. The linter accepts a valid
  `cached_map` and applies the map structural checks.
- [ ] AC-10: Every existing `map` test passes unchanged.
- [ ] AC-11: `examples/demos/cached_map` is authored via
  `scripts/author.sh`, lints clean, and its second smoke run reports
  `reused == N`.
- [ ] AC-12: `reference/graph-yaml.md` documents the `cached_map` section;
  CAP-302 / REQ-YG-726 are registered; there is a changelog fragment of
  type `feat`.

## Alternatives Considered

| Option | Disposition |
|--------|-------------|
| A. Add `memo:` to `map` itself | Deferred: the operator asked for a standalone first implementation; merging is the follow-up. |
| B. Move FR-1116 `map_memo` tools into core, keep the split/merge wiring | Rejected: keeps three nodes of boilerplate per consumer, which is the cost this FR removes. |
| C. LangGraph `CachePolicy` on the map sub-node | Rejected: in-process and keyed on the full Send state (including the dispatch token), so it never hits across runs. |
| D. Single node that runs workers itself in a thread pool | Rejected: loses Send parallelism, LangGraph concurrency config, and FR-1073 accounting reuse. |
| E. Cache failures too | Deferred (D5): needs a status column and a retry policy decision. |
| is_this_a_graph | A per-item memo is control flow inside a node type, not an LLM stage; the example graph is the graph-shaped deliverable. |

## Related

- `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/map_contract.py`
- `examples/shared/map_memo.py` (FR-1116, unchanged)
- `capabilities/CAP-11-subgraph-map.yaml`
