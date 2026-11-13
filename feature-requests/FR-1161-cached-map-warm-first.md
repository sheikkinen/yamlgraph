# Feature Request: FR-1161 `cached_map` Node: Warm-First Map Dispatch for Prompt Caching

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved by operator overrule (2026-11-13). Judge rounds 1 and
2 REJECTED ([judgement](FR-1161-cached-map-warm-first.judgement.md)).
Round 1's R-1..R-6 and round 2's R-2/R-3 are folded below. Round 2's R-1
(the three-use-case bar for a framework primitive) is unmet and is
overruled by the operator: "judgement is advisory. overruled. enforce".
Implemented on `feat/fr-1161-warm-first-map` (§ Implementation Status).
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

Add a node type `cached_map`. Its YAML is the same as `type: map`. It
freezes the item population at dispatch, runs item 0's worker alone, then
fans out items 1..N−1 in parallel from the frozen snapshot. For a cold
cache and a byte-identical eligible prefix, the target is one prefix of
cache writes and N − 1 prefixes of reads, where a cold parallel map writes
up to min(W, N). `cached_map` changes ordering only; it memoizes nothing.
Results, failures, accounting, verdict and outgoing edges follow the
`type: map` contract (§ Parity). Ships with an example under
`examples/demos/cached_map` and a bounded live witness. Folding the
behaviour into `map` (as an option or automatically) is a follow-up.

## Value Statement

Graph authors who map an Anthropic prompt with a cached shared prefix pay,
on a cold run, about one cache write instead of one per concurrent branch.
In the measured N = 12, W = 8 case the input cost fell from 0.867× to
0.199× of uncached on Haiku and from 0.851× to 0.154× on Sonnet. This is
an observed target, not a guarantee: an already warm cache writes zero,
and differing prefixes or expiry write more.

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

An author changes `type: map` to `type: cached_map` and nothing else. On a
cold run with an identical eligible prefix, `--token-usage` shows cache
writes of about one shared prefix and reads of about N − 1; results and
verdict satisfy the map contract (§ Parity); the extra wall time is one
worker's latency.

## Why a core node

Warm-first is not expressible as tools around a plain map: the order of
`Send`s is compiler wiring, and there is no node-type plugin hook (FR-1159
§ Alternatives). The YAML workaround (a single-item map before the real
map) splits one population into two dispatches, two verdicts and two
collect keys, and the author must stitch them.

Committed evidence (R-1), counting only concrete workloads:

| Workload | Shared-prefix contract | Gap in `type: map` |
|---|---|---|
| game-engine `library.yaml` `describe_chars` (and its `redo_chars` re-run, same prompt, not counted separately) | `prompts/describe_character.yaml` system text, about 5.9k characters, identical per item; item in the user turn | A cold map at width 8 writes the prefix up to 8 times; caching costs more than not caching below about N = 10 |
| game-engine `library.yaml` `describe_places` (and `redo_places`, not counted separately) | `prompts/describe_place.yaml` system text, about 1.7k characters; whether it reaches the model's cache minimum is unmeasured | Same; if below the minimum, `cached_map` costs one worker's latency and saves nothing |

That is one consumer repository with two prompts, below the doctrine's
three-use-case bar for a framework primitive (`judge-fr/doctrine.md`).
The demo and the FR-1155 automatic-mode follow-up are not counted.

### Operator decisions (2026-11-13)

1. **Standalone node despite the evidence gap.** Asked "Keep the
   standalone `cached_map` node anyway?", the operator answered: "Yes,
   standalone node (operator override, recorded in FR)". This is a
   product decision by the operator, recorded here, not a judge waiver;
   the evidence above stands as stated. Merging into `map` remains the
   named follow-up.
2. **Paid-run ceiling.** "$1 total, max 3 witness runs" covers the live
   witness, the demo run and all retries (§ Live witness protocol).
3. **Overrule of round 2's verdict.** Round 2 held that the override in
   decision 1 does not satisfy the judge rubric's three-use-case bar. A
   search of yamlgraph and game-engine found no third eligible workload:
   book-setup `settle` (about 3.7k chars), library `invent_look` (about
   2.6k) and dungeon_master `intents` (about 3k) sit near or below the
   cache minimum. The operator answered: "judgement is advisory.
   overruled. enforce". Scope is the plan below with round 2's R-2 and
   R-3 folded; no doctrine is changed.

