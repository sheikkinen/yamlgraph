# Feature Request: Map memo for file corpora — re-run a map only over files that changed

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** In Progress
**Effort:** 1 day
**Requested:** 2026-09-27
**Supersedes:** [FR-1076](FR-1076-shared-map-reuse-helpers.md) (never implemented; its revised scope was never re-judged)
**First consumer / first event:** the second run of
`examples/demos/meta_map` with no committed graph changed: it makes zero
`describe` calls instead of about 56, and writes the same report.
**Research:** FR-890 research route **skipped by operator decision
(2026-09-27)**. Substitute: the in-body Alternatives table below, the
FR-1076 disposition, and the FR-1065 investigation
([docs/investigations/fr1065-resumable-map.md](../docs/investigations/fr1065-resumable-map.md)).
**Prior art:** [FR-1076](FR-1076-shared-map-reuse-helpers.md) — superseded
by this FR (see Alternatives). [FR-897](FR-897-kurkistusopinnot-fresh-look-agent.md)
— unrelated (a strategy fresh-look agent); matched on common nouns only.
FR-1065, FR-1073, FR-032, FR-768, FR-773 — dispositioned in Alternatives and
Related.

## Human decisions

- **2026-09-27, operator:** supersede FR-1076; plan a shared tool sized to
  the `meta_map` demo.
- **2026-09-27, operator:** skip the research route.
- **Carried from FR-1076 (operator, 2026-09-25):** a stored failure is
  carried, not re-run, while its identity matches.
- **Carried from FR-1076 (operator, 2026-09-26):** no live pilot;
  deterministic witnesses only; spend budget $0.
- **2026-09-27, operator:** advisory judgement (`scripts/judge.sh`, copilot
  backend, APPROVED WITH REVISIONS); fold only observed errors.
- **2026-09-27, operator:** "enforce. pr. outsider. merge" — grants
  implementation authority on the folded FR below. The advisory judgement
  is committed verbatim as [FR-1116-map-memo-file-corpus.judgement.md](FR-1116-map-memo-file-corpus.judgement.md).

## Advisory judgement disposition

| Finding | Disposition |
|---|---|
| R-1 synthetic `dispatch: "memo"`; verdict dispatch undefined | Folded: `map_dispatch` argument; every returned failure and the verdict carry it (item 5, AC-04). |
| R-1 `min_success` validation absent | Folded: FR-1073 domain checked before any write (item 5, AC-05). |
| R-2 "one SQLite table" vs two tables | Folded: Summary corrected. |
| R-2 AC-06 stripped all `dispatch` fields | Folded: only `_map_index` is stripped from successes (AC-06). |
| R-2 full plan re-validation, exact JSON domain models | Not folded: hardening, not an observed error. The plan is a typed model produced by split; implementation validates it through that model. |
| R-3 separate-process reuse | Folded into AC-02. |
| R-3 stale-writer witness | Folded as AC-08a. |
| R-3 kill-before-merge witness | Not folded: split writes nothing, so AC-01 already witnesses it. |
| Revised AC list (AC-01..AC-15) | Not adopted wholesale; the folds above map onto the existing numbering. |

## Summary

Two shared Python tools with FR-768 manifests, `map_memo_split` and
`map_memo_merge`, plus one SQLite store (`meta` and `memo` tables). Before a map, split drops the
items whose file bytes and computation files are unchanged since a stored
outcome. After the map, merge stores the new outcomes and gives the
consumer the whole current population in FR-1073 shapes (a success list
carrying `_map_index`, a `MapFailure` list, a `MapVerdict`), re-indexed to
current positions. Existing reducers change only which state keys they
read. The first consumer is `meta_map`.

## Value Statement

Anyone re-running a map over a file corpus pays only for files that
changed, and downstream reducers keep the FR-1073 contract they already
use.

## Problem

`meta_map` sends every discovered file (52 map graphs plus 3 poison paths)
through one LLM call per run, even when no file has changed. The three
poison paths fail the same way on every run.

FR-1076 aimed at the same waste, but its contract grew larger than any
consumer needs: three tools, two tables, run membership, compare-and-set
publication, deletion counts, a store-read API, and about eight new result
models that replace FR-1073's shapes. Checked against `meta_map`:

- `discover` lists the whole population again on every run, so tracking
  run membership and deletions answers a question nobody asks.
