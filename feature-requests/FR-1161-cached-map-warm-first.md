# Feature Request: FR-1161 `cached_map` Node: Warm-First Map Dispatch for Prompt Caching

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Requested:** 2026-11-13
**First consumer / first event:** game-engine's library describe maps
(`workflows/library/library.yaml`: `describe_chars`, `describe_places`,
`redo_chars`, `redo_places`, 9 to 140 items per book, provider anthropic).
Each branch sends the same system prompt (`describe_character.yaml`,
about 5.9k characters) plus one item. The first event: the operator marks
that system prompt `cache: true` and changes `describe_chars` from
`type: map` to `type: cached_map`; the next book run's `--token-usage`
shows about one prefix of cache writes and N − 1 prefixes of cache reads,
where today a cold parallel map at the default width writes up to eight.
The operator's request, 2026-11-13: "plan the cached map as a new node -
implementation differs from base map. merging a potential follow-up, but
first implementation stand alone. include example in the fr scope."
**Research:** [FR-1155.research.md § Map fan-out spike](FR-1155.research.md)
(run `2a47aea8`, raw `usage_metadata` per call) and
[FR-1155 § Follow-up: warm-first map dispatch](FR-1155-prompt-cache-tokens-in-token-usage.md),
plus the in-body dispositioned alternatives table (§ Alternatives
Considered). `is_this_a_graph`: No -- compiler dispatch wiring; no model
stage is added. The example graph and prompt go through `scripts/author.sh`.
**Prior art:**
[FR-1155](FR-1155-prompt-cache-tokens-in-token-usage.md) measured the
problem and wrote this follow-up; its cache meters are this FR's witness
instrument, unchanged.
[FR-1158](FR-1158-cached-map-node.md) (REJECTED) used the name
`cached_map` for a persistent per-item result memo. That is a different
mechanism for a different problem: it skipped calls across runs; this FR
makes every call, in a different order, within one run. Its judgement's
core-vs-contrib objection is answered in § Why a core node.
[FR-1159](FR-1159-map-memo-contrib.md) (REJECTED by the operator after
merge) shipped that memo as contrib; FR-1160 (in flight, separate branch)
removes it. Nothing here depends on either.
[FR-1073](FR-1073-map-result-contract.md) is the dispatch → account → join
result contract; this node reuses it unchanged, with one dispatch token
and one accounting pass over all N indices.
[FR-984](FR-984-map-fan-out-max-concurrency.md) made `max_concurrency` cap map
fan-out; the release wave obeys it unchanged.
[FR-1055](FR-1055-anthropic-prompt-cache-blocks-never-reach-api.md) is
how `system_segments` `cache: true` reaches Anthropic as `cache_control`;
unchanged.
[FR-111](FR-111-compiled-graph-cache.md) and the node-level `cache:` key
(`examples/demos/cache`) are
result caches, not provider prompt caches; out of scope.

## Summary

Add a node type `cached_map`. Its YAML is the same as `type: map`. It runs
item 0's worker alone, then fans out items 1..N−1 in parallel, so a worker
whose prompt has a `cache: true` segment writes the provider's prompt
cache once and every later branch reads it. Results, failures, accounting,
verdict and outgoing edges are those of `type: map`. Ships with an example
under `examples/demos/cached_map` and a live witness through a real graph.
Folding the behaviour into `map` (as an option or automatically) is a
follow-up.

## Value Statement

Graph authors who map an Anthropic prompt with a cached shared prefix pay
one cache write per run instead of one per concurrent branch, which turns
caching from a loss (about 1.12× the uncached input cost at N = 9) into a
saving (about 0.2× on Haiku, 0.15× on Sonnet).

## Problem

The FR-1155 spike (12 items, width 8, a 2,841-token cached system block):

| Model | Variant | Writes | Reads | Input cost vs uncached |
|---|---|---|---|---|
| Haiku 5.5 | cold parallel, W = 8 | 8 | 4 | 0.867 |
| Haiku 5.5 | 1 call, then W = 8 | 1 | 11 | 0.199 |
| Sonnet 5.5 | cold parallel, W = 8 | 8 | 4 | 0.851 |
| Sonnet 5.5 | 1 call, then W = 8 | 1 | 11 | 0.154 |

