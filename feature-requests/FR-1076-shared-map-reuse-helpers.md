# Feature Request: Shared map reuse helpers — skip items finished in earlier runs, read results from a store

**Priority:** HIGH
**Type:** Enhancement
**Status:** Revised 2026-09-26 for re-judgement. The first judgement ([judgement](FR-1076-shared-map-reuse-helpers.judgement.md), APPROVED WITH REVISIONS) cannot be enforced as written: (a) its AC-08 (a resumed thread re-runs no finished branch) is RED against the current engine (FR-1065 report row 5a); (b) FR-1073 merged with a different contract (`MapFailure.index`, map-level `key` cut), which C-3 routes to re-judgement. The operator also cut the store to one items table with no lease ("Deviations from the first judgement"). No implementation authority until `scripts/judge.sh` re-judges this FR.
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

## Deviations from the first judgement

| Judgement demand | This revision | Why |
|---|---|---|
| R-2: tables for items, completed-run membership and lease; unguessable run token; abandoned-lease recovery | Two tables: `meta` and `items`. `items.last_run` marks membership; `meta.current_run` marks the published run. No lease, no token: load writes nothing, and save publishes only if `current_run` still equals the run load saw (item 4). | The lease existed to exclude a second writer. A second concurrent run can only waste spend: save is one transaction and a stale save is refused, so nothing is corrupted. Dropping the lease removes the token, the abandoned-lease procedure, and every crash case that left a lease held. |
| R-5 / AC-08: killed-process resume re-runs no finished branch | No crash claim. Load is read-only, so a killed run leaves the store byte-identical (AC-08). | Row 5a shows the engine re-runs finished branches of the open step; the judgement itself says that fix is a separate FR. |
| R-5 / AC-10: 10,000-item checkpoint witness | 1,000 items, the size FR-1065 already pins in a committed test | 1,000 items already show 4,190,046 B vs 51,208 B; 10× adds runtime, not information. |
| R-3: length-framed node-version hash | SHA-256 of canonical JSON of `{contract, model, files: {relpath: sha256(bytes)}}` | Canonical JSON is unambiguous without hand-rolled framing. |

## Investigation evidence (R-1)

Report [docs/investigations/fr1065-resumable-map.md](../docs/investigations/fr1065-resumable-map.md);
witnesses [tests/unit/test_fr1065_resumable_map_probes.py](../tests/unit/test_fr1065_resumable_map_probes.py)
(REQ-YG-689, marked `slow`) on the stand-alone LangGraph probes in
[tests/fixtures/fr1065/probes.py](../tests/fixtures/fr1065/probes.py).

| Question | Witness | Result | Effect here |
|---|---|---|---|
| SQLite across two processes, and exclusion | `test_sqlite_cache_persists_across_two_writer_processes` (L36), `test_sqlite_cache_gives_no_lease_exclusion` (L44), `test_sqlite_unique_insert_lease_excludes_second_process` (L50) | `SqliteCache` rejected as store and as lock; a `UNIQUE`-key insert gave 0 of 10 double winners (report row 1f) | plain SQLite store; `BEGIN IMMEDIATE` save with a compare-and-set on `current_run` instead of a lease (items 1, 4) |
| Checkpoint bytes, `collect` vs store-selected | `test_store_results_shrink_final_checkpoint` (L57), 1,000 items; 10,000 via `python tests/fixtures/fr1065/probes.py report` | final checkpoint 4,190,046 B vs 51,208 B (rows 2a/2b) | consumers read from the store (item 6) |
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
  whose output is not committed. This FR's AC-10 uses 1,000 items.
- **Fresh-file race unwitnessed.** Report rows 1b/1d (`database is locked`
  while a second process creates a fresh file) have no test. Item 1 turns
  that error into `MapReuseStoreError`, never a miss.

## Summary

Three shared Python tools with manifests — `map_reuse_load`,
`map_reuse_save`, `map_reuse_read` — let any graph skip map items finished in
an earlier run and let consumers read results from a SQLite store instead of
state. No framework change.

## Value Statement

A census author re-runs a map over a changing subject and pays only for what
changed, with counts of new, changed, unchanged, failed and deleted items.

## Problem

Four graphs (`corpus_census`, `file-hook`, `self-portrait`, `ocr_cleanup`)
each built their own skip-if-done logic, with different bugs (plan §5.1). The
map has no cross-run memory, and all results live in state, so every
checkpoint copies them.

## Ideal Result

A graph adds a load node before its map and a save node after it; run 2 over
an unchanged subject makes zero LLM calls, and a consumer reads only the
results it needs from the store.

## Proposed Solution

