# Judgement: FR-1076 Shared map reuse helpers

**Prior art:** `FR-1076-shared-map-reuse-helpers.md` is the FR this judgement governs. FR-1065 (predecessor investigation), FR-1073 (dependency), FR-1031 (Rejected), FR-1032, FR-768 and FR-773 are dispositioned in the FR and cited above.

**Verdict:** APPROVED WITH REVISIONS — shared graph-owned load/save/read tools are a sound and minimal route, but implementation authority activates only after the inherited investigation evidence, the exact store/lease/read contracts, and the FR-1073 dependency are folded into the FR.

**Reviewed against:** `feature-requests/FR-1076-shared-map-reuse-helpers.md`; `feature-requests/FR-1065-resumable-map-investigation.md`; `feature-requests/FR-1065-resumable-map-investigation.judgement.md`; `feature-requests/FR-1073-map-result-contract.md`; `feature-requests/FR-1073.research.md`; `feature-requests/FR-1031-census-extract-cache-dir.md`; `feature-requests/FR-1031-census-extract-cache-dir.judgement.md`; `feature-requests/FR-1032-census-adapter-owned-extract-cache.md`; `feature-requests/032-node-level-caching.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-773-shared-document-splitter-manifest.md`; `feature-requests/FR-391-time-travel-checkpoint-resume.md`; `docs/issues-2026-09-24.md` sections 5.1 and 6.1-6.4; `reference/graph-yaml.md` section "Tool Manifests"; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is concrete and repeated: four graph-local persistence mechanisms are inventoried in the cited plan, while the first consumer names the exact second-run event that currently repays every item (`FR-1076:7-10,52-57`; `docs/issues-2026-09-24.md:240-263`). The ideal result is correspondingly observable: an unchanged second run performs zero LLM calls and consumers materialize only selected results (`FR-1076:59-63`).

The chosen composition seam conforms before extending. Tool manifests already translate shared Python tools into existing runtimes, with graph-relative manifest paths and manifest-relative implementation paths (`reference/graph-yaml.md:1544-1588`); the feeder precedent already demonstrates a manifest tool around a map without a new execution engine (`reference/graph-yaml.md:1599-1617`). Placing deterministic persistence in graph-owned tools therefore respects the three-layer boundary and avoids the infeasible bound-slot invocation rejected in FR-1031 (`FR-1076:28-38,65-85`; `FR-1031-census-extract-cache-dir.judgement.md:23-27`).

The alternatives are substantive: five solution classes identify the chosen class, preserve framework-owned dissent, disposition the rejected extract-cache precedent, and answer `is_this_a_graph` (`FR-1076:131-142`). This satisfies the in-body research form previously accepted for the same solution-class set (`FR-1065-resumable-map-investigation.judgement.md:9-11`). Prior rejected work is not merely cited: FR-1031's failure is distinguished by putting ordinary nodes around the map rather than trying to call a bound slot (`FR-1076:28-31`).

Scope is cohesive rather than bundled. Load, save, and selective read form one cross-run result-store lifecycle after the recorded human decision that consumers read from the store (`FR-1065-resumable-map-investigation.md:4-7`; `FR-1076:88-108`). The single pilot migration proves the abstraction without folding in four unrelated graph migrations (`FR-1076:113-117`). A smaller load/save-only change would recreate the state-materialization cost that the same decision explicitly rejects.

Strategic classification is **framework primitive by demand, delivered through the existing contrib/tool-manifest extension seam**: five concrete consumers are named and no current reuse abstraction works (`FR-1076:7-10,52-57`; `032-node-level-caching.md:3-7`), but no `yamlgraph/` change is necessary because the existing manifest mechanism fits the implementation. This classification authorizes a shared primitive under `examples/shared/`, not compiler or manifest-schema expansion.