## Planned Operations

```yaml
probes:
  - "ls capabilities/CAP-30* and git grep -F REQ-YG-72 — FR-1160 claims CAP-303 / REQ-YG-727; take the next free ids at implementation time"
  - "read map_compiler.compile_map_node and map_contract.make_dispatch_node/make_dispatch_router — the cached_map dispatch node writes the snapshot; both routers read it"
  - "grep NodeType.MAP across yamlgraph/ — every map-recognition site must also recognise cached_map (state_builder, state_codegen, node_schema, validators, linter, loop_limits)"
  - "read the 4 raw cached_map usage_metadata records and the map control's records before computing totals (read_raw_output_first); thresholds are fixed in § Live witness protocol, not after the run"
branches:
  - "a NodeType.MAP site has no obvious cached_map meaning → treat cached_map exactly as map there and name the site in the FR"
  - "LangGraph runs the release Sends before item 0's branch has committed → stop; the design assumption is wrong, return to judge"
  - "live witness fails its gate → read the raw records; check the cache minimum and the system-segment render; if the planned gate itself is wrong, amend the FR and re-judge — never tune thresholds until green"
  - "spend ceiling ($1 or 3 runs) reached → stop; AC-07/AC-08 stay unmet and are reported"
  - "authoring adapter fails → fix the route per its README, never author the demo by hand"
delegations:
  - "judge.sh: 2 runs (first REJECTED; this re-judgement)"
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
  - python -m pytest tests/unit/test_fr1073_map_result_contract.py tests/unit/test_fr1073_ocr_skip_report.py tests/unit/test_fr984_map_max_concurrency.py tests/unit/test_fr1113_meta_map.py tests/unit/test_fr1153_timeout_runnable_context.py tests/unit/test_map_node.py tests/unit/test_map_node_timeout.py tests/unit/test_compile_graph_map.py tests/unit/test_state_builder_map.py tests/unit/test_linter_patterns_map.py tests/unit/test_fr1119_lint_map_fields.py tests/unit/test_fr939_map_overflow_policy.py tests/unit/test_fr944_map_to_map_index.py tests/unit/test_map_flatten_output.py tests/unit/test_conditional_edge_to_map.py -q --no-cov
  - python -m pytest tests/integration/test_fr1161_cached_map_live.py -q --no-cov -s
  - yamlgraph graph lint examples/demos/cached_map/graph.yaml
  - yamlgraph graph run examples/demos/cached_map/graph.yaml --token-usage
  - ruff check yamlgraph/ tests/ && ruff format --check yamlgraph/ tests/
  - lint-imports
  - python scripts/req_coverage.py --strict
  - CI-mirror Docker run of pytest tests/unit -m "not slow" -n auto (the Windows host is not the binding gate)
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
no behaviour change to `map`) and wires:

```text
<name> (dispatch + snapshot) ──warm router──▶ _map_<name>_warm  (Send, index 0)
                             └─ N = 0 ───────▶ _map_<name>_account
_map_<name>_warm ──release router──▶ _map_<name>_sub  (Send, indices 1..N−1)
                 └─ N = 1 ─────────▶ _map_<name>_account
