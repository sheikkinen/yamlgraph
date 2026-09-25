# Feature Request: Shared map reuse helpers — skip items finished in earlier runs, read results from a store

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1076-shared-map-reuse-helpers.judgement.md)); authority gated on R-1 (FR-1065 investigation witnesses), R-2–R-5 folded, and FR-1073 merged. No implementation authority yet.
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
[FR-1065](FR-1065-resumable-map-investigation.md) (APPROVED WITH REVISIONS,
investigation only) — chose framework-owned reuse and kept graph-owned reuse
as dissent; this FR reverses that choice for the reasons in Alternatives, and
takes over FR-1065's reuse questions 1, 2 and 5. Chunked scheduling
(question 3) and node-version inputs under projection (question 4) stay in
FR-1065.
[FR-1073](FR-1073-map-result-contract.md) (Proposed) — supplies the
`failures` channel, `_map_index` on results and `_map_verdict`; this FR
depends on it.
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
          version: updated_at, node_version_files: [prompts/judge_item.yaml],
          model: "{state.model}" }
  state_key: reuse            # {todo, carried_failures, run_id, node_version, counts}
judge_items:
  type: map
  over: "{state.reuse.todo}"
  # ... FR-1073 contract: collect + failures + min_success
reuse_save:   # tool: map_reuse_save
  args: { store: "{state.store}", reuse: "{state.reuse}",
          results: "{state.judgements}", failures: "{state.judgement_failures}" }
  state_key: reuse_stats      # {new, changed, unchanged, failed, carried_failed, deleted}
report:       # tool: map_reuse_read → only what the consumer needs
  args: { store: "{state.store}", fields: [id, score], limit: 50, order_by: score }
```

1. **Store.** One SQLite file per `store` path; one row per key:
   `key, version, node_version, status (ok|failed), result_json, run_id`.
   Only `map_reuse_save` writes, once per run, in one transaction — no
   concurrent branch writes. A second run on the same store while one is
   open raises (lease row taken by load, released by save).
2. **Load.** `version` is the named item field, or the SHA-256 of the item's
   canonical JSON when absent. `node_version` is the SHA-256 of the listed
   files plus `model`. An item is reused when key, version and node_version
   all match a stored row; duplicate keys raise. `todo` holds the rest.
3. **Failures (operator rule, 2026-09-25).** A stored failure is carried —
   reported in `carried_failures`, not re-run — while key, version and
   node_version match. To retry, the loader changes the item's version (for
   example appends a retry epoch) or the prompt/model changes. No separate
   retry setting; in-run transient retry belongs to the FR-1064 retry half.
4. **Save.** Maps each result and failure back to its key through
   `_map_index` into `todo` (FR-1073), upserts rows, and counts keys in the
   store absent from this run's items as `deleted` (rows kept, marked).
5. **Read.** Returns selected fields, filter, order and limit from `ok` rows
   of the latest run's key set. Consumers — prompt or Python — get only what
   they read into state (operator decision for FR-1065: consumers read from
   the store).
6. **Mid-map crash.** Covered by the checkpointer: completed branch writes
   are stored per task, so resuming the same thread does not re-run them.
   Witnessed, not assumed (AC-6).
7. **Migration.** `person_profile_census` only, through the graph-authoring
   route (`scripts/author.sh`). The four existing reinventions are not
   migrated by this FR; each migration is its own change.

Not addressed: chunked scheduling at 100k+ items (FR-1065 question 3); this
run's new results still pass through `collect` state once.

## Acceptance Criteria

- [ ] AC-1: run 1 over five items, run 2 with one item version changed, one removed, one new → exactly the changed and new items execute; counts `changed=1 new=1 unchanged=3 deleted=1`.
- [ ] AC-2: a failed item from run 1 is carried in run 2 without executing; after its version is bumped it executes.
- [ ] AC-3: changing a file in `node_version_files` or `model` re-runs all items.
- [ ] AC-4: two processes: run 1 in one process, run 2 in another reuses run 1's rows; a second concurrent run on the same store raises.
- [ ] AC-5: duplicate keys raise in load before any branch runs.
- [ ] AC-6: `kill -9` during the map with a SQLite checkpointer, resume the thread → finished branches do not re-execute (count sub-node calls). If RED, the FR records it and names branch-level writes as the required change before claiming crash survival.
- [ ] AC-7: `map_reuse_read` with `fields`/`limit` returns only those; checkpoint bytes of the consumer step with read vs full `collect`, reported for a 10k-item fixture.
- [ ] AC-8: `person_profile_census` migrated via `scripts/author.sh`; second smoke run makes zero classify calls (raw log quoted).
- [ ] Tests carry new REQ IDs; manifests documented in `reference/graph-yaml.md` §tool manifests.

## Alternatives Considered

| # | Class | Alternative | Disposition |
|---|---|---|---|
| 1 | framework-owned | Reuse inside the map wrapper, keyed by item identity (FR-1065's choice) | **Dissent preserved.** Can write per branch, so survives a crash without a checkpointer. Loses: framework change in `yamlgraph/compile/` for a side effect the three-layer rule places in tools; one hidden mechanism for every map. |
| 2 | graph-owned, shared | Load/save/read tools behind shared manifests | **Chosen.** FR-1065 rejected graph-owned reuse because four graphs reimplemented it with different bugs and the partition node could not see branch failures. A shared manifest gives one implementation; FR-1073's `failures` channel makes failures visible to save. |
| 3 | adapter-owned | FR-1032 extract cache | Composes as the `version` source; cannot cache LLM branch results. |
| 4 | engine-owned | LangGraph `CachePolicy` / Store | Rejected: `CachePolicy` caches failure records and is inert without `compile(cache=...)`; LangGraph Store is a possible later backend for the same tool interface. |
| 5 | checkpoint-only | Thread resume ([FR-391](FR-391-time-travel-checkpoint-resume.md)) | Answers "finish this run", not "skip earlier runs"; adopted for the mid-map crash (item 6). |

**is_this_a_graph:** the census is a graph; reuse is a deterministic lookup
per item, so it is Python tools called by the graph, not an LLM stage.

## Related

- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §6, §7 J
- Depends on: [FR-1073](FR-1073-map-result-contract.md)
- Partly supersedes: [FR-1065](FR-1065-resumable-map-investigation.md) (questions 1, 2, 5)