The core behaviors are directly testable: two-run selection and counts, carried failures, node-version invalidation, duplicate rejection, cross-process persistence, concurrent-run exclusion, and a real pilot smoke all have observable assertions (`FR-1076:121-129`). After the revisions below remove conditional and underspecified criteria, failing tests can target missing behavior rather than missing fixtures.

## Required revisions

### R-1: Close the inherited investigation before granting fix authority

Fold into FR-1076 citations to the committed FR-1065 investigation report and executable witnesses for: SQLite persistence and exclusion across two processes; serialized checkpoint bytes for a 10,000-item `collect` versus store-selected results; and `kill -9` plus same-thread SQLite-checkpointer resume with exact sub-node call counts. The report must select or reject the proposed key/version/retention/locking semantics and record the pilot's human-approved spend/storage budget.

FR-1065's judgement made those witnesses and report prerequisites to a successor implementation FR (`FR-1065-resumable-map-investigation.judgement.md:15-25,38-53`). FR-1076 currently takes over questions 1, 2, and 5 but cites no completed report (`FR-1076:19-24`) and moves killed-process behavior back into a conditional implementation criterion (`FR-1076:126`). A successor cannot erase its predecessor's evidence gate. If a witness disproves the proposed design, revise the design before seeking authority; do not authorize an implementation that merely records RED.

### R-2: Freeze one typed transactional store and lease contract

Replace the six-column sketch with an explicit, versioned Pydantic-backed store contract. Define tables and constraints for item records, completed-run membership, and the lease; accepted SQLite value encodings; schema creation and version mismatch behavior; transaction boundaries; and fail-loud behavior for malformed JSON, model-invalid rows, unsupported schema versions, unreadable files, and write/commit failures. Absence may be a miss; corruption or I/O failure must not silently become one.

Reconcile "one row per key" with "latest run's key set": the save transaction must assign every current key, including unchanged successes and carried failures, to the newly completed run before that run becomes readable. Define the completed-run marker so `map_reuse_read` never observes a load-only or partially saved run. Define deleted state consistently: the current schema permits only `ok|failed`, while the prose says absent rows are kept and marked deleted (`FR-1076:88-92,102-106`). Freeze whether deletion is a separate membership/tombstone field or a third item status, and state whether a later reappearance is `new` or `changed`.

Define the lease as an atomic unique-store acquisition carrying an unguessable run token; only save with the matching token may publish the run and release it. Fold a fail-loud abandoned-lease recovery procedure into the FR, with no silent time-based stealing. The procedure must preserve concurrent-run exclusion and allow the killed run's same-thread resume to complete and release its own lease. The current acquire-at-load/release-at-save sentence does not say what happens after process death, token mismatch, save failure, or an abandoned thread (`FR-1076:90-92,109-111`).

### R-3: Make identity and invalidation byte-exact

Define accepted key types and their collision-free SQLite encoding. If the `key` field is missing, null, unsupported, or duplicated, load must raise before acquiring a lease or returning `todo`.

Distinguish an omitted `version` argument from a named version field that is missing. The omitted form must hash UTF-8 canonical JSON with an exact canonicalization rule; a named field that is absent must raise rather than silently switch modes. Define how null versions behave.

Define `node_version` byte-for-byte: resolve `node_version_files` relative to the consuming graph, normalize and order paths deterministically, hash both normalized path identity and raw file bytes with unambiguous length framing, include the resolved model string, and raise on an absent, unreadable, or non-file path. Add a store schema/tool-contract version to the invalidation identity so a changed result envelope cannot reuse old rows. The present "SHA-256 of listed files plus model" is not enough to derive stable tests or prevent concatenation/path aliases (`FR-1076:72-75,93-96,123`).

### R-4: Reduce and freeze the read surface

Remove the unspecified free-form `filter` surface. The first consumer demonstrates only selected fields, a limit, and ordering (`FR-1076:84-85,105-108`); an unbounded filter language adds query and validation complexity without a named use case.

