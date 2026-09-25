# Feature Request: Resumable map — investigation (item identity, versions, result store, chunked scheduling)

**Priority:** HIGH
**Type:** Enhancement (investigation)
**Status:** Proposed
**Effort:** 1.5 days (investigation only; the fix FR is filed from its findings)
**Requested:** 2026-09-25
**First consumer / first event:** the fi-catalog pilot
(`docs/plan-web-toolkit.md` component D) and the next person-profile census
re-run (`examples/demos/person_profile_census`): the second run over the same
subject should pay only for new, changed and previously transient-failed
items. Today every re-run pays for all items.
**Research:** in-body dispositioned alternatives table below, plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §4 (failure model),
§5.1 (eleven existing reuse mechanisms, four graph-local reinventions), §6
(root cause), §6.1–§6.4 (syntax, stores, key/version/node version, component
D), and `docs/plan-web-toolkit.md` component D (L179–243). The FR-890
research route was not run.
**Prior art:** `docs/plan-web-toolkit.md` component D (plan, no FR) — this is
its first FR; D's two named gaps (chunked scheduling, results out of state)
and its `kill -9` witness are adopted.
[FR-936-map-node-hardening.md](FR-936-map-node-hardening.md) (SPLIT) — its
non-overlap contract places `CachePolicy`, Store-backed results, resume and
chunked scheduling outside all four children; this FR is where that work goes.
[032-node-level-caching.md](032-node-level-caching.md) (status says
Implemented) — accepts `cache: {ttl}` and builds a LangGraph `CachePolicy`,
but yamlgraph never passes `cache=` to `compile()`, so the policy is inert;
this FR does not reuse it for maps (a node-level `CachePolicy` on the map
sub-node would also cache failure records).
[FR-985](FR-985-census-coverage-floor-and-population-header.md) (Shelved) —
unrelated gate; its runs are the witness that re-runs are routine.
[FR-1031](FR-1031-census-extract-cache-dir.md) (Rejected) and
[FR-1032](FR-1032-census-adapter-owned-extract-cache.md) (judged, not
implemented) — cache the census *extract* step inside one adapter
(`gh_repo_extract`); this FR caches map *branch results* for any sub-node
type. They compose: FR-1032's extract output is a natural source of
`version:`. FR-1031 died because a shared graph's wrapper cannot invoke a
bound adapter slot, and it named "compiler-level" reuse as the separate, larger
FR; this is that FR: the map wrapper is framework code that already owns the
call. FR-1031's judgement also demanded 4–6 genuine solution classes with
preserved dissent and an `is_this_a_graph` answer; see Alternatives below.

## Summary

Establish, with witnesses, the design of a map that reuses finished work
across runs: which store, where results live, how scheduling is bounded, and
what the item key, item version and node version are. Output: a fix FR with a
frozen design, and the investigation's tests as its regression suite
(`investigation_before_fix`).

## Value Statement

Census and catalog authors re-run a map over a changing subject and pay only
for what changed, with a record of what was new, changed, unchanged, failed or
deleted.

## Problem

Four graphs (`corpus_census`, `file-hook`, `self-portrait`, `ocr_cleanup`) each
built their own key, skip-if-done or ledger (plan §5.1). The map has no cross-run memory:
`_map_index` is a position, the checkpointer answers "resume this thread", and
results live in state, so a 10k–500k item `collect` is copied into every
checkpoint.

Two design choices dominate the cost and are open:

1. **Where results live.** 26 in-graph consumers read `collect` from state.
   Either they read a store, or the fan-in copies results back into state,
   which returns the checkpoint-size problem.
2. **Chunked scheduling.** One `Send` per item in one step is unbounded memory
   at census scale; bounded batches change the compiled shape from one map
   edge to a batch loop.

## Ideal Result

A map with `key:` and `cache:` re-run over the same subject executes exactly
the items whose key is new, whose version changed, whose node version changed,
or whose last failure was transient; survives `kill -9` without re-executing
finished items; and writes a per-run ledger that reports deletions.

## Decided (enters the investigation as constraints)

