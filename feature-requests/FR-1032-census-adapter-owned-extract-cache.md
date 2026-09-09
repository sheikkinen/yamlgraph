# Feature Request: FR-1032 adapter-owned extract cache for `gh_repo_extract`

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed (revised 2026-09-09 per judgement R-1…R-7)
**Effort:** 0.5 days
**Requirement:** REQ-YG-673 (new), owned by a new capability **CAP-269 corpus
extraction persistence**. CAP-249 is unchanged — its `modules:` lists only
`tools/tool_slots` and `compile/graph_loader`
(`capabilities/CAP-249-tool-slot-binding.yaml:17-19`), and this FR changes no
binding behaviour.
**Requested:** 2026-09-09
**First consumer / first event:** the FR-899 organization-repository census, at
its second invocation over the same `source` while iterating `rubric` — the
point at which every `gh_repo_extract` call repeats work already done.
**Research:** in-body solution-class table below (FR-889 style), anchored to
the source reads in the FR-1031 and FR-1032 judgements.
**Prior art:** [FR-1031](FR-1031-census-extract-cache-dir.md) — same problem,
REJECTED because a graph-owned wrapper cannot invoke a bound slot;
[032-node-level-caching.md](032-node-level-caching.md) — node granularity, not
per-item; [FR-111-compiled-graph-cache.md](FR-111-compiled-graph-cache.md) —
caches the compiled graph object, not results;
[FR-101-ebook-pipeline-incremental-persist.md](FR-101-ebook-pipeline-incremental-persist.md)
— one demo's stage outputs, superseded by FR-103.

## Summary

Add a private typed cache helper to
`examples/demos/corpus_census/adapters/corpus_adapters.py` and route
`gh_repo_extract` — and only `gh_repo_extract` — through it. An optional
`cache_dir` turns it on; absent, behaviour is exactly as today.

## Value Statement

An org-repo census cannot be iterated. Every rubric change re-pays the full
extraction cost, and an interrupted run keeps nothing.

## Problem

`gh_repo_extract` issues three live `gh api` calls per repository — metadata,
README, contributors (`corpus_adapters.py:135-155`) — and discovery yields at
most `MAX_REPOS = 100` repositories (`corpus_adapters.py:95,112-134`). A full
census is therefore up to 300 remote calls, and every one is repeated on the
next run even when only `rubric` changed. Grepping `corpus_adapters.py` and
`tools.py` for cache/resume/checkpoint returns nothing: there is no reuse of
any kind, and an interruption keeps nothing.

FR-899 moved the census into remote, rate-limited territory without moving it
into durable territory.

## Ideal Result

A second census over the same source with a changed rubric makes zero
extraction calls. An interrupted census resumes at the repository it stopped
on. No entry can be served across a different extractor, extractor version,
source, item, or entry schema. Every way an entry can be wrong is either a
diagnosed miss or a loud failure — never a silent hit.

## Ownership decision (FR-1031 R-2, answered by the operator 2026-09-09)

**Cache composition belongs to the bound extraction implementation.** FR-892
states slot resolution reuses existing runtimes with "no new engine"
(`tool_slots.py:1-7`), and a Python tool receives only resolved state with no
bound-slot callable (`python_tool.py:229-239`). Graph-owned composition would
need a new framework seam and, per judge doctrine, three concrete consumers.
One exists.

The helper is private to `corpus_adapters.py`, which is where
`gh_repo_extract` lives. It is **not** claimed that all census extractors are
co-located — `diary_extract` is in `diary_adapters.py`
(`adapters/diary_adapters.py:45-51`), and that FR-1031 claim was false.

## Proposed Solution

```python
def gh_repo_extract(state: dict[str, Any]) -> str:
    item = _require(state, "item")
    return _cached(state, "gh_repo_extract", GH_REPO_EXTRACT_VERSION, item,
                   lambda: _fetch_repo_bundle(item))
```

**Controls (R-3).** `graph.yaml` state gains `cache_dir: str` and
`cache_refresh: str`; neither is declared today (`graph.yaml:18-40`). Absence
of `cache_dir` disables caching. `--var` values arrive as strings
(`yamlgraph/cli/helpers.py:54-88`), so `cache_refresh` is the exact
case-insensitive enum `true | false`, defaulting to false when absent and
raising `ValueError` on any other value. Python truthiness is not used — under
it, `"false"` would refresh. The map fan-out already copies outer state into
every item send (`map_compiler.py:335-365`), so no compiler or manifest change
is needed. The `graph.yaml` state edit is a material graph-artifact change and
goes through the sole graph-authoring route, retaining its authoring report.

**Two independent versions (R-4).** `CACHE_SCHEMA` versions the JSON envelope.
`GH_REPO_EXTRACT_VERSION` versions the *meaning* of the returned evidence and
is bumped whenever the bundle's composition changes. Both are in the key and
the entry: a stable function name alone would silently serve output from an
older implementation.

Key: `sha256("\x00".join([CACHE_SCHEMA, extractor_id, extractor_version,
source, item]))`, UTF-8.

**Typed entry, validated identity (R-5).** A Pydantic model covers `schema`,
`extractor_id`, `extractor_version`, `source`, `item`, `content`,
`content_sha256`, `bytes`, `fetched_at`. Before any hit the helper validates
the complete model, then exact equality of every identity field against the
requested key material, then `bytes == len(content.encode("utf-8"))` and
`content_sha256 == sha256(content.encode("utf-8"))`. This stops a validly
hashed payload stored under the wrong filename from becoming a silent hit.