Define `map_reuse_read` as reading only the latest **completed** run. Freeze: the allowed `fields` source (stored result object plus the item key); rejection of unknown or duplicate fields; positive bounded `limit`; one validated `order_by` field; explicit ascending/descending selection; deterministic key tie-breaking; and the exact return model. SQL identifiers must come only from validated internal mappings and values must be parameterized. Empty matches return an empty typed result; invalid arguments, invalid stored rows, or absence of a completed run raise named errors. Add acceptance tests for ordering, ties, field projection, limit, invalid fields, and failed/deleted-row exclusion.

### R-5: Replace conditional and report-only criteria with binding assertions

Replace AC-6's "If RED" escape with a required passing killed-process witness. If current checkpointer semantics do not preserve completed branches, enforcement is blocked and the branch-write change re-enters as a separate judged FR; it is not authorized here (`FR-1076:109-111,126`).

For the 10,000-item checkpoint comparison, name the fixture and serialized checkpoint measurement command, assert that the selective-read checkpoint contains only the declared projection and is smaller than the full-collect checkpoint, and record both exact byte counts. This gates the defect class without inventing a forecast percentage (`FR-1076:127`).

For the pilot, assert zero classify invocations with an instrumented call counter on the second unchanged run and retain the raw smoke log as supporting evidence (`FR-1076:128`). Name the unit, process-level integration, killed-process, and graph-artifact test files so every criterion has a direct test surface. Add the capability/REQ artifact, requirement coverage command, changelog fragment, FR implementation record, and diary distillation required by repository doctrine (`.github/copilot-instructions.md:169-171,198-214`).

