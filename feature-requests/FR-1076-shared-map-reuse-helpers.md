# Feature Request: Shared map reuse helpers — skip items finished in earlier runs, read results from a store

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed revision, 2026-09-26. The second [judgement](FR-1076-shared-map-reuse-helpers.judgement.md) is APPROVED WITH REVISIONS; its R-1 through R-3 are dispositioned below. This revision adds explicit computation inputs and save-before-reconciliation, and removes the generic query and checkpoint-size deliverables. Those scope changes require re-judgement through `scripts/judge.sh` before implementation. Merging this documentation grants no runtime implementation authority.
**Effort:** 1 day
**Requested:** 2026-09-25
**First consumer / first event:** the next re-run of
`examples/demos/person_profile_census` over the same subject: run 2 pays only
for new, changed or version-bumped items. Today every re-run pays for all
items.
**Research:** FR-890 research route **skipped by operator decision
(2026-09-25)**. Substitute: the in-body solution classes below (carried from
FR-1065, whose judgement accepted them as meeting the in-body alternative,
FR-1065 judgement "What is sound"), plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §5.1 (four
graph-local reinventions) and §6.1–§6.4.
**Prior art:**
[FR-1065](FR-1065-resumable-map-investigation.md) (investigation complete,
PR #696) — chose framework-owned reuse and kept graph-owned reuse as
dissent; this FR reverses that choice for the reasons in Alternatives, and
takes over FR-1065's reuse questions 1, 2 and 5. Chunked scheduling
(question 3) and node-version inputs under projection (question 4) stay in
FR-1065. Its evidence is in "Investigation evidence" below.
[FR-1073](FR-1073-map-result-contract.md) (merged 2026-09-25, PR #702) —
supplies the `failures` channel (typed `MapFailure` records, default
`<collect>_failures`), `_map_index` on each success in `collect`,
`MapFailure.index` on each failure, and `_map_verdict.<name>`. Its
map-level `key` was cut (FR-1073 amendment A-1), so this FR owns item
keys.
[FR-1031](FR-1031-census-extract-cache-dir.md) (Rejected) — died because a
shared graph's wrapper cannot invoke a bound adapter slot. These helpers are
ordinary graph nodes placed around the map, not adapter slots, so that
rationale does not apply.
[FR-1032](FR-1032-census-adapter-owned-extract-cache.md) (judged, not
implemented) — adapter-level extract cache; composes as a source of
`version`.
[032-node-level-caching.md](032-node-level-caching.md) — inert `CachePolicy`;
not used.
[FR-768](FR-768-tool-manifest-declaration-reuse.md) / [FR-773](FR-773-shared-document-splitter-manifest.md)
— shared tool manifest precedent (`examples/shared/*.tool.yaml`).

## Human decisions

- **2026-09-25, operator (FR-1065 R-3):** consumers read results from the
  store; `collect` state need not stay the consumer contract.
- **2026-09-25, operator:** a stored failure is carried, not re-run, while
  key, version and node version match (item 3).
- **2026-09-26, operator:** no live pilot; deterministic witnesses only.
  Pilot spend budget **$0**; **no live storage budget**. This replaces the
  pilot budget the FR-1065 report records as accepted on 2026-09-25 (one
  census run of spend, 50 MB store cap). Every place the judgement asks for
  a human-approved pilot spend or storage budget uses this decision.
- **2026-09-26, operator:** reviewed the advisory judgement (C-1) and
  instructed "proceed with all fr changes".
- **2026-09-26, operator:** "simplify, rejudge" — replace the five-table
  store with lease tokens by one items table and an optimistic publish
  check; re-run the judge.
- **2026-09-26, operator:** "revise fr-1076, docs pr. outsider. merge" after
  the bounded-reuse proposal. This authorizes this documentation revision
  and its PR, not implementation or a live pilot. The next implementation
  gate is re-judgement of the revised scope.

## Second judgement disposition and revised boundary

| Source | Disposition in this revision |
|---|---|
| R-1: lossless typed load plan and stable payloads | Folded: every current key is represented; dispatch indices are used only for save attribution, never persisted as identity. |
| R-2: identity-reconciled pilot and reordered runs | Folded: the ledger joins by PR identity and proves unchanged, reordered, changed, new and carried-failed cases. |
| R-3: path, scalar and reserved-key rules | Folded: explicit path resolution, strict scalar identities, and a separate key/result envelope. Generic field projection is removed, so result fields cannot shadow identity. |
| Review: rubric changes can reuse stale answers | Add required explicit computation inputs to the signature, including the pilot's rubric and both label sets. No automatic read analysis. |
| Review: strict map blocks downstream save | The pilot opts into `min_success: 0`, saves every accounted outcome, then reconciles the whole current population before synthesis. |
| Scope reduction | Read all current success records for this bounded pilot. No fields/order/filter API or checkpoint-size acceptance gate; no claim of first-run memory reduction. |

The second judgement remains an unedited historical verdict on the prior
scope. The contracts and acceptance criteria below are the proposed replacement,
not a claim that the judge has approved these changes.

## Deviations from the first judgement

| Judgement demand | This revision | Why |
|---|---|---|
| R-2: tables for items, completed-run membership and lease; unguessable run token; abandoned-lease recovery | Two tables: `meta` and `items`. `items.last_run` marks membership; `meta.current_run` marks the published run. No lease, no token: load writes nothing, and save publishes only if `current_run` still equals the run load saw (item 4). | The lease existed to exclude a second writer. A second concurrent run can only waste spend: save is one transaction and a stale save is refused, so nothing is corrupted. Dropping the lease removes the token, the abandoned-lease procedure, and every crash case that left a lease held. |
| R-5 / AC-08: killed-process resume re-runs no finished branch | No crash claim. Load is read-only, so a killed run leaves the store byte-identical (AC-08). | Row 5a shows the engine re-runs finished branches of the open step; the judgement itself says that fix is a separate FR. |
| R-5 / AC-10: checkpoint-size witness | Removed from the proposed implementation scope | The cited 4,190,046 B vs 51,208 B measurements are from the 10,000-item report, not the 1,000-item test. They compare branch-side storage, not this load/map/save design. |
| R-3: length-framed node-version hash | Canonical-JSON computation signature including explicit runtime inputs | Canonical JSON is unambiguous; files and model alone miss a changed rubric. |

## Investigation evidence (R-1)

Report [docs/investigations/fr1065-resumable-map.md](../docs/investigations/fr1065-resumable-map.md);
witnesses [tests/unit/test_fr1065_resumable_map_probes.py](../tests/unit/test_fr1065_resumable_map_probes.py)
(REQ-YG-689, marked `slow`) on the stand-alone LangGraph probes in
[tests/fixtures/fr1065/probes.py](../tests/fixtures/fr1065/probes.py).

| Question | Witness | Result | Effect here |
|---|---|---|---|
| SQLite across two processes, and exclusion | `test_sqlite_cache_persists_across_two_writer_processes` (L36), `test_sqlite_cache_gives_no_lease_exclusion` (L44), `test_sqlite_unique_insert_lease_excludes_second_process` (L50) | `SqliteCache` rejected as store and as lock; a `UNIQUE`-key insert gave 0 of 10 double winners (report row 1f) | plain SQLite store; `BEGIN IMMEDIATE` save with a compare-and-set on `current_run` instead of a lease (items 1, 4) |
| Checkpoint bytes, `collect` vs store-selected | `test_store_results_shrink_final_checkpoint` (L57), 1,000-item assertion; 10,000-item report command | report: final checkpoint 4,190,046 B vs 51,208 B (rows 2a/2b) | context only; no memory-reduction claim for these helpers |
| `kill -9` + same-thread SQLite-checkpointer resume | `test_sigkill_mid_superstep_reruns_completed_branches` (L74); `test_sigkill_in_batch_loop_loses_only_the_open_batch` (L82) | 20 items, 6 finished before the kill, resume ran all 20 (row 5a); a batch loop of 4 re-ran only the 2 open-batch items (5b) | no crash-survival claim (item 7, AC-08) |
| Cross-run reuse from the checkpointer | `test_new_thread_reuses_no_earlier_result` (L98) | 40 calls for 20 items | cross-run reuse needs this store |

Contracts: the report selects store-read results (and a `UNIQUE`-insert
lease, not used here; see Deviations), rejects `SqliteCache` and thread
resume as crash recovery, and
carries key, version, node version and failure-carrying to this FR
unwitnessed; items 2–3 freeze them and AC-03–AC-06 witness them. The report
selects no retention rule; this FR keeps every row, with no TTL (FR-1065
rejected TTL on results).

Gaps, stated plainly:
- **No 10,000-item test.** The 10k numbers come from the report command,
  whose output is not committed. No checkpoint-size deliverable remains here.
- **Fresh-file race unwitnessed.** Report rows 1b/1d (`database is locked`
  while a second process creates a fresh file) have no test. Item 1 turns
  that error into `MapReuseStoreError`, never a miss.

## Summary

Three shared Python tools with manifests — `map_reuse_load`,
`map_reuse_save`, `map_reuse_read` — reuse published item outcomes across
runs. One bounded `person_profile_census` pilot proves identity, invalidation
and failure accounting. No framework change, generic query API or crash-resume
implementation.

## Value Statement

A census author re-runs a map over a changing subject and pays only for what
changed, with counts of new, changed, unchanged, failed and deleted items.

## Problem

The plan inventories four related but different mechanisms: `corpus_census`
writes a final ledger, `file-hook` uses output-file existence, `self-portrait`
caches lookups, and `ocr_cleanup` works in batches (plan §5.1). They are
precedents, not four interchangeable implementations this FR must migrate.
The concrete gap is the pilot's repeated classification of unchanged PRs.

Two composition defects in the previous proposal matter before storage code:
files/model do not capture a changed runtime rubric, and a strict map can
raise before a downstream save. Counting only new dispatches also hides
carried failures. This revision fixes those contracts in one consumer.

## Ideal Result

An unchanged second census run makes zero classification calls and emits the
same key-to-classification ledger. A changed rubric cannot reuse answers to
the old question. A failed item does not prevent successful outcomes from
being saved; the final ledger accounts for the whole current population.
An interrupted unpublished run may redo work, but cannot damage the last
published run.

## Proposed Solution

`examples/shared/map_reuse.py` plus `map_reuse_load.tool.yaml`,
`map_reuse_save.tool.yaml`, `map_reuse_read.tool.yaml`.

Proposed composition, not an executable graph or new map syntax:

```text
extract current PR evidence (existing strict map)
  -> prepare keyed classification items and explicit computation inputs
  -> map_reuse_load
  -> judge_items (min_success: 0; todo only)
  -> map_reuse_save (all outcomes, one transaction)
  -> map_reuse_read (the run just saved)
  -> reduce_pr_ledger (whole-population reconciliation and existing canary)
  -> existing synthesis
```

1. **Store.** One SQLite file per `store` path. Every row passes through a
   private Pydantic model on write and on read.

   | Table | Columns |
   |---|---|
   | `meta` | `name TEXT PRIMARY KEY, value TEXT NOT NULL`; rows `schema_version = 1`, `current_run` (absent until the first publish) |
  | `items` | `key TEXT PRIMARY KEY, version TEXT NOT NULL, node_version TEXT NOT NULL, status TEXT NOT NULL CHECK (status IN ('ok','failed')), result_json TEXT NOT NULL, last_run TEXT NOT NULL` — latest record per key; `result_json` is the stable success payload or `StoredFailure` |

   - *Encodings.* `key` and a named `version` are stored as their JSON
     text, so `"1"` and `1` differ; `result_json` is canonical JSON
     (item 2).
   - *Schema.* A missing or zero-byte file is created by the first save.
     Any other file must hold `schema_version = 1`, else
     `MapReuseSchemaError`.
   - *Fail loud (C-7).* A non-SQLite or unreadable file, `database is
     locked` after a 30 s busy timeout, malformed JSON, a row that fails its
     model, or a failed write or commit raise `MapReuseStoreError`. Only
     "no row for this key" is a miss.
   - *Membership and deletion.* The published run's members are the rows
     with `last_run = current_run`. A key is `deleted` when it was a member
     of the previous published run and is absent from this run's items; its
     row is kept. A key that reappears is compared with its kept row: match
     → `unchanged`, mismatch → `changed`. `new` means no row. Rows are
     never pruned and have no TTL.
2. **Identity.** `map_reuse_load` checks all of this before returning;
   any violation raises `MapReuseIdentityError`.
   - *Key.* `key` names an item field whose value is a non-empty `str` or
     an `int` (not `bool`). Missing, null, another type, or two items with
     the same encoded key raise.
   - *Version.* Omitted `version` → SHA-256 of the UTF-8 bytes of
     `json.dumps(item, sort_keys=True, separators=(",", ":"),
     ensure_ascii=False, allow_nan=False)`; an item that does not serialize
     raises. A named `version` field must be present with a non-null `str`
     or `int`, never `bool`; missing or null raises, never falls back to hashing.
   - *Paths.* Absolute `base_dir` stays absolute; relative `base_dir` resolves
     against the process working directory at load. Each `node_version_files`
     entry resolves against that directory. Resolve symlinks; reject missing,
     unreadable, non-file, escaping or duplicate normalized paths. The pilot's
     preparation tool supplies its absolute directory from `Path(__file__)`,
     not an assumed repository cwd. Manifests resolve implementation paths,
     not arbitrary arguments ([tool manifests](../reference/graph-yaml.md#tool-manifests-fr-768)).
   - *Computation signature.* Keep the store column name `node_version`;
     its value is SHA-256 of the canonical JSON of
     `{"contract": "map_reuse/1", "provider": <provider>, "model": <model>,
     "inputs": <computation_inputs>, "files": {<normalized relative POSIX
     path>: <sha256 of raw bytes>}}`. Provider and model are required resolved
     non-empty strings. `computation_inputs` is an explicit JSON object,
     validated through Pydantic JSON-value types; non-finite numbers and
     non-JSON values raise. No discovery of state reads or environment values.
     Callers must enumerate every non-item input affecting classification.
     The pilot freezes this object to `rubric`, `problem_labels`,
     `surface_labels`, and `temperature: 0`; it hashes its graph, classification
     prompt and preparation/reducer tool file. Effective provider is `azure`
     and model is resolved once before both signature construction and calls.
     Changing synthesis-only inputs does not invalidate classification.
   - *Reuse rule.* An item is reused when key, version and node version
     match its `items` row; otherwise it goes to `todo`.
3. **Failures (operator rule 2026-09-25; FR-1073).** A stored `failed` row
   whose key, version and node version match is carried: listed in
   `carried_failures`, not dispatched, counted as `carried_failed`.
   Because it is not dispatched, FR-1073's `min_success` does not count it.
   It must still appear as a failed row in whole-population reconciliation
   (item 8). To deliberately retry one unchanged failed item, the caller may
   supply a changed named version: a canonical JSON string containing both
   the unchanged source version and a caller-owned retry epoch. This is an
   explicit invalidation, not a claim that source content changed. No new
   retry option or automatic failure-class policy is added. A changed
   computation signature also invalidates failures. Tolerated and untolerated
   map failures are stored; tolerance is diagnostic, not proof of success.

   **Typed load plan (second judgement R-1).** The public result is
   `MapReuseLoad {store_path, base_run, node_version, current, todo,
   carried_failures, counts}`. `store_path` is absolute and save uses it;
   callers cannot accidentally save the plan into another store.
   - `current: list[ReuseItem]` contains every current input in order.
     `ReuseItem {key: str, version: str, current_index: int,
     node_version: str, classification: Literal[new, changed, unchanged,
     carried_failed]}` stores canonical encoded key/version and a
     non-negative current index. Keys are unique and indices exactly
     `0..len(current)-1`.
   - `todo: list[ReuseTodo]` contains only new/changed entries in current
     order. `ReuseTodo {current_index: int, item: dict[str, JsonValue]}`
     points to exactly one current record and carries the original item.
     The pilot unwraps `item` for its classification call.
   - `StoredFailure {error_type: str, message: str, node: str,
     tolerated: bool}` omits dispatch and index.
     `KeyedFailure {key: str, current_index: int, failure: StoredFailure}`
     uses the encoded key and this load's index; `carried_failures` is a
     list of these, never old `MapFailure` records.
   - `ReuseCounts {new, changed, unchanged, carried_failed, deleted}` has
     non-negative integer fields, derived from the plan and prior membership.
     `new + changed + unchanged + carried_failed == len(current)`;
     `deleted` counts previous members absent now. Save validates the plan
     and membership again inside its transaction; aggregates never replace
     the records. All models reject extra fields and invalid scalar types.
4. **Concurrency.** Load reads metadata and item rows in one read transaction;
  it returns `base_run` (the `current_run` it saw, or null). Save publishes only if `current_run`
   still equals `base_run`, checked inside its transaction; otherwise it
   raises `MapReuseConflict` and changes nothing. Two runs started from the
   same store can both spend; only the first to save publishes. No lock is
   held between load and save, so a killed, failed or abandoned run leaves
   nothing to clean up.
5. **Save (FR-1073).** `map_reuse_save(reuse, results, failures)` uses
  `reuse.store_path`. One `BEGIN IMMEDIATE` transaction checks
  `base_run`; maps each success to its `todo` item by `_map_index`
   ([map_compiler.py L194–L199](../yamlgraph/compile/map_compiler.py#L194-L199))
   and each failure by `MapFailure.index`
   ([map_results.py L18](../yamlgraph/models/map_results.py#L18)); the
  indices together must be exactly `0..len(todo)−1`, once each, else
  `MapReuseIdentityError` and nothing is published. Map that local index
  through `todo.current_index` to the stable key, never directly to the
  original population. Reject boolean/non-integer indices. Strip top-level
  `_map_index` from successful payloads; the pilot also removes any
  `source_index` attribution claim before persistence. Convert failures to
  `StoredFailure`. Save creates a new
   `run_id` (UUID4 hex), upserts `items` for executed keys, sets
   `last_run = run_id` on every current key (executed, unchanged, carried),
   sets `meta.current_run = run_id`, and commits. On any error the
   transaction rolls back and the previous published run stays readable.
   Returns typed `MapReuseSave {run_id: str, counts: ReuseCounts,
   failed: int, failures: list[KeyedFailure]}`. `failed` counts this
   dispatch's failures; `failures` includes new and carried failures rebound
   to current indices. A published run means accounted and durable, not that
   every item succeeded. Publishing precedes consumer acceptance.
6. **Read.** `map_reuse_read(store, run_id)` returns all successful rows
   of the current published run, ordered by encoded key. Read metadata and
   rows in one read transaction. If `current_run != run_id`, raise
   `MapReuseConflict`, never return another run's rows. Historical snapshots
   are not supported. SQL is fixed and parameterized.
   Return `MapReuseReadResult {run_id: str, rows: list[ReuseSuccess]}`;
   `ReuseSuccess {key: StrictStr | StrictInt, result: dict[str, JsonValue]}`
   contains the decoded key separately from the payload. A result's own `key`
   stays under `result` and cannot shadow identity. Failed and deleted rows
   are absent; a published all-failed or empty population yields `rows: []`.
   No published run raises `MapReuseReadError`. There is no field projection,
   ordering argument, limit, filter, pagination or generic query language.
7. **Mid-map crash.** Not survived. After `kill -9` a same-thread resume
   re-runs every finished branch of the open map step (FR-1065 row 5a).
  This FR claims only that a run killed before save leaves the last published
  store unchanged (AC-08); save rollback preserves the prior publication.
  Restart from fresh graph state. Resuming a historical load plan after another
  writer publishes must conflict, not silently refresh. Bounding the loss
  needs a batch loop (row 5b; FR-1065
   question 3) or branch-level store writes; neither is authorized here.
8. **Pilot migration.** `person_profile_census` only, through
   `scripts/author.sh` with a committed brief under
   `feature-requests/authoring-briefs/`. Load sits before `judge_items`
   ([graph.yaml L105](../examples/demos/person_profile_census/graph.yaml#L105)),
   whose items are the `contents` collected by `extract_items`; the brief
  fixes identity to the discovered `item_ref` string (`items` entries),
  pairing current extracted bundles through their extraction indices once
  during preparation. Require one unique item reference and bundle per
  current input. Prepare `{id: item_ref, evidence: parsed_bundle}` items;
  the omitted-version canonical hash covers that evidence, not transient
  dispatch indices. Remove `source_index` from the classification prompt
  and variables: order is not a semantic input. Do not trust any model
  attribution field. The absolute base directory and explicit computation
  inputs are constructed by this preparation tool (item 2).
  `judge_items` declares integer `min_success: 0` and keeps failures separate
  from successes. This preserves branch accounting while allowing save to run
  after any number of classification failures, including all failures.
  It does not loosen extraction: that map remains strict.
   `reduce_pr_ledger` ([tools.py L392](../examples/demos/person_profile_census/tools.py#L392))
  reads published successes using save's `run_id`, and save's key-bearing
  new/carried failures. It joins both to the current `items` and prepared
  evidence by stable key. Missing, duplicate, unknown or multiply attributed
  keys raise before ledger output or synthesis. Recompute ledger
  `source_index` from current ordering; no stored or model-supplied index is
  trusted. Exactly one success or explicit failure must account for each
  current key, including carried failures. Existing row-level validation,
  failed-row reporting, canary and synthesis rules remain; no new coverage
  threshold is introduced (FR-985 remains shelved). An all-failed population
  is saved and accounted but must not produce a successful synthesis; enforce
  that in the pilot reducer. A downstream rejection does not roll back saved
  work. A canary failure similarly stops synthesis after persistence.
  Tests run the actual migrated graph with patched LLM responses and a call
  counter. No provider is called and no live graph run is authorized. The
  four related mechanisms are not migrated.

Not addressed: chunked scheduling (FR-1065 question 3), first-run state or
checkpoint size. Executed results still pass through `collect`, and the
bounded pilot reads all successful records. This version claims saved
classification calls across published runs, not bounded memory or survival
of unpublished branch work.

## Proposed implementation scope (requires re-judgement)

| Deliverable | Surface |
|---|---|
| D-1 | `examples/shared/map_reuse.py`: typed load, save and read functions; lossless plan, stable failure, store and read models |
| D-2 | `examples/shared/map_reuse_load.tool.yaml`, `map_reuse_save.tool.yaml`, `map_reuse_read.tool.yaml` |
| D-3 | Focused identity, invalidation, transaction, publication, failure, corruption and read tests; process-boundary tests for separate-process reuse and interrupted unpublished work |
| D-4 | Removed: no checkpoint-size witness or memory-saving claim |
| D-5 | `person_profile_census` graph/prompt migration through `scripts/author.sh`; preparation and reducer tools; deterministic identity/failure/invalidation graph witnesses ($0) |
| D-6 | Tool-manifest and `examples/shared/README.md` docs, capability/REQ traceability, changelog fragment, FR implementation record, diary entry |

Not authorized: any change under `yamlgraph/`; map compiler, checkpointer,
tool-manifest schema or CLI changes; Redis or LangGraph Store backends;
chunked scheduling; automatic retry policy or state-read analysis; generic
projection, ordering, limit or filter APIs; migrating
`corpus_census`, `file-hook`, `self-portrait` or `ocr_cleanup`; locks or
leases; branch-level writes into the store; any crash-survival claim; live
pilot runs.

Conditions from the second judgement remain constraints on the revised
proposal: C-2 (shared implementation and the explicitly authorized pilot
tools only; no framework change), C-3 (stable identity), C-4 (authoring
route), C-5 (fail loud), C-6 (RED before GREEN; other examples untouched).
C-1's folds are dispositioned above, but scope changes still require a new
judgement. FR-1073 and FR-939 are merged; the pilot keeps overflow rejection
and its existing 500-item cap. A docs merge does not activate these deliverables.

## Acceptance Criteria

Proposed replacement criteria. Unchecked items are implementation obligations,
not claims established by this docs revision. AC-10 now witnesses semantic
invalidation, not checkpoint size.

- [x] AC-01: This FR cites the committed FR-1065 report and its executable two-process SQLite, checkpoint-size and killed-process witnesses, with the gaps named ("Investigation evidence"); selected contracts are folded (items 1–7); the pilot budget is the operator's 2026-09-26 decision ($0 spend, no live storage).
- [ ] AC-02: Typed schema tests create a versioned empty store and reject unsupported schema versions, malformed or model-invalid rows, unreadable stores, and failed writes or commits without turning them into misses.
- [ ] AC-03: The typed load plan retains all current keys and maps each todo entry to its current record. Run 1 over five successful items, then run 2 with one changed version, one removed key and one new key, executes exactly the changed and new items and reports `changed=1`, `new=1`, `unchanged=3`, `deleted=1`; read returns all five current successes, including reused records. Plan/count/membership inconsistencies raise before publication.
- [ ] AC-04: A failed item is carried without executing while identity/version/signature match. The carried record has its stable key and current index, never an earlier dispatch index. A deliberate named-version invalidation retaining the source version and changing only its retry epoch executes that item; no automatic retry or false source-change claim occurs.
- [ ] AC-05: Changing a listed file byte, provider or resolved model re-runs all current items; unchanged inputs give an identical signature across processes. Absolute and relative base directories obey item 2 from a non-repository cwd. Missing, unreadable, escaping, duplicate and non-file paths raise before fan-out.
- [ ] AC-06: Omitted `version` uses the frozen canonical-JSON hash; named missing/null/boolean/unsupported versions, missing/null/boolean/unsupported keys, duplicate encoded keys and non-JSON computation inputs raise before dispatch. String `"1"` and integer `1` remain distinct. Extra model fields and invalid plan indices are rejected.
- [ ] AC-07: Run 2 in a separate process reuses run 1's rows. Two loads from the same published run, then two saves: the first publishes, the second raises `MapReuseConflict` and the store is unchanged by it. A failed save transaction leaves the previous published run readable.
- [ ] AC-08: With no concurrent writer, load leaves the store byte-identical and creates no file when none exists. Kill a separate process after at least one classification finishes but before save: the previous publication stays readable, and a fresh run redoes the unpublished work and can publish. No no-rework claim. A stale plan after another publication raises a conflict.
- [ ] AC-09: Read returns every success of the requested current publication in encoded-key order, excluding failed/deleted records; a result field named `key` cannot shadow decoded item identity. Empty/all-failed published runs return an empty typed list; absent publication raises. A newer publication before read raises a conflict. No query/projection arguments exist.
- [ ] AC-10: On the actual migrated graph, changing only `rubric`, only `problem_labels`, or only `surface_labels` invalidates classifications, including carried failures. Each case records exactly the expected classify calls and verifies the new inputs reached them. Changing only synthesis runtime inputs makes zero classify calls. Merely reordering the population does not change item versions or signatures.
- [ ] AC-11: All three manifests validate through the FR-768 mechanism, resolve `map_reuse.py` relative to the manifests, and expose only the item 1–6 contracts; no `yamlgraph/` file changes.
- [ ] AC-12: With the merged FR-1073 map, interleaved successes and failures map through dispatch-local indices to the right todo records and stable keys. Missing, duplicate, boolean or out-of-range indices raise and publish nothing. Persisted payloads contain no dispatch-local attribution fields; the pilot neither persists nor trusts model `source_index`.
- [ ] AC-13: The pilot is migrated through `scripts/author.sh` and linted. Provider-free graph witnesses prove an unchanged second run makes zero classify calls and produces the same complete key-to-classification ledger. A third run reorders inputs, removes one successful key, changes one item, adds one item and carries one failure: only changed/new items classify, and exactly one correctly attributed ledger row represents every current key. Current source indices are recomputed, not replayed.
- [ ] AC-14: A new capability/REQ entry (IDs picked after enumerating main and open PRs) governs the helpers; every new test carries its marker; `python scripts/req_coverage.py --strict` passes; `reference/graph-yaml.md` §Tool Manifests and `examples/shared/README.md` document the contracts and errors; changelog fragment, FR implementation record and diary entry are present.
- [ ] AC-15: In the migrated graph, one untolerated classification failure does not prevent save: `min_success: 0` allows publication, read returns successes, and the ledger includes that failure. On rerun it remains in the whole-population denominator despite an empty todo list. All-failed and canary-failed runs save outcomes but stop before synthesis. Trace node order and publication, not only final state. Duplicate, missing or unknown ledger keys fail before synthesis; failure rows remain visibly failed, never classified successes.

Test surfaces: `tests/unit/test_fr1076_map_reuse.py` for pure models and
store operations in test-owned temporary paths;
`tests/integration/test_fr1076_map_reuse.py` for separate-process and kill
witnesses; `tests/integration/test_fr1076_person_profile_reuse.py` for actual
graph composition (AC-10, AC-13, AC-15), all provider-free. Do not add a
repository-wide census or a new unit-tier infrastructure dependency.

## Alternatives Considered

| # | Class | Alternative | Disposition |
|---|---|---|---|
| 1 | framework-owned | Reuse inside the map wrapper, keyed by item identity (FR-1065's choice) | **Dissent preserved.** Can write per branch, so survives a crash without a checkpointer. Loses: framework change in `yamlgraph/compile/` for a side effect the three-layer rule places in tools; one hidden mechanism for every map. |
| 2 | graph-owned, shared | Load/save/read tools behind shared manifests | **Chosen.** FR-1065 rejected graph-owned reuse because four graphs reimplemented it with different bugs and the partition node could not see branch failures. A shared manifest gives one implementation; FR-1073's `failures` channel makes failures visible to save. |
| 3 | adapter-owned | FR-1032 extract cache | Composes as the `version` source; cannot cache LLM branch results. |
| 4 | engine-owned | LangGraph `CachePolicy` / Store | Rejected: `CachePolicy` caches failure records and is inert without `compile(cache=...)`; no second backend is planned here. |
| 5 | checkpoint-only | Thread resume ([FR-391](FR-391-time-travel-checkpoint-resume.md)) | Answers "finish this run", not "skip earlier runs", and re-runs every finished branch of the open step after `kill -9` (FR-1065 row 5a). Not used (item 7). |

**is_this_a_graph:** the census is a graph; reuse is a deterministic lookup
per item, so it is Python tools called by the graph, not an LLM stage.

The pilot needs all its current outcomes for an identity-complete ledger,
not a top-50 query. A generic read API and its checkpoint witness are removed
rather than maintained for an imaginary second consumer. Explicit computation
inputs avoid coupling this small reuse tool to FR-955's automatic analysis.
Save-before-reconciliation uses existing map policy, not a new retry or
compiler mechanism. Batch writes or branch persistence would answer a different
crash-recovery promise and remain outside this FR.

## Related

- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §6, §7 J
- Depends on: [FR-1073](FR-1073-map-result-contract.md) (merged, PR #702)
- Evidence: [FR-1065 report](../docs/investigations/fr1065-resumable-map.md) (PR #696)
- Partly supersedes: [FR-1065](FR-1065-resumable-map-investigation.md) (questions 1, 2, 5)