Parallel branches cannot read a cache entry that is still being written,
so a cold map pays about min(W, N) writes. Caching beats no caching only
when $N > W(1.25-r)/(1-r)$, about N > 10 at W = 8. Every cached map of ten
items or fewer at the default width costs more than not caching. Warming
first removes $(W-1)(1.25-r)$ prefix-equivalents per run for about one
call's latency (0.7 to 1.8 s in the spike).

Two things the spike did not prove: it imitated a map with a semaphore
rather than running `type: map`, and it did not show whether the cache is
readable at the first streamed token. This FR's design waits for item 0's
whole worker, so the second question does not arise; the first is closed
by AC-07.

## Ideal Result

An author changes `type: map` to `type: cached_map` and nothing else. The
run's `--token-usage` shows cache writes of about one shared prefix and
reads of about N − 1, the collected results and verdict are identical to
`type: map`'s, and the extra wall time is one worker's latency.

## Why a core node

FR-1158's judgement asked a core primitive for three independent use
cases and found the memo expressible as tools around a plain map. Warm-first
is not expressible that way: the order of `Send`s is compiler wiring, and
there is no node-type plugin hook (FR-1159 § Alternatives). The YAML
workaround (a single-item map before the real map) splits one population
into two dispatches, two verdicts and two collect keys, and the author
must stitch them. Use cases: game-engine's four library maps (two
prompts), any `examples/demos/prompt-caching`-style prompt put under a
map, and the FR-1155 follow-up's automatic mode, which needs this
mechanism to exist before a trigger can switch it on.

## Planned Operations

```yaml
probes:
  - "ls capabilities/CAP-30* and git grep -F REQ-YG-72 — FR-1160 claims CAP-303 / REQ-YG-727; take the next free ids at implementation time"
  - "read map_compiler.compile_map_node and map_contract.make_dispatch_router — the warm and release routers reuse resolve_items and the count check"
  - "grep NodeType.MAP across yamlgraph/ — every map-recognition site must also recognise cached_map (state_builder, state_codegen, node_schema, validators, linter, loop_limits)"
  - "read 4 raw usage_metadata records from the live witness before asserting on token sums (read_raw_output_first)"
branches:
  - "a NodeType.MAP site has no obvious cached_map meaning → treat cached_map exactly as map there and name the site in the FR"
  - "LangGraph runs the release Sends before item 0's branch has committed → stop; the design assumption is wrong, return to judge"
  - "live witness shows more than one prefix of writes → read the raw records; check the cache minimum and the system-segment render before touching code"
  - "authoring adapter fails → fix the route per its README, never author the demo by hand"
delegations:
  - "judge.sh: 1 run, 2 if revisions are disputed"
  - "author.sh: 1 run for examples/demos/cached_map"
  - "outsider.sh: 1 run on the PR"
  - "review.sh: 1 run from another session"
waits:
  - "judge"
  - "live Anthropic witness run"
  - "CI on the PR"
  - "operator merge decision"
commands:
  - scripts/judge.sh feature-requests/FR-1161-cached-map-warm-first.md
  - scripts/author.sh tmp/fr-1161-cached-map-demo-brief.md
  - python -m pytest tests/unit/test_fr1161_cached_map.py -q --no-cov
  - python -m pytest tests/integration/test_fr1161_cached_map_live.py -q --no-cov
  - yamlgraph graph lint examples/demos/cached_map/graph.yaml
  - yamlgraph graph run examples/demos/cached_map/graph.yaml --token-usage
  - python scripts/req_coverage.py --strict
```

## Proposed Solution

### YAML

```yaml
nodes:
  describe:
    type: cached_map          # was: map
    over: "{state.items}"
    as: item
    collect: described
    node:
      type: llm
      prompt: describe        # its system_segments carry cache: true
      state_key: description
```

