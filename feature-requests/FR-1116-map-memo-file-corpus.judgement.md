# Judgement: FR-1116 Map memo for file corpora — re-run a map only over files that changed

**Verdict:** APPROVED WITH REVISIONS — the file-corpus memo is a feasible, contribution-sized use of the existing split/map/merge seam, but authority activates only after the merged dispatch identity, policy validation, typed persistence boundary, and concurrency witnesses are frozen in the FR.

**Reviewed against:** `feature-requests/FR-1116-map-memo-file-corpus.md`; `feature-requests/FR-1076-shared-map-reuse-helpers.md`; `feature-requests/FR-1076-shared-map-reuse-helpers.judgement.md`; `feature-requests/FR-1073-map-result-contract.md`; `feature-requests/FR-1113-meta-map-demo.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-773-shared-document-splitter-manifest.md`; `docs/investigations/fr1065-resumable-map.md`; `docs/issues-2026-09-24.md` sections 5.1 and 6; `reference/graph-yaml.md` sections "`type: tool_call`" and "Tool Manifests"; `examples/demos/meta_map/graph.yaml`; `examples/demos/meta_map/subgraphs/summarize_one.yaml`; `examples/demos/meta_map/tools.py`; `examples/demos/meta_map/README.md`; `examples/shared/split_document.py`; `examples/shared/split_document.tool.yaml`; `yamlgraph/models/map_results.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/compile/map_contract.py`; `yamlgraph/compile/node_compiler.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/node_factory/tool_nodes.py`; `yamlgraph/tools/python_tool.py`; `yamlgraph/tools/tool_builders.py`; `yamlgraph/utils/expressions.py`; `tests/unit/test_fr778_tool_call_on_error.py`; `.gitignore`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

**Prior art:** dispositioned in the parent FR header ([FR-1116](FR-1116-map-memo-file-corpus.md) — FR-1076 superseded, FR-897 unrelated, FR-1065/1073/032/768/773).

## What is sound

The scope is materially smaller than the superseded design. FR-1116 removes run membership, compare-and-set publication, deletion accounting, querying, checkpoint-size claims, and generic item/version modes, while retaining only the split and merge needed by the named consumer (`FR-1116:29-36,50-65,98-104,187-191`; `FR-1076:241-296`). That is the minimal path from the stated first event—an unchanged second `meta_map` run—to zero repeated `describe` calls (`FR-1116:9-11,74-80`).

The problem is real and supported by committed evidence. `meta_map` currently dispatches its entire path list with `min_success: 0.9` and reads successes, failures, and the map verdict by dispatch-local index (`examples/demos/meta_map/graph.yaml:65-83`; `examples/demos/meta_map/tools.py:154-180,194-205`). The investigation proves that a new run reuses nothing through the checkpointer, that a killed open map step re-runs completed branches, and that `SqliteCache` is not a lock or a cross-run identity mechanism (`docs/investigations/fr1065-resumable-map.md:20-40,45-66,94-116`). The proposed row identity—path bytes plus a computation signature—addresses that evidence without claiming crash survival (`FR-1116:98-140,163-167`).

The substituted research is substantive enough for the FR-890 gate. Six distinct solution classes are dispositioned; the framework-owned alternative is preserved as the stronger long-term option; FR-1076, FR-1065, FR-032, and the graph-local reinventions are distinguished; and `is_this_a_graph` is answered (`FR-1116:207-219`). This satisfies the doctrine's alternative-record route rather than merely shape-checking a `Research` field (`.github/skills/judge-fr/doctrine.md:118-130`).

Feasibility and architecture alignment are strong. FR-768 manifests translate to existing Python tool declarations, manifest paths resolve relative to the manifest, and the feeder precedent exposes a tool result through `<state_key>.result` (`reference/graph-yaml.md:1575-1625,1630-1648`). The loader registers the underlying Python function directly for `tool_call`, and `on_error: fail` raises when that callable raises (`yamlgraph/compile/graph_loader.py:291-307`; `yamlgraph/node_factory/tool_nodes.py:99-115,121-169`; `tests/unit/test_fr778_tool_call_on_error.py:62-82,146-151,196-200`). Deterministic I/O therefore remains under `examples/shared/`, while the graph remains orchestration, consistent with the three-layer rule and the required authoring route (`FR-1116:84-96,168-185`; `.github/copilot-instructions.md:13,190-198`).

