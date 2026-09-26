# Judgement: FR-1076 Shared map reuse helpers

**Verdict:** APPROVED WITH REVISIONS — the shared graph-owned store is a sound, scoped primitive, but authority activates only after the load/save plan and pilot define stable key-based attribution instead of relying on dispatch-local map indices.

**Reviewed against:** `feature-requests/FR-1076-shared-map-reuse-helpers.md`; `feature-requests/FR-1076-shared-map-reuse-helpers.judgement.md`; `feature-requests/FR-1073-map-result-contract.md`; `docs/investigations/fr1065-resumable-map.md`; `tests/unit/test_fr1065_resumable_map_probes.py`; `docs/issues-2026-09-24.md` sections 5.1 and 6; `reference/graph-yaml.md` section "Tool Manifests"; `yamlgraph/compile/map_compiler.py`; `yamlgraph/models/map_results.py`; `yamlgraph/models/state_builder.py`; `examples/demos/person_profile_census/graph.yaml`; `examples/demos/person_profile_census/tools.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The FR now handles the first judgement's two decisive blockers honestly. It cites the committed investigation and executable witnesses, narrows the killed-process claim to read-only store invariance, reduces the checkpoint witness to the already pinned 1,000-item fixture, and consumes FR-1073's merged `MapFailure.index` contract rather than its proposed map-level key (`FR-1076:5,60-67,69-95,239-243,285-302`; `docs/investigations/fr1065-resumable-map.md`, results 2a/2b and 5a/5b). The $0 deterministic-pilot decision is explicit rather than hidden behind an unavailable live budget (`FR-1076:43-58,244-254,303`).

The problem and first event are concrete: several graph-local mechanisms duplicate incomplete reuse behavior, while an unchanged second census run currently repays every item (`FR-1076:8-16,98-120`; `docs/issues-2026-09-24.md:247-263,294-312`). The proposed load → map → save → selective-read lifecycle directly addresses that event without adding compiler, checkpointer, CLI, or backend machinery (`FR-1076:123-148,261-280`).

The concurrency simplification is feasible. A read-only load records the published run it observed; `BEGIN IMMEDIATE` serializes saves; the save compares `meta.current_run` with `base_run` before atomically publishing a new membership; a stale writer raises and cannot partly publish (`FR-1076:153-174,205-223,297`). This permits duplicate spend but not a corrupt winner, removes abandoned-lease recovery, and matches the operator's explicit tradeoff (`FR-1076:60-65`).

Architecture alignment is strong. Existing tool manifests translate shared Python implementations into the ordinary runtime and resolve implementation paths relative to the manifest (`reference/graph-yaml.md:1550-1605`). Keeping deterministic persistence under `examples/shared/` and migrating one graph through `scripts/author.sh` conforms to the repository's graph-authoring and three-layer rules (`FR-1076:261-280`; `.github/copilot-instructions.md:13,194,198`). The three helpers form one result-store lifecycle, so load, save, read, tests, documentation, and one proving consumer are cohesive rather than an orthogonal bundle.

The alternatives satisfy the substantive in-body research route: five solution classes are dispositioned, framework-owned dissent is preserved, rejected FR-1031 is distinguished, and `is_this_a_graph` is answered (`FR-1076:18-41,310-321`). Strategic classification is **framework primitive delivered through the existing contrib/tool-manifest seam**: four reinventions plus the named pilot establish 3+ use cases, no existing reuse abstraction fits, and no new framework runtime is needed.

Most acceptance criteria are mechanically testable and name their test surfaces (`FR-1076:285-308`). Store corruption, identity, invalidation, conflicts, transaction rollback, selective reads, separate-process reuse, checkpoint size, manifest validation, FR-1073 result accounting, and provider-free graph execution can all be condemned by direct failing tests.

## Required revisions

### R-1: Freeze a lossless typed load plan for save

Replace the comment-only `MapReuseLoad {todo, carried_failures, base_run, node_version, counts}` contract with an exact Pydantic model. It must carry an ordered record for every current input item, including its encoded key, encoded version, current input index, node version, and classification (`new`, `changed`, `unchanged`, or `carried_failed`). Each dispatched `todo` item must identify its corresponding current-item record; aggregate counts must be derived from these records rather than serving as the only representation of unchanged membership.

Make `map_reuse_save` consume that plan. It must use `_map_index` and `MapFailure.index` only to map this dispatch's outputs onto the ordered `todo` records, then use the full current-item records to assign `last_run` to executed, unchanged, and carried keys. This closes the contradiction between the declared load result, which exposes no lossless list of unchanged current keys, and save's obligation to republish every current key (`FR-1076:129-144,195-220`).

Define stable stored payloads. After attribution, strip the success envelope's dispatch-local `_map_index` before writing `result_json`. Store failures through a private typed stable-failure model that omits `dispatch` and dispatch-local `index`; expose carried failures as typed records containing the encoded item key and current input index. Do not present an index from an earlier dispatch as a current FR-1073 index. The merged engine guarantees only a branch index within one dispatch (`yamlgraph/compile/map_compiler.py:194-199`; `yamlgraph/models/map_results.py:13-21`).

### R-2: Make the pilot reconcile and prove results by item identity

Freeze the `person_profile_census` migration's data path. After save, the reducer must consume the published successful rows from `map_reuse_read`, combine current-run and carried failures from their typed key-bearing records, and join every record to the current `items` and `contents` by the FR's declared PR identity key. It must reject duplicate keys, missing current keys, and any current item without exactly one success or failure. It must not trust a stored `_map_index`, stored `source_index`, list position, or an old failure index for current attribution.

This is required because the current reducer resolves findings to `items[index]` and `contents[index]` (`examples/demos/person_profile_census/tools.py:160-166,386-389,392-447`), while FR-1073's success and failure indices describe only the map dispatch that produced them. The present AC-13 can pass with zero second-run classify calls even if reused rows are omitted or paired with the wrong PR (`FR-1076:244-254,303`).

Expand AC-13 with semantic witnesses. The unchanged second run must produce the same complete key-to-classification ledger as run 1, not merely zero calls. A third deterministic run must reorder the subject, remove one key, change one item, and add one item; it must call `classify_pr` exactly for the changed and new keys and produce one correctly attributed ledger row for every current key. Include a carried failure in that sequence and prove it remains attached to its key without entering FR-1073 completeness arithmetic.

### R-3: Close path and scalar boundary ambiguities

Define `base_dir` resolution byte-exactly: absolute paths remain absolute; relative paths resolve against a named boundary, and the pilot must pass a value that remains correct when invoked outside the repository root. Continue to reject every normalized `node_version_files` path outside that resolved directory (`FR-1076:185-194`). A shared manifest's implementation path is portable by manifest-relative resolution, but arbitrary tool arguments do not inherit graph-relative semantics (`reference/graph-yaml.md:1561-1594`).

State explicitly that booleans are rejected for named versions as they are for keys, or explicitly authorize and test them; Python's `bool`/`int` relationship must not decide the persisted identity accidentally (`FR-1076:177-186`). Reserve projected field `key` for the decoded item key: if a stored success also has a top-level `key`, the item key wins and the result field is not addressable through that name. Add direct tests for both rules so the identity and read contracts are derivable without implementation guesses (`FR-1076:225-236`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/shared/map_reuse.py`: typed load, save, and read functions; exact typed load-plan, stable-failure, store-row, and read-result models |
| D-2 | `examples/shared/map_reuse_load.tool.yaml`, `map_reuse_save.tool.yaml`, and `map_reuse_read.tool.yaml` |
| D-3 | Unit and process-level tests for identity, persistence, complete current-run membership, transactions, publish conflicts, stable failure carrying, reads, corruption, and separate-process reuse |
| D-4 | Deterministic 1,000-item checkpoint-size witness with exact recorded byte counts and reproduction command |
| D-5 | `examples/demos/person_profile_census` migration through `scripts/author.sh`, including identity-based reducer reconciliation and deterministic unchanged/reordered/changed run witnesses |
| D-6 | Tool-manifest and `examples/shared/README.md` documentation, capability/REQ traceability, changelog fragment, FR implementation record, and diary entry |

