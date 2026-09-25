# FR-1065 Investigation Report — Resumable Map Probes

**Status:** complete (questions 1, 2, 3-memory, 5; question 3-join and 4 blocked, see Limits)
**Governs:** [FR-1065](../../feature-requests/FR-1065-resumable-map-investigation.md) AC-01–AC-06; evidence for [FR-1076](../../feature-requests/FR-1076-shared-map-reuse-helpers.md) R-1 / AC-01
**Environment:** macOS, Python 3.13 (`.venv`), langgraph 1.2.11, langgraph-checkpoint-sqlite 3.1.1
**Probes:** [tests/fixtures/fr1065/probes.py](../../tests/fixtures/fr1065/probes.py) — minimal stand-alone LangGraph graphs; no `yamlgraph/` code runs.
**Witnesses:** [tests/unit/test_fr1065_resumable_map_probes.py](../../tests/unit/test_fr1065_resumable_map_probes.py) (REQ-YG-689, 12 tests, marked `slow`)

Reproduce the full report (10,000 items, about 15 minutes):

```bash
python tests/fixtures/fr1065/probes.py report > tmp/fr1065-report.json
```

The witness tests run the same probes at smaller sizes:

```bash
pytest tests/unit/test_fr1065_resumable_map_probes.py -q --no-cov
```

## Summary for a reader without context

A "map" runs one step per item (one LLM call per row of a census, for
example). Two things were unknown: whether finished items survive a crash
or a second run, and whether keeping every result in graph state is too
expensive. Findings:

1. A killed process (`kill -9`) loses **every** item of the step that was
   running, including items that had already finished. LangGraph writes a
   step's results to the checkpoint only when the whole step ends.
2. Splitting the map into batches bounds that loss to one batch, and cuts
   peak memory at 10,000 items from 77 MB to 4–5 MB.
3. Keeping results out of state shrinks the final checkpoint about 82×.
4. LangGraph's `SqliteCache` works as a per-item result store inside one
   process, but cannot be a lock, and can crash a second process that opens
   a fresh file at the same moment (intermittent: seen in one of two report
   runs for writers, 7 of 10 rounds for lock claimants).
5. A new run (new thread) reuses nothing; only resuming the same thread
   does.

## Results (10,000 items, 400-byte payload unless stated)

Numbers are from the final report run (`tmp/fr1065-report.json`, not
committed; regenerate with the command above). Where an earlier run of the
same probe differed, both are shown.

| # | Probe | Result |
|---|---|---|
| 1a | `SqliteCache`, 500 concurrent branches, one process | 0 errors, 500 stored; p50 16.8 ms, p95 32.4 ms per set |
| 1b | `SqliteCache`, two writer processes, **fresh** file | **intermittent.** Earlier run: one writer crashed with `sqlite3.OperationalError: database is locked` in `SqliteCache.__init__` (the WAL pragma / `CREATE TABLE`), 500 read back. Final run: no crash, 1,000 read back |
| 1c | `SqliteCache`, two writer processes, file pre-created | 1,000 read back from 2 pids; no errors (both runs) |
| 1d | Lease via `SqliteCache` get-then-set, fresh file | final run: 7 claimant crashes (`database is locked`) and 3 rounds with two winners, of 10; earlier run: a crash in all 10 |
| 1e | Lease via `SqliteCache` get-then-set, pre-created | 10 of 10 rounds **both** claimants won — no exclusion (both runs) |
| 1f | Lease via SQLite `INSERT` on a `UNIQUE` key | 0 of 10 rounds with two winners; 0 crashes (both runs) |
| 2a | Results in state (`collect`, add reducer) | final checkpoint 4,190,046 B; pending writes 4,598,851 B; db 20,545,536 B; 125 s |
| 2b | Results in a side store, state keeps 50 selected | final checkpoint 51,208 B (82× smaller); pending writes 459,938 B; checkpoint db 7,344,128 B + side store 4,587,520 B; 167 s |
| 3 | One-step fan-out vs batch loop of 500 | peak 77.2 MB / 375 s vs 4.38 MB / 25.1 s (earlier run: 285 s vs 21.8 s); the batch loop fits LangGraph's default recursion limit (10,007) |
| 5a | `kill -9` mid-step, one-step map, 20 items, `durability` default and `sync` | 6 items finished before the kill; resume ran all 20 again (6 finished items re-ran); final results correct |
| 5b | `kill -9` mid-step, batch loop of 4, both durabilities | 6 finished (batch 1 + 2 items of batch 2); resume ran 16 (only the 2 open-batch items re-ran); results correct |
| 5c | `SIGINT` mid-step, both durabilities | the running step finished all 20 before exit; resume made 0 calls |
| 5d | Same items, new `thread_id` | 40 calls for 20 items: nothing reused across runs |
| 6 | Node `CachePolicy` with and without `compile(cache=...)` | 2 calls without a cache, 1 with `InMemoryCache`; no `yamlgraph/` route passes `cache=` (AST witness) |

Raw observations worth reading before the numbers:

- 2a timing is superlinear: 2,000 items took 5.5 s, 10,000 took 121–125 s
  (5× items, about 22× time). The add reducer re-copies the growing list.
- 2b is slower than 2a because the probe serializes side-store inserts
  behind one lock with a commit per insert; this is a probe artifact, not a
  store property. FR-1076 writes once per run in one transaction.