- A row that carries its own (key, version, signature) is correct for its
  own inputs. Concurrent writers can only duplicate spend; they cannot
  corrupt anything, so publication does not need to be serialized.
- The store-read tool existed to shrink checkpoints. #717 withdrew that
  claim and kept the tool anyway.
- Replacing FR-1073's shapes forces every consumer to rewrite its reducer.
  `meta_map`'s [`render_report`](../examples/demos/meta_map/tools.py#L200-L205)
  requires every index 0..N−1 exactly once. That check keeps working if
  merge re-indexes to current positions.

One real composition defect remains. A map's `min_success` counts only
the items it dispatched. With a memo, that is the changed subset, which is
the wrong population, and a threshold miss raises before any save can
run. [`compute_verdict`](../yamlgraph/models/map_results.py#L90-L118)
returns `met` for zero dispatched items, so an all-reused run passes
without checking anything.

## Ideal Result

Run 2 over an unchanged corpus makes zero LLM calls and writes a report
with the same rows. Editing one file re-runs that file only. Editing the
prompt, the subgraph or the tool code re-runs everything. The three
poison paths stay failed without being re-run. The completeness threshold
is judged over the whole current population, after the work is saved.

## Proposed Solution

`examples/shared/map_memo.py`, `examples/shared/map_memo_split.tool.yaml`
and `examples/shared/map_memo_merge.tool.yaml`. Both tools are invoked as
`tool_call` nodes with `on_error: fail`, and their outputs are read from
`<state_key>.result`, following the `split_document` feeder precedent in
[graph-yaml.md](../reference/graph-yaml.md#tool-manifests-fr-768).

```text
discover → poison_the_source
  → memo_split      (tool_call map_memo_split)
  → summarize       (map over {state.memo.result.todo}; min_success: 0)
  → memo_merge      (tool_call map_memo_merge; commits, then enforces min_success)
  → prepare_reduce → reduce → render   (read {state.merged.result.*})
```

1. **Items.** `items` is a list of distinct, non-empty path strings, each
   naming a readable regular file. Relative paths resolve against the
   process working directory, as `meta_map`'s `discover` already assumes.
   The key is the path string exactly as given. Version = SHA-256 of the
   file's bytes. Anything else (a non-string, empty, duplicate, missing
   or non-file item) raises `MapMemoInputError` before the map runs.
   Dict items and other version modes are out of scope.
2. **Signature.** `signature_files` is a non-empty list of paths resolved
   the same way. `inputs` is an optional JSON object for anything else
   that affects the per-item computation. Signature = SHA-256 of
   `json.dumps({"contract": "map_memo/1", "files": {<path as given>:
   <sha256 of bytes>}, "inputs": <inputs or {}>}, sort_keys=True,
   separators=(",", ":"), ensure_ascii=False, allow_nan=False)`.
   Provider and model are not separate arguments; they are covered because
   they live in the hashed graph files (`defaults:`). CLI or environment
   overrides are not captured unless the caller passes them in `inputs`;
   the tool manifest says so.
3. **Store.** One SQLite file at `store`:
   `meta(name TEXT PRIMARY KEY, value TEXT NOT NULL)` with
   `schema_version = 1`, and
   `memo(key TEXT PRIMARY KEY, version TEXT NOT NULL, signature TEXT NOT
   NULL, status TEXT NOT NULL CHECK (status IN ('ok','failed')), payload
   TEXT NOT NULL)`.
   - A row is a hit only if both `version` and `signature` equal the
     current values.
   - Rows are validated through private Pydantic models when written and
     when read.
   - Rows for absent keys are kept and are never pruned (no TTL).
   - A missing file is a miss for every item. Split creates nothing; the
     first merge creates the file.
   - Any other failure raises `MapMemoStoreError`: a non-SQLite file, a
     wrong `schema_version`, invalid JSON or a row that fails its model,
     `database is locked` after a 30 s busy timeout, or a failed write.
     None of these degrades to a miss.
4. **`map_memo_split(items, signature_files, store, inputs=None)`** is
   read-only; one read transaction. It returns `MemoPlan {store, signature,
   current: [MemoItem {key, version, index, hit: none|ok|failed}], todo:
   list[str], hits: dict[str, payload]}`.
   - `store` is the absolute path, so merge writes to the store that
     split read.
   - `todo` holds the missed keys in current order.
   - For `ok` hits the payload is the stored success dict. For `failed`
     hits it is a `StoredFailure {error_type, message, node, tolerated}`.
5. **`map_memo_merge(plan, results, failures, map_name, map_dispatch, min_success=1.0)`.**
   - `map_dispatch` is the non-empty token of the map dispatch over `todo`
     (`meta_map` passes `{state._map_verdict.summarize.dispatch}`). Every
     executed `MapFailure` must carry this `map_name` and `map_dispatch`,
     else `MapMemoInputError`.
   - `min_success` follows FR-1073: a non-negative integer, or a finite
     float in `[0.0, 1.0]`; `1` and `1.0` stay distinct. Booleans and any
     other value raise `MapMemoInputError` before any write.
   - `results` is the map's `collect` list and `failures` its FR-1073
     failures list. Each `_map_index` and `MapFailure.index` points into
     `plan.todo`. Together they must cover 0..len(todo)−1 exactly once
     each, else `MapMemoInputError` and nothing is written. Booleans and
     other non-integer indices are rejected.
   - In one `BEGIN IMMEDIATE` transaction, merge upserts one row per
     executed key: `ok` holds the success dict without `_map_index`;
     `failed` holds a `StoredFailure`. Tolerated and untolerated failures
     are both stored. Reused rows are not rewritten. Then it commits.
   - It returns `MemoMerged {records, failures, verdict, counts}`:
     - `records` has one success dict per `ok` current item, in current
       order, with `_map_index` set to the current index.
     - `failures` has one `MapFailure` per failed current item, executed
       or reused, with `map = map_name`, `dispatch = map_dispatch` and
       `index` = current index. Reuse provenance lives in `counts`, not in
       `dispatch`.
     - `verdict` = `compute_verdict(map_dispatch, len(current), rows,
       min_success)` over the whole current population.
     - `counts {executed_ok, executed_failed, reused_ok, reused_failed}`.
   - After commit, if `verdict.met` is false, merge raises
     `MapCompletenessError(map_name, verdict)`. The work is already
     durable, and the threshold is judged on the right population.
6. **Concurrency and crashes.** There is no lock and no run identity. Two
   concurrent runs may both execute the same miss; the last upsert wins,
   and each row is correct for its own version and signature. A run
   killed before merge loses that run's work and leaves the store
   unchanged. This FR makes no crash-survival claim (FR-1065 row 5a).
7. **Consumer: `meta_map`**, through `scripts/author.sh` with a committed
   brief under `feature-requests/authoring-briefs/`:
   - Insert `memo_split` and `memo_merge`.
   - Map `summarize` over `{state.memo.result.todo}` with `min_success: 0`.
     Pass `min_success: 0.9` and the `summarize` dispatch token to merge.
   - Store at `outputs/meta_map/memo.sqlite`, which is already git-ignored.
   - `signature_files`: `examples/demos/meta_map/graph.yaml`,
     `subgraphs/summarize_one.yaml`, `prompts/describe_graph.yaml`,
     `tools.py`. Over-invalidation is the safe direction.
   - `reduce_inputs` and `render_report` read records, failures and the
     verdict from `merged.result` instead of `summaries`,
     `summary_failures` and `_map_verdict`. Their index-coverage check
     and report shape stay as they are. The report's coverage line adds
     the four memo counts.
   - README: document the memo and how to force a full run (delete the
     store).
   - The other map graphs (`person_profile_census`, `corpus_census`,
     `ocr_cleanup`, `file-hook`, `self-portrait`) are not touched.

Not authorized: any change under `yamlgraph/`; map compiler, checkpointer,
manifest schema or CLI changes; Redis or LangGraph Store backends; dict
items or custom version fields; run membership, deletion tracking,
publication or conflict detection; a store-read or query API; pruning or
TTL; automatic retry policy; branch-level writes; live runs.

## Acceptance Criteria

- [ ] AC-01: Split over a missing store returns every item in `todo`, creates no file, and leaves an existing store byte-identical.
- [ ] AC-02: Run 1 over five files, then run 2 in a separate process with one file's bytes changed, executes exactly that file. Merge returns five records with `_map_index` 0..4 in current order and counts `executed_ok=1, reused_ok=4`.
- [ ] AC-03: Changing one byte in any signature file, or changing `inputs`, re-runs every item. The same inputs produce the same signature in a separate process.
- [ ] AC-04: A failed item from run 1 is carried in run 2 without executing. It appears in `failures` with its current index and the supplied `map_dispatch`, counts toward `reused_failed` and `verdict.failed` over the whole population, and `verdict.dispatch == map_dispatch`. Changing its bytes re-runs it.
- [ ] AC-05: Merge judges `min_success` over the whole current population. It raises `MapCompletenessError` only after commit, and the next split then reuses the stored outcomes. An all-reused run with a threshold miss also raises; it is not treated as met because nothing was dispatched. Invalid `min_success` values (booleans, negatives, non-finite or out-of-range floats, strings) raise `MapMemoInputError` and write nothing.
- [ ] AC-06: Merge rejects results and failures whose indices together miss, duplicate or exceed 0..len(todo)−1, or are non-integer (including booleans), or whose failures carry another map name or dispatch. It writes nothing in that case. A stored success drops only `_map_index` and keeps every other field, including one named `dispatch`; a stored failure validates as `StoredFailure` (no map, dispatch or index).
- [ ] AC-07: Non-string, empty, duplicate, missing or non-file items and signature files raise `MapMemoInputError` before any map branch runs.
- [ ] AC-08: A non-SQLite file, a wrong `schema_version`, a malformed or model-invalid row, and a failed write each raise `MapMemoStoreError`; none returns a miss.
- [ ] AC-08a: Stale writer: plan A split over version 1 and plan B over version 2; merge B, then merge A. A following split over version 2 is a miss, never a false hit, and neither merge writes a partial row. (Kill-before-merge needs no separate witness: split is read-only, AC-01.)
- [ ] AC-09: Both manifests validate through FR-768 loading, resolve `map_memo.py`, and require no `yamlgraph/` change.
- [ ] AC-10: `meta_map` is migrated through `scripts/author.sh`, and its report records lint and a deterministic smoke run. A provider-free test runs the migrated graph twice on a fixture corpus plus the poison, with a call counter. Run 1 makes one `describe` call per path. Run 2 makes zero, writes the same report table and failures table, and still has the three poison paths failing with `ClaimMismatchError`. Editing one fixture file makes run 3 call `describe` exactly once.
- [ ] AC-11: A new capability/REQ governs the helpers, every new test carries its marker, and `python scripts/req_coverage.py --strict` passes. The shared README, manifest contract comments, changelog fragment, FR implementation record and diary entry are present.

## Alternatives Considered

| Option | Disposition |
|---|---|
| FR-1076 as revised in #717 | Superseded. It solves membership, publication and store reads, which neither `meta_map` nor the census needs, and it replaces FR-1073's shapes, so every consumer's reducer must change. |
| Framework-owned reuse (a map `memo:` key) | Rejected for now. It needs compiler and checkpointer changes and a judged key/version contract across all map sub-node types. It becomes cheaper once two example consumers prove the contract. It is the only option that fixes the `min_success` placement without a consumer opting into `min_success: 0`. |
| Graph-local cache in `meta_map/tools.py` | Rejected. `person_profile_census` is the named second consumer (FR-1076), so a graph-local copy would be the fifth reinvention (docs/issues-2026-09-24.md §5.1). |
| LangGraph `SqliteCache` / node `CachePolicy` | Rejected by the FR-1065 probes (row 1f) and FR-032: no cross-run identity control, and it caches branches, not keyed outcomes. |
| Content-addressed rows (PK = key+version+signature) | Rejected. It grows without bound on every edit. PK = key with a self-describing row gives the same correctness with bounded size. |
| Save inside each branch | Rejected. It needs branch-level writes, which FR-1065 kept out of scope. Merge-after-map loses only the killed run's work. |

`is_this_a_graph`: no. Split and merge are deterministic I/O with no model
step, so they are Python tools, as the three-layer rule requires.

## Related

- [FR-1076](FR-1076-shared-map-reuse-helpers.md) (superseded), [FR-1065](FR-1065-resumable-map-investigation.md), [FR-1073](FR-1073-map-result-contract.md), [FR-1113](FR-1113-meta-map-demo.md), [FR-768](FR-768-tool-manifest-declaration-reuse.md), [FR-773](FR-773-shared-document-splitter-manifest.md)
- [examples/demos/meta_map](../examples/demos/meta_map/README.md)