The work has one responsibility: memoizing complete per-file map outcomes and proving that composition in one consumer. The store, split, merge, manifests, and `meta_map` migration are one lifecycle rather than orthogonal features. Strategic classification is **Contrib/example**: there are two named consumers and an existing manifest/tool seam with a missing reusable component, while a general framework primitive is explicitly deferred (`FR-1116:19-25,184-191,211-216`; `.github/skills/judge-fr/doctrine.md:51-57`).

Most criteria are directly testable: byte-preserving reads, byte/signature invalidation, stable failure carrying, exact index coverage, post-commit completeness enforcement, corrupt-store failures, manifest expansion, call counts, and report equality all name observable assertions (`FR-1116:193-205`). The revisions below close the remaining cases where an enforcer would otherwise have to invent semantics.

## Required revisions

### R-1: Freeze one current dispatch identity and the full FR-1073 policy boundary

Change the merge contract to receive the changed-subset map's non-empty dispatch token explicitly, for example `map_memo_merge(plan, results, failures, map_name, map_dispatch, min_success=1.0)`, with `meta_map` passing `_map_verdict.summarize.dispatch`. Validate that every executed `MapFailure` has exactly that `map_name` and `map_dispatch`. Rebind every returned failure—executed or reused—to the current `map_name` and `map_dispatch`, and set `MemoMerged.verdict.dispatch` to the same token. Keep reuse provenance in `counts`, not in a synthetic `MapFailure.dispatch == "memo"`.

This is required because FR-1073 defines `dispatch` as the identity shared by branch accounting and its verdict, including zero-item dispatches (`feature-requests/FR-1073-map-result-contract.md:110-120,146-160,167-193`; `yamlgraph/compile/map_contract.py:31-36,50-70,177-204`). FR-1116 currently promises the map token for executed failures, `"memo"` for reused failures, and an unspecified `compute_verdict(...)` dispatch, while successful results carry no token from which merge can recover it (`FR-1116:141-162`; `yamlgraph/models/map_results.py:13-22,34-44,90-117`). That produces a mixed population with no defined verdict identity, especially when `todo` is empty or every executed item succeeds.

Freeze `min_success` validation at the merge boundary to the FR-1073 contract: accept non-negative integers and finite floats in `[0.0, 1.0]`; reject booleans, strings, negative integers, non-finite floats, and out-of-range floats with `MapMemoInputError` before opening a write transaction. Preserve the distinction between integer `1` and float `1.0`; integer values above the current population are valid but unmet (`feature-requests/FR-1073-map-result-contract.md:177-193`). Add direct tests for every boundary and for all-success, mixed executed/reused failure, and zero-`todo` dispatch identity.

### R-2: Make the plan and persisted payload contract lossless and self-validating

Correct the summary from "one SQLite table" to "one SQLite store with `meta` and `memo` tables" (`FR-1116:29-30,115-120`). Define the exact Pydantic models and JSON domain for `MemoPlan`, `MemoItem`, `StoredFailure`, store rows, counts, and `MemoMerged`. Successful payloads must be JSON objects with string keys and JSON values; non-JSON values, non-finite numbers, and non-object successes raise `MapMemoInputError` before any write. `inputs` must be a JSON object under the same rules.

Make merge revalidate the whole plan before opening `BEGIN IMMEDIATE`: `current` keys are unique; indices are exactly `0..len(current)-1`; `todo` is exactly the ordered keys whose hit is `none`; `hits` has exactly one payload for every `ok` or `failed` hit and none for misses; each hit payload agrees with its status; `store` is absolute; and signature/version fields have their declared SHA-256 shape. Then validate the union of result and failure indices, failure map/dispatch attribution, and every payload before opening the transaction. A malformed or stale in-memory plan is an input error and writes nothing.