Not authorized: any change under `yamlgraph/`; map compiler, checkpointer, tool-manifest schema, or CLI changes; Redis or LangGraph Store backends; chunked scheduling; retry policy; SQL or expression filters; migration of `corpus_census`, `file-hook`, `self-portrait`, or `ocr_cleanup`; locks or leases; branch-level store writes; live pilot runs; or any claim that completed branches survive a killed open map step.

## Revised acceptance criteria

- [x] AC-01: The FR cites the committed FR-1065 report and executable two-process SQLite, checkpoint-size, and killed-process witnesses; states their gaps; folds their selected contracts; and records the operator's $0 spend and no-live-storage decision.
- [ ] AC-02: Typed schema tests create a versioned empty store and reject unsupported schema versions, malformed or model-invalid rows, unreadable stores, and failed writes or commits without converting them to misses.
- [ ] AC-03: `MapReuseLoad` returns the frozen ordered current-item plan. Run 1 over five items followed by run 2 with one changed version, one removed key, and one new key executes exactly the changed and new items, republishes all five current memberships, reports `changed=1`, `new=1`, `unchanged=3`, `deleted=1`, and excludes the deleted key from read.
- [ ] AC-04: A failed item from run 1 is carried in run 2 without execution; its carried record contains its encoded key and current input index, not its old dispatch index. After only its version changes it executes. `failed`, `carried_failed`, and published membership are asserted separately.
- [ ] AC-05: One changed byte in any node-version file or a changed model re-runs all current items; unchanged inputs produce an identical node version across processes. Absolute and relative `base_dir` behavior is tested from a working directory other than the repository root; missing, unreadable, duplicate, non-file, or escaping paths raise before fan-out.
- [ ] AC-06: Omitted `version` uses the frozen canonical-JSON hash; a named missing, null, boolean, or unsupported version and a missing, null, boolean, unsupported, or duplicate key raise during load before any branch runs.
- [ ] AC-07: Run 2 in a separate process reuses run 1 rows. Two loads from the same published run followed by two saves allow the first to publish; the second raises `MapReuseConflict` and changes nothing. A failed save transaction leaves the prior published run readable.
- [ ] AC-08: Load leaves an existing store file byte-identical and creates no file when none exists; a run killed before save leaves no published change, and a following run loads and publishes normally.
- [ ] AC-09: `map_reuse_read` reads only the published run; projection, bounded limit, ascending and descending order, encoded-key tie-break, unknown and duplicate field rejection, invalid limit rejection, reserved item-key behavior, incomparable-order rejection, and exclusion of failed and deleted rows match the frozen typed contract.
- [ ] AC-10: On the deterministic 1,000-item fixture, run 2 over unchanged input has empty `todo`; a 50-row read leaves only the requested projection and empty `collect` in the consumer checkpoint; that checkpoint serializes to fewer bytes than the full-collect checkpoint; both exact byte counts and the reproduction command are recorded in the FR.
- [ ] AC-11: All three manifests validate through the FR-768 mechanism, resolve `map_reuse.py` relative to the manifests, expose only the frozen contracts, and require no `yamlgraph/` change.
- [ ] AC-12: With merged FR-1073 behavior, an integration fixture maps successes by `_map_index` and failures by `MapFailure.index` to the correct ordered `todo` records, including interleaved outcomes; out-of-range, duplicate, or missing indices raise and publish nothing. Persisted success and failure payloads contain no dispatch-local attribution fields.
- [ ] AC-13: `person_profile_census` is migrated through `scripts/author.sh` and its report records lint. Deterministic provider-free witnesses prove: an unchanged second run makes zero `classify_pr` calls and produces the same complete key-to-classification ledger as run 1; a reordered third run with one removed, one changed, one new, and one carried-failed key calls only the changed and new keys and emits exactly one correctly attributed row per current key.
- [ ] AC-14: A new capability/REQ entry governs the helpers; every new test carries its marker; `python scripts/req_coverage.py --strict` passes; tool-manifest and shared-tool docs cover the exact models, path semantics, identity rules, and errors; and the changelog fragment, FR implementation record, and diary entry are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 into FR-1076 before implementation authority activates. | GATE |
| C-2 | Keep all runtime implementation under `examples/shared/`; no `yamlgraph/`, manifest-schema, compiler, checkpointer, or CLI change is authorized. | GATE |
| C-3 | Use dispatch-local indices only inside the current save attribution step; persisted and carried records must be rebound by stable item key. | GATE |
| C-4 | Material pilot graph or prompt edits must use `scripts/author.sh` and retain its substantive lint and deterministic validation report. | GATE |
| C-5 | Store corruption, I/O errors, publish conflicts, invalid identities, incomplete current-item plans, and reducer reconciliation failures must fail loudly; none may degrade to a miss, empty success, or partial ledger. | GATE |
| C-6 | RED tests must precede GREEN implementation, and the four existing graph-local reuse implementations must remain untouched. | GATE |

Authority granted: after R-1 through R-3 are folded, implement the three typed SQLite-backed shared tools, their manifests and witnesses, and the single identity-reconciled `person_profile_census` migration within D-1 through D-6.