Every `type: map` key is accepted with the same meaning: `over`, `as`,
`node`, `collect`, `failures`, `flatten_output`, `min_success`, `timeout`,
`max_items`, `on_overflow`. Worker types are those `map` supports.

### Wiring

`yamlgraph/compile/cached_map_compiler.py` builds the worker exactly as
`compile_map_node` does (shared helper extracted from `map_compiler.py`,
no behaviour change) and wires:

```text
<name> (dispatch) ──warm router──▶ _cmap_<name>_warm   (Send, index 0)
                  └─ N = 0 ───────▶ _cmap_<name>_account
_cmap_<name>_warm ──release router──▶ _cmap_<name>_sub (Send, indices 1..N−1)
                  └─ N = 1 ─────────▶ _cmap_<name>_account
_cmap_<name>_sub ──▶ _cmap_<name>_account ──▶ _cmap_<name>_join
```

- `dispatch`, `account` and `join` are FR-1073's `make_dispatch_node`,
  `make_account_node` and `make_join_node`, unchanged: one token, one
  `dispatched = N`, one accounting pass that requires indices 0..N−1.
- `_warm` and `_sub` are the same wrapped worker function registered under
  two node names. The warm router and the release router are
  `make_dispatch_router` generalised to an index range (`[0, 1)` and
  `[1, N)`); both re-resolve `over` and keep its count check.
- Item 0 runs in its own superstep, so the release Sends start only after
  its worker has returned and its result is committed. For a subgraph
  worker this waits for the whole child graph.
- Item 0 failing (exception, timeout, `on_error: skip`) still releases the
  rest; they then run cold. The failure is accounted as in `map`.
- `max_concurrency` applies to the release wave as to any fan-out.
- No provider check, no prompt inspection: the node always warms first.
  On a prompt without a cached segment it costs one worker's latency and
  nothing else.

### Registration

`NodeType.CACHED_MAP`; `NODE_TYPE_HANDLERS`; `node_schema` required-field
check; `validate_map_node`; map recognition in `state_builder`,
`state_codegen`, linter `VALID_NODE_TYPES`, map pattern checks,
`checks_semantic`, `checks_schema._llm_nodes`, `loop_limits`; the
`compile_nodes` map-like metadata path so outgoing edges leave from join.
Each site treats `cached_map` exactly as `map`.

### Documentation and example

- `reference/graph-yaml.md`: a `cached_map` section after `map` with the
  wiring above, the cost table, and when not to use it (no cached segment,
  a non-Anthropic provider, a shared prefix below the model's cache
  minimum).
- `examples/demos/cached_map/` via `scripts/author.sh`: one `cached_map`
  over 4 short items, an Anthropic Haiku prompt whose `system_segments`
  carry a `cache: true` block above the cache minimum, a README and
  `demo-output.log` from a real run with `--token-usage` showing the cache
  read and write lines. Indexed in `examples/README.md`.
- Capability `CAP-304-cached-map-warm-first.yaml` with REQ-YG-728 (ids
  subject to the allocation probe), regenerated `ARCHITECTURE.md`,
  changelog fragment `type: feat`.

### Tests

Unit (`tests/unit/test_fr1161_cached_map.py`, offline, patched
`execute_prompt` and Python workers, sync and async invocation):

1. Order: a recording worker shows item 0 returned before any other item
   started, for N = 5 and `max_concurrency` 8.
2. Parallelism kept: items 1..N−1 overlap (peak in-flight > 1 with a
   barrier), and `max_concurrency: 2` caps the release wave at 2.
3. Same result as `map`: the same graph with `type: map` and
   `type: cached_map` yields equal `collect`, failures and `MapVerdict`
   (counts, met) for a mix of successes and one failure.
4. Item 0 fails: the other N − 1 still run; the verdict counts the failure;
   `min_success` 1.0 fails the join, `min_success: 0.5` passes.
5. N = 0 and N = 1: no release Sends; verdict as in `map`.
6. Subgraph worker: item 0's whole child graph finishes before item 1
   starts.
7. Topology: compiled node names are `<name>`, `_cmap_<name>_warm`,
   `_cmap_<name>_sub`, `_cmap_<name>_account`, `_cmap_<name>_join`, and a
   following edge leaves from `_cmap_<name>_join`.