| Condition | Behaviour |
|---|---|
| Entry absent | Miss. Normal path, no diagnostic. |
| Malformed JSON, model-invalid, non-string content, invalid timestamp | Diagnosed miss naming the reason; re-fetch, atomically overwrite. |
| Mismatched `schema`, `extractor_id`, `extractor_version`, `source`, `item`, `bytes`, or `content_sha256` | Diagnosed miss naming *which* field; re-fetch, atomically overwrite. |
| Read fails with any `OSError` other than `FileNotFoundError` | **Raise.** |
| Replace fails after bounded retry | **Raise**, temp file removed. |

**Durability and bounded replace (R-6).** The entry is written before
`_cached` returns, so no repository is complete without its entry. Write is a
unique same-directory temp file, then `os.replace`: **at most three attempts,
retrying only `PermissionError`** (Windows raises it when the destination is
momentarily open), reusing the already-created temp file. Any other `OSError`
raises immediately. A temp create/write/flush/close failure is a failure, not a
replace retry. On every terminal failure the temp file is removed without
masking the primary exception.

**Freshness is operator-controlled.** `<org>/<name>` is a mutable identity, so
a hit means "this extractor version already saw this item", never "this item is
current". There is no TTL and no eviction. `cache_refresh=true` forces every
item to miss and rewrite. This FR does **not** claim to satisfy the corpus
pattern's immutable-identity rule (`corpus-map-reduce.md:57-82`) — it
deliberately keys a mutable source and records no cache provenance in the
ledger.

**The ledger is unchanged (R-5, FR-1031).** No cache column; the reducer's row
schema stays frozen. Hit/miss is asserted in tests via a call counter.

## Acceptance Criteria

Test surface: `tests/unit/test_census_extract_cache.py`, every test tagged
`@pytest.mark.req("REQ-YG-673")`.

1. `cache_dir` unset → `fetch` runs on every call; no file is created under
   `tmp_path`.
2. Two consecutive `gh_repo_extract` runs with `cache_dir` set → the second
   run's fetch counter is `0`. Asserted on the counter, never wall-clock.
3. Abort after N of M items, re-invoke → the first N have counter `0`, the
   remaining M−N fetch, and N entries existed on disk before re-invocation.
4. Distinct entries, no cross-serving, for each of: different `extractor_id`,
   different `extractor_version`, different `source`, different `item`,
   different `CACHE_SCHEMA`.
5. Parametrised corruption — malformed JSON, model-invalid, non-string
   content, invalid timestamp, and each mismatched identity field, `bytes`,
   and `content_sha256` — each re-fetches, overwrites, and logs a diagnostic
   naming that specific reason, asserted through `caplog` at a frozen level.
6. `cache_refresh` accepts `true`/`false` case-insensitively, defaults to false
   when absent, and raises `ValueError` for any other value including `"0"`,
   `"yes"`, and `""`.
7. `cache_refresh=true` misses and rewrites against an otherwise valid entry.
8. An entry unreadable for a non-absence reason raises; it does not degrade to
   a miss.
9. Replace behaviour: at most three attempts, only `PermissionError` retried,
   any other `OSError` propagates on the first occurrence, destination stays
   intact on failure, and no orphan temp file remains in any terminal path.
10. Ledger output is byte-identical for the same corpus with and without
    `cache_dir`.
11. Wiring: `CAP-269` created owning `REQ-YG-673` with modules for
    `examples/demos/corpus_census` (graph), `corpus_adapters.py`, and the new
    test file; CAP-249 untouched; changelog fragment; FR implementation record;
    graph-authoring report for the `graph.yaml` change; diary distillation.

**Not authorized:** caching `pdf_extract`, `git_extract`, `gh_pr_extract`, or
`diary_extract`; a GitHub-file extractor; any `yamlgraph/` change; ledger or
reducer changes; manifest-schema changes; TTL or eviction; a shared framework
cache primitive. Additional adapters may opt in only under later evidence.

## Research: solution classes

`is_this_a_graph`? **No.** No per-item model call and no pipeline stage — an
I/O concern inside one tool of an existing graph, which this FR modifies.

| # | Class | Evidence | Disposition |
|---|---|---|---|
| 1 | **Adapter-owned private helper, one call site** | `gh_repo_extract` and the helper share `corpus_adapters.py:135-155` | **Chosen.** No framework change; per-item durability is structural; only the adapter knows what makes its own output stale. |
| 2 | Graph-owned wrapper tool | `tool_slots.py:141-145`, `python_tool.py:229-239` — no bound-slot callable in state | Rejected: infeasible. FR-1031's rejection cause. |
| 3 | Compiler-level `cache_dir` on the map node | `map_compiler.py:228-332` | Rejected **for now**: framework primitive, needs 3+ consumers; one exists. |
| 4 | LangGraph node `CachePolicy` (FR-032) | `map_compiler.py:52` iterates in-node; no `BaseCache` at any `compile()` call site | Rejected: node granularity keys the whole item list, and no store is wired. |
| 5 | Checkpointer-based resume | `executor_async.py:216` | Rejected: resumes one interrupted run; a new run with a changed rubric still re-fetches. |
| 6 | External pre-materialisation — fetch to a local tree, bind local adapters | Done ad hoc this session for a *different* workload | Rejected: two-step operator workflow, provenance outside the census, and it is the hand-rolling the doctrine forbids. |

**Preserved disagreement.** Class 6 needs zero code and demonstrably works; the
counter is that the babysitter script is where provenance dies. Class 3 is the
better end state if a second and third consumer appear, making class 1 a local
optimum that must then be undone. Accepted knowingly: one consumer does not buy
a framework seam.

## Related

- FR-892 slot binding; FR-899 org-repo census; FR-895 synthesize tail.
- [reference/patterns/corpus-map-reduce.md](../../reference/patterns/corpus-map-reduce.md)
- [FR-1032 judgement](FR-1032-census-adapter-owned-extract-cache.judgement.md)