Resolve the payload contradiction by stripping only dispatch-local attribution. A stored success drops `_map_index` but preserves an ordinary business field named `dispatch`; a stored failure is the declared `StoredFailure` and therefore omits `map`, `dispatch`, and `index`. Replace AC-06's blanket "payloads contain no ... `dispatch`" with those status-specific assertions (`FR-1116:139-150,200`). This preserves the consumer's success object rather than silently deleting an unrelated field.

### R-3: Add witnesses for the persistent and concurrent claims

Extend the acceptance criteria with a separate-process reuse witness: process A creates and merges a store, and process B splits the same files/signature and receives an empty `todo` plus the complete hits. A same-process second invocation is not sufficient evidence for a cross-run SQLite memo; the investigation specifically found that new runs receive no reuse from the existing checkpointer (`docs/investigations/fr1065-resumable-map.md:36-40,60-66,111-116`).

Add a deterministic stale-writer witness for the stated last-upsert-wins policy. Split plan A over version 1, split plan B over version 2, merge B, then merge A; neither merge may partly write or report another plan's data, and a following split over version 2 must be a miss rather than a false hit. Add a separate-process kill-before-merge witness showing the prior store bytes and readable outcomes remain unchanged. These tests do not introduce publication, conflict detection, locks, leases, or branch writes; they directly test the concurrency and crash behavior already claimed at `FR-1116:163-167`.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/shared/map_memo.py`: typed split and merge functions; input, plan, row, stable-failure, counts, and merged-result models; SQLite schema and transactions |
| D-2 | `examples/shared/map_memo_split.tool.yaml` and `examples/shared/map_memo_merge.tool.yaml`, with exact argument, output, invalidation, and error contracts |
| D-3 | Focused unit and process-level tests for file/signature hashing, plan invariants, JSON payloads, FR-1073 index/dispatch/policy behavior, persistence, corruption, concurrency, and interrupted unpublished work |
| D-4 | A committed brief under `feature-requests/authoring-briefs/` and the `examples/demos/meta_map/graph.yaml` migration through `scripts/author.sh` |
| D-5 | `examples/demos/meta_map/tools.py` and `README.md` updates for merged records/failures/verdict, memo counts, and forced full reruns |
| D-6 | Provider-free `meta_map` graph witnesses, authoring validation record, shared-tool documentation, capability/REQ entry, changelog fragment, FR implementation record, and diary entry |

Not authorized: any change under `yamlgraph/`; map compiler, checkpointer, manifest schema, CLI, or provider changes; Redis or LangGraph Store backends; dict items or custom version fields; run membership or deletion tracking; publication, compare-and-set, conflict detection, locks, or leases; a store-read/query API; pruning or TTL; retry policy; branch-level writes; migration of any map graph other than `meta_map`; live model runs; checkpoint-size or crash-survival claims.

## Revised acceptance criteria