- A first 2b measurement reported the checkpoint db and side store at the
  identical byte size. Cause: both used the file name `store.db`. Fixed
  (`side-store.db`); all numbers above are from the fixed probe.
- 5a trace (`put_writes` timestamps): branches finished at 71–178 ms, but
  their writes reached the checkpointer together at 177–179 ms, at the
  step's end. The two task writes persisted before the kill are the start
  node and the fan-out, not branches.

## Candidate contracts — selected or rejected

| Candidate (FR-1065 "Decided" table, relabelled per judgement R-2) | Verdict | Evidence |
|---|---|---|
| `SqliteCache` as the durable result store | **Rejected** | 1b: fresh-file race can crash a second process; TTL-only, `INSERT OR REPLACE`, no single-copy guarantee |
| `SqliteCache` as the run lock | **Rejected** | 1d, 1e |
| SQLite `UNIQUE`-key insert as the run lock (lease) | **Selected** | 1f; FR-1076 R-2 adds the token and recovery rules |
| Results read from a store; state keeps only what consumers select | **Selected** (human decision 2026-09-25, FR-1065 status) | 2a vs 2b |
| Thread resume as crash recovery for a one-step map | **Rejected** | 5a: every finished branch of the open step re-runs |
| Batch loop as crash-loss bound | **Selected for a fix FR** | 5b: loss bounded to the open batch |
| Cross-run reuse from the checkpointer | **Rejected** | 5d |
| FR-032 node `CachePolicy` for map reuse | **Rejected** | 6: inert in yamlgraph; would also cache failure records |
| Item key = the item's own ID; version = source change signal or canonical-JSON hash; node version = hash of definition files + model | **Carried unwitnessed to FR-1076** | no probe can select these; FR-1076 R-3 freezes them byte-exact with its own tests |
| Permanent failures carried while key/version/node version match | **Carried to FR-1076** (operator rule 2026-09-25) | no engine behavior involved |
| JSONL ledger with two-run lock | **Replaced** by the FR-1076 SQLite store + lease | 1f |

## Consumer migration counts (question 2)

| Contract | Consumers to migrate | Checkpoint bytes at 10k |
|---|---|---|
| Materialise (keep `collect` in state) | 0 | 4,190,046 final; 20.5 MB db |
| Store-read (selected) | all readers of a map's `collect` key | 51,208 final; 7.3 MB db + 4.6 MB store |

Counts for store-read, two methods that disagree:

- Plan `docs/issues-2026-09-24.md` §6: 26 consumers (method not recorded; not reproduced here).
- Regex census in this investigation (2026-09-25): 70 map nodes with
  `collect` in 54 graph files under `examples/`; 89 (graph, key, file)
  reader pairs in 74 distinct files. The regex matches `state.<key>`,
  `state["<key>"]`, `{<key>`, `{{ <key>` and `.get("<key>")` in the graph's
  own directory. It over-counts (a downstream map's `over:` reading the key
  is a consumer, but a same-named key in an unrelated file in the same
  directory is not) and is an **upper bound**.
- FR-1073's census (22 `_error` sites in 16 files, plus one) counts only
  failure-row readers, a subset.

FR-1076 does not migrate these: it migrates one graph (`person_profile_census`)
and each further migration is its own change.

## What blocks what

- **FR-1076 AC-08 / C-6 (same-thread crash survival) is RED against the
  current engine for a one-step map (5a).** Per FR-1076 R-5 and C-6, that
  blocks FR-1076 enforcement as written. Two routes exist, each needing its
  own judged FR: (a) a batch loop around the map (5b bounds loss to one
  batch; FR-1065 question 3), or (b) branch-level writes into the reuse
  store. FR-1076's own scope forbids both, so its AC-08 must be narrowed to
  "resume re-runs at most the open step" or wait for one of those FRs.
- **Question 3, join compatibility:** FR-944's map-to-map join and
  FR-1064's join node were not composed with the batch loop. Blocked:
  FR-1064 is split and its join half is not refiled.
- **Question 4 (node-version inputs under projection):** blocked on FR-955
  (judged, not implemented); there is no projected branch state to probe.

## Limits

- Sync `invoke` only. Async (`ainvoke`) and the yamlgraph map wrapper were
  not probed.
- `RedisCache` not probed (no Redis in the environment).
- One machine, two report runs; the witness tests repeat the
  deterministic claims at small sizes on every run. The fresh-file race
  (1b, 1d) is timing-dependent and has no witness test; only the
  pre-created-file behavior is pinned.
- Memory is Python heap (`tracemalloc`), not RSS.
- The kill point is "after 6 finished items", polled every 5 ms from the
  parent; the 5a/5b counts assume no seventh item finishes inside that
  window (items take 50 ms, 2 at a time).

## Pilot budget (judgement R-3; accepted by operator 2026-09-25)

For the `person_profile_census` pilot under FR-1076:

- **Spend:** run 1 costs what a census run costs today. Run 2 over an
  unchanged subject: 0 LLM calls (FR-1076 AC-13). Run 2 over a changed
  subject: at most the changed and new items.
- **Storage:** one SQLite store per subject, capped at 50 MB. At the
  probe's 400 bytes per result, 10,000 items used 4.6 MB.
- **Probe spend:** this investigation made no LLM calls.