_map_<name>_sub ──▶ _map_<name>_account ──▶ _map_<name>_join
```

- **Names (R-4).** Registered node names keep the `_map_<name>_*` prefix
  that the shared wrapper, failure, account and join factories already use
  as diagnostic identifiers (`map_compiler.py:157`; `map_contract.py:51,203,217`).
  Only `_map_<name>_warm` is new. Registered names and diagnostic names
  therefore match; no factory is parameterized for naming.
- `account` and `join` are FR-1073's `make_account_node` and
  `make_join_node`, unchanged: one token, one `dispatched = N`, one
  accounting pass that requires indices exactly 0..N−1.
- `_warm` and `_sub` are the same wrapped worker function registered under
  two node names.
- `max_concurrency` applies to the release wave as to any fan-out.
- No provider check, no prompt inspection: the node always warms first.
  On a prompt without a cached segment it costs one worker's latency and
  nothing else.

### Dispatch-time snapshot (R-2)

A plain map's router copies the current state into every `Send`
(`map_contract.py:151-170`). Re-resolving `over` after the warm superstep
would see item 0's result already appended to `collect`; if `over` reads
that channel the population changes, and a count check misses a
same-length substitution. Later workers would also see post-warm state.
So `cached_map` freezes everything at dispatch:

- **Owner.** The `cached_map` dispatch node (a thin wrapper around
  `make_dispatch_node`) resolves `over` once, applies `max_items` /
  `on_overflow` (an overflow raise happens here, before any worker runs),
  and writes one record to a private channel
  `_cached_map_snapshot[<name>]`.
- **Typed transport.** The record is a Pydantic envelope
  `CachedMapSnapshot{dispatch: str, items: list[Any], inputs: dict[str, Any]}`
  in `yamlgraph/models/map_results.py`. It is stored as a shallow field
  mapping (`{"dispatch": s.dispatch, "items": s.items, "inputs": s.inputs}`),
  never `model_dump()`: contained items and inputs keep their Python
  values (Pydantic models stay models), exactly as the plain map's `Send`
  passes them (round 2 R-2). Checkpoint serialization is the existing
  one. `inputs` is the dispatch-time state minus
  execution bookkeeping (`_map_open`, `_map_accounting`, `_map_verdict`,
  `_cached_map_snapshot`). No process-global event, no mutable compiler
  closure.
- **Readers.** Both routers build `Send`s only from the snapshot:
  `{**inputs, <as>: items[i], _map_index: i, _map_dispatch: dispatch}`.
  Neither router reads `over` or current state. The release wave therefore
  gets the same items, indices, token and common inputs as item 0.
- **Lifetime.** The channel uses `merge_map_open`'s open/close semantics:
  dispatch opens `{<name>: record}`; the cached_map account step closes it
  with `{<name>: None}` in the same update that closes `_map_open`. A
  re-entry dispatches with a fresh token and a fresh snapshot; an
  unclosed snapshot on re-entry raises `MapAccountingError` as an
  overlapping `_map_open` does.
- **State.** `state_builder` adds `_cached_map_snapshot: Annotated[dict, merge_map_open]`
  for `cached_map` nodes, alongside the map channels. The checkpoint holds
  one extra copy of the inputs while the dispatch is open; documented in
  the reference.

### Release after a settled warm outcome (R-3)

Item 0 runs in its own superstep. Release happens after its wrapped
outcome has settled and committed: success, classified failure, tolerated
skip, or wrapper timeout. Successful workers, including whole subgraph
child graphs, finish before release. A timed-out worker's thread is not
stopped by the existing wrapper (`Future.result(timeout=...)`, shutdown
`wait=False`, `map_compiler.py:103-125`), so its background work may
overlap the release wave. Timeout behaviour is unchanged; cancellation is
out of scope. After any warm outcome the rest still run, cold if item 0
did not write the cache.

### Parity (R-4)

`cached_map` satisfies the `map` result contract for equivalent
deterministic worker outcomes: `collect` content ordered by `_map_index`,
failures (index, type, message, tolerated) and `MapVerdict`
(counts, policy, met) equal those of the same graph with `type: map`, with
per-run dispatch ids normalized consistently. Missing, duplicate or
misattributed indices are never normalized away. Ordering does not make
stochastic LLM output or side-effect timing identical; the reference says
so.

### Registration

`NodeType.CACHED_MAP`; `NODE_TYPE_HANDLERS`; `node_schema` required-field
check; `validate_map_node`; map recognition in `state_builder`,
`state_codegen`, linter `VALID_NODE_TYPES`, map pattern checks,
`checks_semantic`, `checks_schema._llm_nodes`, `loop_limits`; the
`compile_nodes` map-like metadata path so outgoing edges leave from join.
Each site treats `cached_map` exactly as `map`, plus the snapshot channel
in `state_builder` / `state_codegen`. The published
`yamlgraph/schemas/graph-v1.json` does not enumerate node types (`type`
is a free string defaulting to `llm`), so it needs no change; a test
asserts that it still validates a `cached_map` graph.

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
`execute_prompt` and Python workers, sync and async invocation, every
test marked with the allocated REQ; bounded `threading.Event` waits only):

1. Order: a recording worker shows item 0 returned before any other item
   started, for N = 5 and `max_concurrency` 8.
2. Parallelism kept: items 1..N−1 overlap (peak in-flight > 1 with a
   bounded barrier), and `max_concurrency: 2` caps the release wave at 2.
3. Parity (§ Parity): the same graph with `type: map` and
   `type: cached_map` gives equal normalized `collect`, failures and
   `MapVerdict` for a mix of successes and one failure.
4. Warm outcome truth table (round 2 R-3), N = 4, item 0 parameterized,
   items 1..3 succeed:
   - exception or wrapper timeout: `succeeded=3, tolerated=0, failed=1,
     accepted=3`; `min_success: 1.0` unmet, `0.5` met;
   - tolerated skip: `succeeded=3, tolerated=1, failed=0, accepted=4`;
     both met.
   Every case asserts release, indices exactly 0..3, one token, the
   committed verdict and snapshot closure; an unmet policy raises at join
   only after accounting commits. `compute_verdict` is unchanged. The
   timeout worker waits on an event the test sets in teardown, so no work
   leaks.
5. N = 0 and N = 1: no release Sends; verdict as in `map`.
6. Subgraph worker: item 0's whole child graph finishes before item 1
   starts.
7. Topology: compiled node names are `<name>`, `_map_<name>_warm`,
   `_map_<name>_sub`, `_map_<name>_account`, `_map_<name>_join`;
   diagnostics in failure records name `_map_<name>_*`; a following edge
   leaves from `_map_<name>_join`.
8. Snapshot, collect-as-over: `over` and `collect` are the same
   append-reduced channel. Exactly the original N item identities run,
   each once; one token; indices exactly 0..N−1; no count-mismatch raise.
9. Snapshot, common input: a worker reads a state variable that item 0's
   result changes through collection; every release worker sees the
   dispatch-time value.
10. Re-entry: the graph loops back to the same `cached_map` twice with
    different populations; the second dispatch uses a fresh token and
    only its own items; the snapshot channel is closed after each account.
11. Cap and overflow: `max_items` truncates before the warm worker;
    `on_overflow: error` raises at dispatch with zero workers started.
12. Schema, load and state: `node_schema` / `validate_map_node` reject a
    `cached_map` missing `over`, `as`, `node` or `collect` with `map`'s
    messages; inferred state carries `collect`, the failures channel, the
    map channels and `_cached_map_snapshot`; `state_codegen` output for a
    `cached_map` graph compiles; `graph-v1.json` validates it.
13. Composition: `map → cached_map` and `cached_map → map` in one graph
    each produce both verdicts with independent tokens.
14. Lint: `yamlgraph graph lint` accepts a `cached_map` graph and reports
    the same missing-field errors `map` reports.
15. Type preservation (round 2 R-2): items are Pydantic models and a
    common input is a Pydantic model; a Python worker reads their
    attributes and asserts their concrete types in the warm and release
    calls; outputs equal the plain map's after dispatch-id normalization.

### Live witness protocol (R-5)

`tests/integration/test_fr1161_cached_map_live.py`, skipped without
`ANTHROPIC_API_KEY`:

- Model `claude-haiku-5-5` (the FR-1155 spike's Haiku id; a different id
  is an FR amendment), `max_tokens: 16`, N = 4, `max_concurrency: 4` on both the
  graph and the invocation.
- Two graphs over the same 4 items: a control `type: map` and a
  `type: cached_map`. Each variant's cached system segment is
  byte-identical across its own 4 calls, above the model's cache minimum,
  and starts with its own fresh random nonce so neither reads the other's
  cache or a previous run's.
- **P** is the cached_map warm call's write, by FR-1155's rule
  `max(cache_creation, ephemeral_5m + ephemeral_1h)`. Missing or zero P
  fails the witness; no threshold is derived from it.
- **Gate (cached_map only):** the first call writes P and reads 0; total
  writes in `[P, 1.5 P]`; total reads ≥ `2.5 P`.
- **Control:** the ordinary map's writes and reads are recorded as
  context. `writes > 1.5 P` is expected but not asserted: concurrency
  bounds width; it does not guarantee overlapping misses at the provider.
- The test prints all 4 cached_map raw `usage_metadata` records and the
  control's records and totals; they are read and quoted in this FR before
  the aggregate verdict is reported.
- **Spend ceiling (operator, 2026-11-13):** $1 total and at most 3 witness
  runs, covering this test, the demo run and every retry. One run is
  8 Haiku calls of about a 3k-token prefix plus 16 output tokens
  (estimated well under $0.05). Missing credentials, a reached ceiling or
  a skipped test leave AC-07 unmet. If observations show the gate itself
  is wrong, amend the FR and re-judge; never tune until green.

## Acceptance Criteria

- [x] AC-01: `type: cached_map` with the YAML of an existing `type: map`
  node compiles and runs; unit tests 12 and 14 pass (schema, load, state,
  codegen, published schema, lint).
- [x] AC-02: Unit test 1: item 0's worker returns before any other item's
  worker starts (sync and async invocation).
- [x] AC-03: Unit test 2: items 1..N−1 run concurrently, and
  `max_concurrency: 2` caps them at 2 in flight.
- [x] AC-04: Unit test 3: normalized parity per § Parity.
- [x] AC-05: Unit tests 4 and 5: every warm outcome (exception, tolerated
  skip, timeout) releases the rest with full accounting; N = 0 and N = 1
  behave as `map`.
- [x] AC-06: Unit tests 6, 7, 11 and 13 pass (subgraph order, topology
  and diagnostic names, cap/overflow before warm, composition).
- [x] AC-07: The live witness passes the § Live witness protocol gate
  within the spend ceiling; the 4 cached_map raw records and the control's
  totals are quoted in this FR.
- [x] AC-08: `examples/demos/cached_map` exists, authored via
  `scripts/author.sh` (`tmp/draft-authoring-report.md` recorded), lints,
  and its `demo-output.log` comes from a real run (inside the ceiling)
  showing cache read and write tokens.
- [x] AC-09: `reference/graph-yaml.md` documents `cached_map` (wiring,
  snapshot, timeout overlap, parity limits, when not to use it); the
  capability, REQ, `ARCHITECTURE.md`, `examples/README.md` index and
  changelog fragment are added; `python scripts/req_coverage.py --strict`,
  `ruff check`, `ruff format --check` and `lint-imports` pass.
- [x] AC-10: No change to `type: map` behaviour: the existing-suite
  command in § Planned Operations passes unchanged, and the CI-mirror
  unit run is green.
- [x] AC-11: Unit tests 8, 9, 10 and 15 pass (snapshot: collect-as-over,
  common input, re-entry, type preservation).
- [ ] AC-12: This FR records implementation status and decisions, and a
  diary entry with a `Seed:` is added under `docs/diary/`.

## Implementation Status (2026-11-13)

Commits: RED `2cc93b23`, GREEN `3d07d1d2`, node-type inventory tests
`383e2a8e`, live witness `a6199407`, then demo, docs and this status.

**Decisions and deviations**

- `compile_map_node` was split into `_create_sub_node` and `_wire_map` so
  that `cached_map` reuses the same worker, `wrap_for_reducer` and
  `resolve_items`. `_wire_map` passes to `wire_cached_map` in
  `yamlgraph/compile/cached_map_compiler.py` when the type is
  `cached_map`. The node compiler registers `cached_map` with the same
  handler as `map`.
- The snapshot is built through `CachedMapSnapshot` and stored as
  `dict(snapshot)` (shallow), so Pydantic items and inputs keep their
  types (test 15).
- Every recognition site named in § Proposed Solution treats `cached_map`
  as `map`, plus the snapshot channel. Two existing inventory tests
  (`test_constants`, `test_node_type_registry`) list the new type.
- Line-keyed allowlists shifted by the edits: `docs/confessions.md`
  (CONF-001/008/044, 221, 235–237) and `scripts/hedging_check.py` were
  updated to the new line numbers. Module-map budget 302 → 304.
- The test harness's `consume` tool originally read rows without `v`
  (seed rows in test 8, child output in test 6); it now skips them. This
  was a defect in the test harness, not in the node.
- The live witness worker is a Python tool that calls `create_llm`
  directly, so it can return each call's raw `usage_metadata`. The demo
  covers the `type: llm` sub-node path.

**Live witness (AC-07), run 1 of 3, raw records**

```text
map[0..3] input_token_details: cache_read 0, cache_creation 0, ephemeral_5m_input_tokens 2940 (each of 4)
map totals: writes=11760 reads=0
cached_map[0]: cache_read 0, cache_creation 0, ephemeral_5m_input_tokens 2946
cached_map[1]: cache_read 2946, ephemeral_5m_input_tokens 0
cached_map[2]: cache_read 2946, ephemeral_5m_input_tokens 0
cached_map[3]: cache_read 2946, ephemeral_5m_input_tokens 0
cached_map totals: writes=2946 reads=8838
```

P = 2946. Gate: the first call wrote P and read 0; writes 2946 ∈ [P, 1.5P];
reads 8838 ≥ 2.5P = 7365. Passed. Things a generated dump would not show:
`cache_creation` is 0 on every write, which is why FR-1155's max rule is
needed, and `output_token_details.reasoning` was 0 on `map[0]` but 16 on
the other seven calls (unexplained). The control wrote the prefix once
per item: 4 writes and 0 reads at width 4.

**Demo (AC-08), run 2 of 3.** `scripts/author.sh` authored
`examples/demos/cached_map` (`tmp/draft-authoring-report.md`). The
adapter's final check exited 65 because the report lists paths with
Windows backslashes; the files exist. The agent's single run failed
before any LLM call: with a state-only default, `{state.items}` resolved
to the state dict's `items` method (`got builtin_function_or_method`).
The agent moved the default to graph-level `variables`. One real run
followed (`demo-output.log`): `35272 in / 44 out (4 calls), 26400 cache
read, 8800 cache write`, labels for all 4 items, no failures.
Total paid spend is about $0.06 of the $1 ceiling, with 2 of 3 runs used.

**Deviation (operator decision, 2026-11-13): authoring-proof path
separators.** The FR-767 commit backstop (`scripts/check_authoring_proof.py`)
also rejected the demo commit: it searches the report for each staged
path as written, and the report uses `\`. The operator chose to fix this
inside FR-1161, not in a separate FR. Both checks now replace `\` with
`/` when they read the report. In `scripts/author.sh` the extraction
moved into `artifact_candidates()` so a test can call it. Witness:
`tests/unit/test_fr1161_authoring_proof_separators.py` (RED before the
fix, GREEN after; REQ-YG-423).

**Follow-ups (not in scope):** a `{state.<name>}` expression should not
resolve to a dict method name such as `items`, `keys` or `values`; this
returns a plausible wrong answer.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| `warm_first: true` option on `map` | Deferred to the follow-up the operator named: first a standalone node, then merge. |
| Automatic warming in `map` (Anthropic + `cache: true` + N ≥ 2 + prefix ≥ minimum) | Deferred to the same follow-up; it needs this mechanism and a static cache-segment predicate that does not exist yet. |
| One superstep, branches > 0 wait on an event set by item 0 (FR-1155 follow-up's sketch) | Rejected: waiting branches hold `max_concurrency` slots, so item 0 can be starved when it is not in the first wave; it also needs cross-branch shared state. The two-superstep wiring above keeps FR-1073's single token, which was the sketch's reason to avoid two supersteps. |
| Release at item 0's first streamed token | Rejected: unmeasured whether the cache is readable then, and the map wrapper does not stream. Whole-worker wait is the spike's measured `warm8` variant. |
| YAML-only: a one-item map before the real map | Rejected: two dispatches, two verdicts, two collect keys for one population; authors must stitch results and thresholds. |
| Warm with a synthetic call (no real item) | Rejected: costs one extra call; the first real item warms for free. |
| Name `warm_map` instead of `cached_map` | Rejected: `cached_map` is the operator's term. The reference states it means prompt-cache ordering, not result memoization (FR-1158's rejected meaning). |
| Contrib / plugin node type | Rejected: no plugin hook exists; adding one is more core surface than this node. |

## Related

- [FR-1155.research.md § Map fan-out spike](FR-1155.research.md)
- `examples/demos/prompt-caching/` — the `system_segments` `cache: true` pattern.
- `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/map_contract.py`.
- game-engine `workflows/library/library.yaml` — first consumer.