- [ ] AC-01: Split over a missing store returns every item in `todo` and creates no file. Split over an existing valid store leaves its bytes unchanged.
- [ ] AC-02: Process A merges five successful files. Process B splits the same files and signature and gets an empty `todo` plus five hits. After one file's bytes change, split returns exactly that file; merge returns five records in current order with `_map_index` 0..4 and counts `executed_ok=1`, `reused_ok=4`.
- [ ] AC-03: Changing one byte in any signature file or changing any JSON `inputs` value re-runs every item. The same files and inputs produce the same signature in a separate process. Non-object, non-JSON, or non-finite `inputs` raise `MapMemoInputError` before fan-out.
- [ ] AC-04: A failed item from run 1 is carried in run 2 without executing, has its current index, contributes to `reused_failed` and to the whole-population verdict, and is rebound to the current merge dispatch. Changing its bytes re-runs it.
- [ ] AC-05: Merge accepts `min_success` only under the FR-1073 integer/fraction contract, preserving `1` versus `1.0`; every invalid boundary raises `MapMemoInputError` before a write transaction. Valid thresholds are judged over the whole current population.
- [ ] AC-06: A threshold miss raises `MapCompletenessError` only after commit. The next split reuses those durable outcomes, and an all-reused threshold miss still raises. The returned verdict and every returned failure share the supplied non-empty current map name and dispatch token.
- [ ] AC-07: Merge rejects a plan with non-contiguous indices, duplicate keys, todo/hit disagreement, missing or extra hit payloads, invalid digests, or a non-absolute store. It also rejects results and failures whose indices miss, duplicate or exceed `0..len(todo)-1`, are booleans/non-integers, or whose failure map/dispatch differs from the supplied current identity. Every rejection occurs before `BEGIN IMMEDIATE` and writes nothing.
- [ ] AC-08: Successful payloads are JSON objects. Persistence removes `_map_index` and preserves every other business field, including a field named `dispatch`; persisted failures validate as `StoredFailure` and contain no map, dispatch, or index attribution. Invalid payloads raise `MapMemoInputError` and write nothing.
- [ ] AC-09: Non-string, empty, duplicate, missing, unreadable, or non-file items and signature files raise `MapMemoInputError` before any map branch runs. Relative paths resolve against the process working directory, and the exact path string remains the key.
- [ ] AC-10: A non-SQLite file, missing or wrong `schema_version`, malformed JSON, model-invalid row, lock beyond the 30-second busy timeout, and failed write or commit each raise `MapMemoStoreError`; none degrades to a miss, partial commit, or success-shaped result.
- [ ] AC-11: Deterministic stale plans for different versions demonstrate last-upsert-wins without false hits or partial writes. A separate process killed before merge leaves the prior store byte-identical and readable. No lock, lease, publication, or conflict API is introduced.
- [ ] AC-12: Both manifests validate through FR-768 loading, resolve `map_memo.py` relative to the manifests, document their exact contracts and CLI/environment invalidation responsibility, and require no `yamlgraph/` change.
- [ ] AC-13: `meta_map` is migrated through `scripts/author.sh`: split and merge are `tool_call` nodes with `on_error: fail`; `summarize` maps over `memo.result.todo` with integer `min_success: 0`; merge receives the current map dispatch and enforces whole-population `min_success: 0.9`; reducers read `merged.result`.
- [ ] AC-14: A provider-free graph test runs the migrated graph over a fixture corpus plus the three poison paths. Run 1 makes one `describe` call per path. Unchanged run 2 makes zero and produces the same success and failure tables, with the expected executed-to-reused count change. Editing one fixture file makes run 3 call `describe` exactly once. All runs retain the three `ClaimMismatchError` failures at their current indices.
- [ ] AC-15: The committed authoring report records lint and deterministic smoke evidence. A new capability/REQ governs the helpers, every new test carries its requirement marker, `python scripts/req_coverage.py --strict` passes, and the shared README, manifest comments, changelog fragment, FR implementation record, and diary entry are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 and the revised acceptance criteria into FR-1116 before implementation authority activates. | GATE |
| C-2 | Keep all runtime implementation under `examples/shared/`; no file under `yamlgraph/` and no manifest, compiler, checkpointer, or CLI contract may change. | GATE |
| C-3 | Preserve one current map/dispatch identity across `MemoMerged.verdict` and all returned `MapFailure` records; provenance belongs in counts, not a synthetic failure dispatch. | GATE |
| C-4 | Validate the full plan, policy, attribution, and JSON payload boundary before opening the write transaction; no invalid input may partially mutate the store. | GATE |
| C-5 | Store corruption, schema mismatch, I/O/locking/commit failure, invalid files, invalid plans, and incomplete accounting must fail loudly; none may become a miss, empty success, or partial report. | GATE |
| C-6 | Material `meta_map` graph or prompt edits must use `scripts/author.sh` and retain its substantive lint and deterministic smoke record. | GATE |
| C-7 | RED tests must precede GREEN implementation, including separate-process reuse, stale-writer, kill-before-merge, all-reused threshold, and consumer call-count witnesses. | GATE |
| C-8 | Keep the other map graphs byte-unchanged and make no live model call. | GATE |

Authority granted: after R-1 through R-3 are folded, implement the two typed SQLite-backed shared tools, their manifests and deterministic witnesses, and the single `meta_map` migration within D-1 through D-6.