| Part | Definition |
|---|---|
| `key:` | The item's own ID, declared (FR-1064). Required with `ledger:`. |
| `version:` | Optional; the source's own change signal (ETag, git blob SHA, mtime, revision ID, `updated_at`). Default: hash of the item's canonical JSON. |
| Node version | Computed once per run at fan-out: hash of the sub-node definition (LLM: prompt file, output schema, *resolved* provider and model; python/tool: source file of the function; agent/subgraph: declared `node_version:`, required with `cache:`) plus the branch inputs other than the item, as bounded by FR-955's projection. |
| Reuse rule | Reuse when key, version and node version all match a stored entry; otherwise run. `--refresh` bypasses reuse. |
| Failures | A **permanent** failure (FR-1064 `error_class: permanent`) is stored with its key, version and node version and is not re-run while all three match; it is reported again in `failures` (marked carried) and counts against `min_success`. A **transient-exhausted** failure is not stored and is retried on the next run. To force re-running permanent failures, the upstream loader changes their version (for example appends a retry epoch), the node version changes (prompt fix), or `--refresh` is used. No separate failure-retry setting. |
| TTL | None on the result store (once it holds the only copy it is not a cache). Remote change is detected by `version:`, not by expiry. |
| Ledger | JSONL, one snapshot per run: `{key, version, node_version, status, error_class, attempts, run}`, status ∈ new / changed / unchanged / failed / deleted; `deleted` from the previous snapshot. Two concurrent runs on one ledger path raise. |

## Questions the investigation must answer (each with a committed witness)

1. **Store.** Does LangGraph's `SqliteCache` (and `RedisCache`), called
   directly by the branch wrapper, hold under concurrent branches in one
   process and across two processes? If not, which store does.
2. **Results location.** For the 26 consumers: measure the checkpoint size of
   a 10k-item `collect` with and without FR-955; decide store-read versus
   materialise, with the consumer migration count for each.
3. **Chunked scheduling.** Prototype bounded `Send` batches; record the
   compiled shape, how it composes with FR-944's map-to-map join and
   FR-1064's join node, and memory at 10k items.
4. **Node version inputs.** On FR-955's projected branch state, confirm that
   every template `state.*` read is inside the projection (FR-955 enumerates
   direct Jinja `state` consumers).
5. **Resume.** `kill -9` mid-run, re-run: finished items are not re-executed
   and output equals an uninterrupted run.

## Acceptance Criteria

- [ ] One committed witness test per question 1–5 (RED where the current code fails).
- [ ] A two-run fixture: run 2 changes one item's version, deletes one, and contains one transient-failed and one permanent-failed item from run 1 — asserts exactly the changed and the transient item are executed, the permanent one is carried, and the ledger classifies all five states.
- [ ] A node-version change (prompt edit) re-runs all items; `--refresh` re-runs all.
- [ ] The fix FR is filed with the frozen design, citing these witnesses, and states the lint rules (`ledger:` without `key:`; `cache:` on agent/subgraph without `node_version:`; FR-032 `cache:` inside a map sub-node is inert).
- [ ] `032-node-level-caching.md` status corrected (inert: no `compile(cache=...)`), with the grep witness.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Hash the fully rendered request per item | Rejected: needs rendering below the wrapper, covers LLM nodes only, and unstable values (timestamps) become silent misses. Items carry their own identity. |
| LangGraph `CachePolicy` on the map sub-node | Rejected: no result predicate, would cache failure records; inert without `compile(cache=...)`. |
| LangChain `set_llm_cache` | Not needed: the lookup happens in the wrapper before any request is built. |
| TTL on results | Rejected: makes expiry load-bearing for correctness (component D's warning). |
| Per-graph ledgers (status quo) | Rejected: four reinventions already. |
| Separate `retry_failures:` setting | Rejected: a version change on the item already expresses it; one mechanism. |

Solution classes (chosen: 1):

1. **Framework-owned reuse in the map wrapper**, keyed by item identity. Chosen.
2. **Graph-owned reuse**: a python node before the map partitions done/undone
   and one after merges (how `corpus_census` and `file-hook` work today).
   Preserved dissent: it needs no framework change and is fully explicit; it
   loses because four graphs reimplemented it with different bugs (plan §5.1)
   and the partitioning node cannot see branch failures classified by
   FR-1064.
3. **Adapter-owned reuse** (FR-1032): caches one source's fetches; composes
   with 1 as its `version:` source, cannot replace it for LLM branches.
4. **Engine-owned reuse**: LangGraph `CachePolicy` / Store. Rejected above
   for maps; Store remains a candidate backend for question 1.
5. **Thread resume only** (checkpointer, FR-391): answers "finish this run",
   not "skip what earlier runs did".

`is_this_a_graph`: the census map itself is a graph; the reuse decision is a
deterministic lookup per item, not a model call, so it is framework code, not
a graph.

## Related

- Plan: [docs/issues-2026-09-24.md §6, §7 J](../docs/issues-2026-09-24.md)
- Depends on: [FR-1064](FR-1064-map-branch-contract.md) (key, failure channel, `error_class`), [FR-955](FR-955-map-branch-input-projection.md) (bounded inputs), [FR-939](FR-939-map-overflow-policy.md) (no silent slicing before any paid run)
