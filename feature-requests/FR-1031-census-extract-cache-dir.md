# Feature Request: FR-1031 `cache_dir` on the census extract slot

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Rejected
**Verdict:** REJECTED (2026-09-09) — shared wrapper cannot invoke a bound slot; see [judgement](FR-1031-census-extract-cache-dir.judgement.md)
**Superseded-by:** [FR-1032](FR-1032-census-adapter-owned-extract-cache.md)
**Effort:** 0.5 days
**Requested:** 2026-09-09
**First consumer / first event:** the CLAUDE.md corpus census, at the moment
`extract` re-fetches 620 GitHub files that are already on disk from an
interrupted harvest (2026-09-09, this session).
**Research:** in-body dispositioned alternatives table below (FR-889 style),
grounded in a read of the three prior-art FRs and the census source.
**Prior art:** [032-node-level-caching.md](032-node-level-caching.md) — node
granularity, not per-item, and no store is wired (see table);
[FR-111-compiled-graph-cache.md](FR-111-compiled-graph-cache.md) — caches the
compiled graph object, not results;
[FR-101-ebook-pipeline-incremental-persist.md](FR-101-ebook-pipeline-incremental-persist.md)
— one demo's stage outputs, superseded by FR-103, not a reusable extract cache.

## Summary

Give `examples/demos/corpus_census/graph.yaml` an optional `cache_dir` so the
`extract` stage reads from disk when an item has already been fetched. Absent
the variable, behaviour is unchanged.

## Value Statement

The census re-fetches its entire corpus on every run and cannot resume. For a
remote corpus that is the difference between a census you can iterate on and
one you run once and hope.

## Problem

`gh_repo_extract` issues three live `gh api` calls per item on every run.
Grepping `corpus_adapters.py` and `tools.py` for cache/resume/checkpoint
returns nothing — there is no reuse of any kind.

Consequences, measured this session:

- A 620-item corpus costs roughly 1,860 GitHub calls and about 30 minutes per
  run, paid again for every rubric change.
- An interrupted run loses everything. A harvest killed at 600/1000 survived
  only because the hand-rolled script it should not have been happened to
  write to disk.

The census was built for local corpora — diary entries, git commits, PDFs —
where re-reading costs nothing. FR-899's GitHub adapters moved it into remote,
rate-limited territory without moving it into durable territory.

## Ideal Result

An interrupted census resumes at the item it stopped on. Items already fetched
cost nothing. Re-running with a changed rubric re-judges without re-fetching.
The ledger proves which items came from cache and which from the network. No
adapter contains caching code, so every present and future corpus inherits the
behaviour.

## Proposed Solution

A **shared tool**, per the operator constraint — caching is owned by the graph,
never by an adapter.

- `tools.py` gains `cached_extract`, wrapping the bound `extract` slot. Bound
  adapters are unchanged and stay cache-unaware.
- New optional `--var cache_dir=<path>`. Absent → the slot is called directly,
  exactly as today.
- Key is `sha256(item_ref)`; entry is `<cache_dir>/<key>.json` holding
  `{item, content, sha256, bytes, fetched_at}`. `sha256` and `bytes` are
  already required by the freeze stage of
  [corpus-map-reduce.md](../../reference/patterns/corpus-map-reduce.md), so the
  key material exists.
- Hit → return stored content. Miss → call the slot, write the entry, return.
- `reduce_ledger` gains a `cache` column (`hit` | `miss`) so coverage reconcile
  can prove the split deterministically.

```bash
yamlgraph graph run examples/demos/corpus_census/graph.yaml \
  --tool discover=adapters/gh-org-discover.tool.yaml \
  --tool extract=adapters/gh-repo-extract.tool.yaml \
  --var cache_dir=tmp/census-cache/claude-md \
  --var source=... --var rubric=... --var output_path=... \
  --var brief_path=... --var brief_rubric=...
```

**Principal implementation risk, flagged for the Judge.** `extract_items` is
`type: python, tool: extract`. Wrapping requires a shared tool to invoke a
bound slot. If FR-892 slot binding does not support slot-invocation from a
tool, the fallback is a `cache_dir` field on the map node handled by the
compiler — which is a larger change and should be a separate FR, not a silent
widening of this one.

## Acceptance Criteria

1. With `cache_dir` unset, the census runs exactly as today; no new files.
2. Two consecutive runs over the same corpus with `cache_dir` set: the second
   makes zero `extract` network calls, proven by an adapter call counter in the
   test, not by wall-clock.
3. A run interrupted after N items and re-invoked completes the remaining
   items and re-uses the first N.
4. Changing `rubric` between runs re-judges every item and re-fetches none.
5. The ledger reports per-item `hit` | `miss`, and hits plus misses equals the
   item count.
6. A corrupt or unreadable cache entry is a miss, not a crash, and is recorded
   as a miss.
7. Adapter files under `corpus_census/adapters/` are unchanged by this FR.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Reuse FR-032 node-level caching (`cache: true`) | **Rejected — wrong granularity.** `map_compiler.py` iterates `for item in items:` inside one graph node, so a `CachePolicy` key covers the whole item list; one new item invalidates every item. Secondary: no `BaseCache` is passed at any `compile()` call site and no cache backend is imported anywhere in `yamlgraph/`, so the policy has no store today. That gap is real but separate from this FR. |
| FR-111 compiled graph cache | **Not applicable.** Caches the compiled graph object; says nothing about node or item results. |
| FR-101-style incremental persist | **Rejected — not reusable.** Persists one demo's stage outputs to survive a crash. Superseded by FR-103. Does not give content-addressed per-item reuse at a slot boundary. |
| Cache inside each adapter | **Rejected by operator constraint.** N adapters means N implementations and N bugs; a shared tool gives every corpus the behaviour once. |
| Checkpointer-based resume | **Rejected — wrong axis.** A checkpointer resumes one interrupted run; it does not let a *new* run with a changed rubric skip fetching. |

## Related

- FR-892 census tool slots; FR-899 GitHub adapters; FR-895 synthesize tail.
- [reference/patterns/corpus-map-reduce.md](../../reference/patterns/corpus-map-reduce.md)
  — freeze stage already mandates `sha256` and `bytes`.
- [docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md](../../docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md)
  — the session that surfaced this.