`examples/shared/map_reuse.py` plus `map_reuse_load.tool.yaml`,
`map_reuse_save.tool.yaml`, `map_reuse_read.tool.yaml`.

```yaml
reuse_load:   # tool: map_reuse_load
  args: { store: "{state.store}", items: "{state.items}", key: id,
          version: updated_at, base_dir: examples/demos/my_census,
          node_version_files: [graph.yaml, prompts/judge_item.yaml],
          model: "{state.model}" }
  state_key: reuse    # MapReuseLoad {todo, carried_failures, base_run, node_version, counts}
judge_items:
  type: map
  over: "{state.reuse.todo}"
  # FR-1073: successes in collect (each with _map_index), MapFailure records in failures
  collect: judgements
  failures: judgement_failures
reuse_save:   # tool: map_reuse_save
  args: { store: "{state.store}", reuse: "{state.reuse}",
          results: "{state.judgements}", failures: "{state.judgement_failures}" }
  state_key: reuse_stats   # {new, changed, unchanged, failed, carried_failed, deleted}
report:       # tool: map_reuse_read → only what the consumer needs
  args: { store: "{state.store}", fields: [key, score], limit: 50,
          order_by: score, descending: true }
  state_key: top           # MapReuseReadResult {run_id, rows}
```

1. **Store.** One SQLite file per `store` path. Every row passes through a
   private Pydantic model on write and on read.

   | Table | Columns |
   |---|---|
   | `meta` | `name TEXT PRIMARY KEY, value TEXT NOT NULL`; rows `schema_version = 1`, `current_run` (absent until the first publish) |
   | `items` | `key TEXT PRIMARY KEY, version TEXT NOT NULL, node_version TEXT NOT NULL, status TEXT NOT NULL CHECK (status IN ('ok','failed')), result_json TEXT NOT NULL, last_run TEXT NOT NULL` — latest record per key; `result_json` is the success dict or the `MapFailure` |

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
     or `int`; missing or null raises, never falls back to hashing.
   - *Node version.* `base_dir` is required and every `node_version_files`
     entry resolves against it. The graph passes its own directory because
     a python tool receives no graph path (manifests resolve only their own
     paths, [reference/graph-yaml.md §Tool Manifests](../reference/graph-yaml.md#tool-manifests-fr-768)).
     A path that is missing, unreadable, not a regular file, outside
     `base_dir`, or a duplicate after normalization raises. The node
     version is the SHA-256 of the canonical JSON (the `version` rule
     above) of `{"contract": "map_reuse/1", "model": <model>, "files":
     {<POSIX path relative to base_dir>: <sha256 hex of raw bytes>}}`;
     `model` is a required non-empty string.
   - *Reuse rule.* An item is reused when key, version and node version
     match its `items` row; otherwise it goes to `todo`.
3. **Failures (operator rule 2026-09-25; FR-1073).** A stored `failed` row
   whose key, version and node version match is carried: listed in
   `carried_failures`, not dispatched, counted as `carried_failed`.
   Because it is not dispatched, FR-1073's `min_success` does not count it.
   To retry, the loader changes the item's version (for example appends a
   retry epoch) or the prompt/model changes. Tolerated and non-tolerated
   `MapFailure` records are both stored as `failed`. In-run transient retry
   belongs to the FR-1064 retry half.
4. **Concurrency.** Load only reads; it returns `base_run` (the
   `current_run` it saw, or null). Save publishes only if `current_run`
   still equals `base_run`, checked inside its transaction; otherwise it
   raises `MapReuseConflict` and changes nothing. Two runs started from the
   same store can both spend; only the first to save publishes. No lock is
   held between load and save, so a killed, failed or abandoned run leaves
   nothing to clean up.
5. **Save (FR-1073).** One `BEGIN IMMEDIATE` transaction: check
   `base_run`; map each success to its `todo` item by `_map_index`
   ([map_compiler.py L194–L199](../yamlgraph/compile/map_compiler.py#L194-L199))
   and each failure by `MapFailure.index`
   ([map_results.py L18](../yamlgraph/models/map_results.py#L18)); the
   indices together must be exactly `0..len(todo)−1`, once each, else
   `MapReuseIdentityError` and nothing is published. Save creates a new
   `run_id` (UUID4 hex), upserts `items` for executed keys, sets
   `last_run = run_id` on every current key (executed, unchanged, carried),
   sets `meta.current_run = run_id`, and commits. On any error the
   transaction rolls back and the previous published run stays readable.
   Returns `{run_id, new, changed, unchanged, failed, carried_failed,
   deleted}`.
6. **Read.** `map_reuse_read(store, fields, limit, order_by="key",
   descending=False)` returns the rows with `last_run = current_run` and
   `status = 'ok'`. Failed, carried-failed and deleted keys are excluded;
   an unpublished run is invisible.
   - `fields`: non-empty, no duplicates, each `key` or a top-level field of
     the stored result; a field missing from any selected row raises.
   - `limit`: `int` in 1..10,000 (not `bool`). `order_by`: one field from
     the same set. Ties break by encoded key, ascending.
   - SQL is fixed parameterized statements; projection and ordering run on
     model-validated rows, so no argument reaches SQL as an identifier.
   - Returns `MapReuseReadResult {run_id, rows}`, each row holding exactly
     `fields` in order; no match → `rows: []`. Invalid arguments, no
     published run, or `order_by` values that do not compare raise
     `MapReuseReadError`. There is no filter argument.
7. **Mid-map crash.** Not survived. After `kill -9` a same-thread resume
   re-runs every finished branch of the open map step (FR-1065 row 5a).
   This FR claims only that a killed run leaves the store unchanged
   (AC-08). Bounding the loss needs a batch loop (row 5b; FR-1065
   question 3) or branch-level store writes; neither is authorized here.
8. **Pilot migration.** `person_profile_census` only, through
   `scripts/author.sh` with a committed brief under
   `feature-requests/authoring-briefs/`. Load sits before `judge_items`
   ([graph.yaml L105](../examples/demos/person_profile_census/graph.yaml#L105)),
   whose items are the `contents` collected by `extract_items`; the brief
   names the PR identity field used as `key` (load raises if it is absent).
   `reduce_pr_ledger` ([tools.py L392](../examples/demos/person_profile_census/tools.py#L392))
   reads reused rows from the store, not only this run's `findings`. Per
   the 2026-09-26 decision both runs are deterministic: the witness test
   patches the LLM factory, so no provider is called and no live graph run
   happens. The four existing reinventions are not migrated.

Not addressed: chunked scheduling (FR-1065 question 3). This run's executed
results still pass through `collect` once (an FR-1073 append list), so the
checkpoint saving applies to reused items and to consumers that read the
store.

## Scope (frozen by judgement)

| Deliverable | Surface |
|---|---|
| D-1 | `examples/shared/map_reuse.py`: typed load, save and read functions plus private typed store models |
| D-2 | `examples/shared/map_reuse_load.tool.yaml`, `map_reuse_save.tool.yaml`, `map_reuse_read.tool.yaml` |
| D-3 | Unit tests for identity, persistence, transactions, publish conflicts, failures, reads and corruption, plus one separate-process reuse test |
| D-4 | 1,000-item checkpoint-size witness |
| D-5 | `person_profile_census` migration through `scripts/author.sh`: lint, two deterministic runs with a call counter (no live run; $0) |
| D-6 | Tool-manifest and `examples/shared/README.md` docs, capability/REQ traceability, changelog fragment, FR implementation record, diary entry |

Not authorized: any change under `yamlgraph/`; map compiler, checkpointer,
tool-manifest schema or CLI changes; Redis or LangGraph Store backends;
chunked scheduling; retry policy; SQL or expression filters; migrating
`corpus_census`, `file-hook`, `self-portrait` or `ocr_cleanup`; locks or
leases; branch-level writes into the store; any crash-survival claim; live
pilot runs.

Conditions carried from the first judgement: C-4 (runtime code only under
`examples/shared/`), C-5 (pilot edits only through `scripts/author.sh`),
C-7 (fail loud; items 1, 2, 4, 6), C-8 (RED before GREEN; the four
reinventions untouched). C-3 is met: FR-1073 merged (PR #702) and items 2
and 5 use its final contract.

## Acceptance Criteria

The first judgement's criteria, changed where "Deviations" says: AC-07,
AC-08 and AC-10 rewritten; AC-01 and AC-13 for the $0 decision; AC-12 for
FR-1073's final contract.

- [x] AC-01: This FR cites the committed FR-1065 report and its executable two-process SQLite, checkpoint-size and killed-process witnesses, with the gaps named ("Investigation evidence"); selected contracts are folded (items 1–7); the pilot budget is the operator's 2026-09-26 decision ($0 spend, no live storage).
- [ ] AC-02: Typed schema tests create a versioned empty store and reject unsupported schema versions, malformed or model-invalid rows, unreadable stores, and failed writes or commits without turning them into misses.
- [ ] AC-03: Run 1 over five items, then run 2 with one changed version, one removed key and one new key, executes exactly the changed and new items and reports `changed=1`, `new=1`, `unchanged=3`, `deleted=1`; a read of run 2 returns all five current keys, including the three unchanged, and not the deleted key.
- [ ] AC-04: A failed item from run 1 is carried in run 2 without executing; after only its version changes it executes. `failed` and `carried_failed` counts and run membership are asserted separately.
- [ ] AC-05: One changed byte in any node-version file, or a changed `model`, re-runs all current items; unchanged inputs give an identical node version across processes. A missing or unreadable file raises before fan-out.
- [ ] AC-06: Omitted `version` uses the frozen canonical-JSON hash; a named but missing version field, a missing, null or unsupported key, or a duplicate encoded key raises in load before any branch runs.
- [ ] AC-07: Run 2 in a separate process reuses run 1's rows. Two loads from the same published run, then two saves: the first publishes, the second raises `MapReuseConflict` and the store is unchanged by it. A failed save transaction leaves the previous published run readable.
- [ ] AC-08: Load leaves the store file byte-identical (and creates no file when none exists), so a run killed at any point before save leaves the store unchanged; a following run loads and publishes normally.
- [ ] AC-09: `map_reuse_read` reads only the published run; projection, limit, ascending and descending order, key tie-break, unknown- and duplicate-field rejection, invalid-limit rejection, and exclusion of failed and deleted rows match item 6.
- [ ] AC-10: On a deterministic 1,000-item fixture, run 2 over the unchanged fixture (empty `todo`) followed by a 50-row `map_reuse_read`: the consumer step's checkpoint holds only the requested projection and an empty `collect`, serializes to fewer bytes than run 1's full-`collect` checkpoint, and both exact byte counts and the command are recorded in this FR.
- [ ] AC-11: All three manifests validate through the FR-768 mechanism, resolve `map_reuse.py` relative to the manifests, and expose only the item 1–6 contracts; no `yamlgraph/` file changes.
- [ ] AC-12: With the merged FR-1073 map, an integration fixture maps successes by `_map_index` and failures by `MapFailure.index` to the right `todo` keys, including interleaved success/failure order; out-of-range, duplicate or missing indices raise and publish nothing.
- [ ] AC-13: `person_profile_census` is migrated through `scripts/author.sh`; its authoring report records lint; a deterministic test runs the migrated graph twice with a patched LLM factory and a call counter: run 2 over the unchanged subject makes exactly zero `classify_pr` calls, and neither run calls a provider.
- [ ] AC-14: A new capability/REQ entry (IDs picked after enumerating main and open PRs) governs the helpers; every new test carries its marker; `python scripts/req_coverage.py --strict` passes; `reference/graph-yaml.md` §Tool Manifests and `examples/shared/README.md` document the contracts and errors; changelog fragment, FR implementation record and diary entry are present.

Test surfaces: `tests/unit/test_fr1076_map_reuse.py` (AC-02–AC-12; the
separate-process case marked `slow`),
`tests/unit/test_fr1076_person_profile_reuse.py` (AC-13).

## Alternatives Considered

| # | Class | Alternative | Disposition |
|---|---|---|---|
| 1 | framework-owned | Reuse inside the map wrapper, keyed by item identity (FR-1065's choice) | **Dissent preserved.** Can write per branch, so survives a crash without a checkpointer. Loses: framework change in `yamlgraph/compile/` for a side effect the three-layer rule places in tools; one hidden mechanism for every map. |
| 2 | graph-owned, shared | Load/save/read tools behind shared manifests | **Chosen.** FR-1065 rejected graph-owned reuse because four graphs reimplemented it with different bugs and the partition node could not see branch failures. A shared manifest gives one implementation; FR-1073's `failures` channel makes failures visible to save. |
| 3 | adapter-owned | FR-1032 extract cache | Composes as the `version` source; cannot cache LLM branch results. |
| 4 | engine-owned | LangGraph `CachePolicy` / Store | Rejected: `CachePolicy` caches failure records and is inert without `compile(cache=...)`; LangGraph Store is a possible later backend for the same tool interface. |
| 5 | checkpoint-only | Thread resume ([FR-391](FR-391-time-travel-checkpoint-resume.md)) | Answers "finish this run", not "skip earlier runs", and re-runs every finished branch of the open step after `kill -9` (FR-1065 row 5a). Not used (item 7). |

**is_this_a_graph:** the census is a graph; reuse is a deterministic lookup
per item, so it is Python tools called by the graph, not an LLM stage.

## Related

- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §6, §7 J
- Depends on: [FR-1073](FR-1073-map-result-contract.md) (merged, PR #702)
- Evidence: [FR-1065 report](../docs/investigations/fr1065-resumable-map.md) (PR #696)
- Partly supersedes: [FR-1065](FR-1065-resumable-map-investigation.md) (questions 1, 2, 5)