8. Lint: `yamlgraph graph lint` accepts a `cached_map` graph and reports
   the same missing-field errors `map` reports.

Live (`tests/integration/test_fr1161_cached_map_live.py`, skipped without
`ANTHROPIC_API_KEY`, Haiku): two graphs over the same N = 4 items, one
`type: map`, one `type: cached_map`, each with a fresh random nonce at the
top of its cached system segment so neither reads the other's cache. With
P the per-call prefix size read from the raw records:

- `type: map` writes more than 1.5 P (several branches wrote);
- `type: cached_map` writes at most 1.5 P and reads at least 2.5 P.

## Acceptance Criteria

- [ ] AC-01: `type: cached_map` with the YAML of an existing `type: map`
  node compiles and runs; `yamlgraph graph lint` accepts it and reports
  the same missing-field errors as `map`.
- [ ] AC-02: Unit test 1: item 0's worker returns before any other item's
  worker starts (sync and async invocation).
- [ ] AC-03: Unit test 2: items 1..N−1 run concurrently, and
  `max_concurrency: 2` caps them at 2 in flight.
- [ ] AC-04: Unit test 3: `collect`, failures and `MapVerdict` equal those
  of the same graph with `type: map`.
- [ ] AC-05: Unit tests 4 and 5: item 0's failure releases the rest; N = 0
  and N = 1 behave as `map`.
- [ ] AC-06: Unit tests 6, 7 and 8 pass (subgraph worker order, topology
  and following edge, lint).
- [ ] AC-07: The live witness passes, and four raw `usage_metadata` records
  from it are quoted in this FR with the cache fields, before the
  thresholds are fixed.
- [ ] AC-08: `examples/demos/cached_map` exists, authored via
  `scripts/author.sh` (`tmp/draft-authoring-report.md` recorded), lints,
  and its `demo-output.log` comes from a real run showing cache read and
  write tokens.
- [ ] AC-09: `reference/graph-yaml.md` documents `cached_map`; the
  capability, REQ, `ARCHITECTURE.md`, `examples/README.md` index and
  changelog fragment are added; `python scripts/req_coverage.py --strict`
  passes.
- [ ] AC-10: No change to `type: map` behaviour: the existing map test
  suites (FR-1073, FR-984, FR-1113, FR-1153) pass unchanged.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| `warm_first: true` option on `map` | Deferred to the follow-up the operator named: first a standalone node, then merge. |
| Automatic warming in `map` (Anthropic + `cache: true` + N ≥ 2 + prefix ≥ minimum) | Deferred to the same follow-up; it needs this mechanism and a static cache-segment predicate that does not exist yet. |
| One superstep, branches > 0 wait on an event set by item 0 (FR-1155 follow-up's sketch) | Rejected: waiting branches hold `max_concurrency` slots, so item 0 can be starved when it is not in the first wave; it also needs cross-branch shared state. The two-superstep wiring above keeps FR-1073's single token, which was the sketch's reason to avoid two supersteps. |
| Release at item 0's first streamed token | Rejected: unmeasured whether the cache is readable then, and the map wrapper does not stream. Whole-worker wait is the spike's measured `warm8` variant. |
| YAML-only: a one-item map before the real map | Rejected: two dispatches, two verdicts, two collect keys for one population; authors must stitch results and thresholds. |
| Warm with a synthetic call (no real item) | Rejected: costs one extra call; the first real item warms for free. |
| Name `warm_map` instead of `cached_map` | Open for the judge. `cached_map` is the operator's term; FR-1158's use of it is rejected, and the reference section states the prompt-cache meaning. |
| Contrib / plugin node type | Rejected: no plugin hook exists; adding one is more core surface than this node. |

## Related

- [FR-1155.research.md § Map fan-out spike](FR-1155.research.md)
- `examples/demos/prompt-caching/` — the `system_segments` `cache: true` pattern.
- `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/map_contract.py`.
- game-engine `workflows/library/library.yaml` — first consumer.