Finally, state that FR-1073 must be judged, revised as required, implemented, and merged before FR-1076 enforcement. FR-1076 maps save inputs through `_map_index` and consumes a separate `failures` channel (`FR-1076:25-27,79-82,102-104`), but FR-1073 is still Proposed (`FR-1073-map-result-contract.md:3-5`). If its final contract differs, revise FR-1076 and re-run judgement rather than coding against the proposal.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/shared/map_reuse.py`: typed load, save, and selective-read tool functions plus private typed store models |
| D-2 | `examples/shared/map_reuse_load.tool.yaml`, `map_reuse_save.tool.yaml`, and `map_reuse_read.tool.yaml` |
| D-3 | Unit and process-level integration tests for identity, persistence, transactions, leases, failures, reads, and corruption |
| D-4 | Controlled killed-process/checkpointer witness and 10,000-item checkpoint-size witness |
| D-5 | `examples/demos/person_profile_census` migration through `scripts/author.sh`, including lint, two-run smoke, call counter, and raw log |
| D-6 | Tool-manifest/reference documentation, examples/shared documentation, capability/REQ traceability, changelog fragment, FR implementation record, and diary distillation |

Not authorized: any change under `yamlgraph/`; map compiler, checkpointer, tool-manifest schema, or CLI changes; Redis or LangGraph Store backends; chunked scheduling; retry policy; arbitrary SQL or expression filters; migrations of `corpus_census`, `file-hook`, `self-portrait`, or `ocr_cleanup`; automatic lease expiry/stealing; branch-level writes into the reuse store; or a claim of general crash survival beyond the tested same-thread SQLite-checkpointer resume.

## Revised acceptance criteria

- [ ] AC-01: FR-1076 cites a committed FR-1065 investigation report with executable two-process SQLite, 10,000-item checkpoint-size, and killed-process resume witnesses; the selected contracts and human-approved pilot spend/storage budget are folded into the FR.
- [ ] AC-02: Typed schema tests create a versioned empty store and reject unsupported schema versions, malformed/model-invalid result rows, unreadable stores, and failed writes or commits without converting them to misses.
- [ ] AC-03: Run 1 over five items followed by run 2 with one changed version, one removed key, and one new key executes exactly the changed and new items and reports `changed=1`, `new=1`, `unchanged=3`, `deleted=1`; a read of run 2 includes all five current keys, including the three unchanged rows, and excludes the deleted key.
- [ ] AC-04: A failed item from run 1 is assigned to run 2 as a carried failure and does not execute; after only its item version changes it executes. Failed and carried-failed counts and latest-run membership are asserted separately.
- [ ] AC-05: Changing one byte in any declared node-version file or changing the resolved model re-runs all current items; unchanged inputs produce an identical node version across processes. Missing or unreadable files raise before fan-out.
- [ ] AC-06: Omitted item version uses the frozen canonical-JSON hash; a declared but missing version field, invalid key, null/unsupported key, or duplicate encoded key raises during load before any map branch executes and leaves no acquired lease.
- [ ] AC-07: Separate-process run 2 reuses run 1 rows. A concurrent load loses atomic lease acquisition and raises a named error. Save with a wrong token cannot publish or release; transaction failure leaves the prior completed run readable.
- [ ] AC-08: A killed process resumed with the same SQLite-checkpointer thread executes no already completed branch, publishes one complete run, and releases its matching lease. The frozen abandoned-lease recovery procedure is tested separately and cannot steal a live lease.
- [ ] AC-09: `map_reuse_read` reads only the latest completed run; projection, limit, ascending/descending ordering, deterministic key ties, unknown-field rejection, invalid-limit rejection, and exclusion of failed/deleted rows match the frozen typed contract.
- [ ] AC-10: For the committed 10,000-item fixture, the selective-read consumer checkpoint contains only the requested projection, serializes to fewer bytes than the full-collect checkpoint, and records both exact byte counts with the reproducible command.
- [ ] AC-11: All three manifests validate through the existing FR-768 mechanism, resolve `map_reuse.py` relative to the manifests, and expose only the frozen typed function contracts; no `yamlgraph/` file changes.
- [ ] AC-12: After FR-1073 is merged, an integration fixture proves successful results and failure records map through `_map_index` to the correct `todo` keys, including interleaved success/failure order; out-of-range, duplicate, or missing indices raise and publish nothing.
- [ ] AC-13: `person_profile_census` is migrated through `scripts/author.sh`; the validation artifact records lint and two complete smoke runs, and an instrumented counter proves the unchanged second run makes exactly zero classify calls while the retained raw log shows the same outcome.
- [ ] AC-14: A new capability/REQ entry governs the helpers, every changed test carries its requirement marker, `python scripts/req_coverage.py --strict` passes, tool-manifest and shared-tool docs cover the exact contracts and errors, and the changelog fragment, FR implementation record, and diary entry are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into FR-1076 and obtain human review of this advisory judgement before implementation authority activates. | GATE |
| C-2 | Complete and cite the FR-1065 investigation witnesses; no production store or migration work may begin from unevidenced storage/crash assumptions. | GATE |
| C-3 | FR-1073's final judged contract must be implemented and merged before FR-1076 enforcement; contract drift requires FR-1076 revision and a new judgement. | GATE |
| C-4 | Keep all runtime implementation under `examples/shared/`; no `yamlgraph/`, manifest-schema, compiler, checkpointer, or CLI change is authorized. | GATE |
| C-5 | Material changes to the pilot graph or prompts must use `scripts/author.sh` and retain its substantive validation artifact, lint, and smoke evidence. | GATE |
| C-6 | The killed-process witness must pass before the FR may claim same-thread crash survival; a required branch-level store write or framework change is a separate FR. | GATE |
| C-7 | Store corruption, I/O errors, lease conflicts, invalid identities, and invalid read arguments must fail loudly under typed tests; none may degrade to a hit, empty success, or broad miss. | GATE |
| C-8 | RED tests precede GREEN implementation, and the four existing graph-local reuse implementations remain untouched. | GATE |

Authority granted: after all gates are satisfied, implement the three typed SQLite-backed shared tools, their manifests and tests, and the single `person_profile_census` migration exactly within D-1 through D-6.
