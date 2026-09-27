# Judgement: FR-1120 Census re-run classifies only new or updated PRs

**Verdict:** APPROVED WITH REVISIONS — the contrib/example design is a minimal second consumer of FR-1116, but authority activates only after the `updatedAt` evidence and open-PR policy are made explicit, pairing is frozen as an index-safe join, and every promised invalidation input has a witness.

**Reviewed against:** `feature-requests/FR-1120-census-map-memo.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `feature-requests/FR-1116-map-memo-file-corpus.md`; `feature-requests/FR-1076-shared-map-reuse-helpers.md`; `feature-requests/FR-962-person-profile-census-authored-prs.md`; `feature-requests/FR-966-visibility-conjunction-unsatisfiable.md`; `feature-requests/FR-984-map-fan-out-max-concurrency.md`; `feature-requests/FR-985-census-coverage-floor-and-population-header.md`; `feature-requests/FR-1119-lint-map-owned-state-fields.md`; `docs/investigations/fr1065-resumable-map.md`; `examples/shared/map_memo.py`; `examples/demos/corpus_census/adapters/corpus_adapters.py`; `examples/demos/person_profile_census/graph.yaml`; `examples/demos/person_profile_census/tools.py`; `examples/demos/person_profile_census/README.md`; `tests/unit/test_fr966_authored_pr_visibility.py`.

## What is sound

- **Scope and single responsibility:** the proposal extends the existing split/merge memo with one caller-supplied version mode, adds one version-producing adapter, and migrates one named consumer (`FR-1120:37-49, 91-118`). Its explicit exclusion of framework code, merge/schema changes, adjacent censuses, pruning, and query APIs keeps the change bounded (`FR-1120:208-212`).
- **Consistency:** the graph preserves the current two-map pipeline while memoizing the combined bundle/finding outcome, which is necessary because the reducer validates findings against extracted bundles (`FR-1120:68-75, 120-146`; `person_profile_census/tools.py:392-466`). Keeping `map_memo_merge` unchanged is consistent with its existing indexed-record contract (`map_memo.py:339-375`).
- **Measurability and testability:** the split behavior, adapter failures, carried judge failure, zero-call second run, one-item third run, missing-store failure, lint result, documentation, and traceability artifacts are all directly assertable (`FR-1120:171-182`). The provider-free graph witness follows the successful FR-1116 precedent (`FR-1116:225-238`).
- **Feasibility:** the current memo already separates item version computation from merge attribution (`map_memo.py:209-219, 262-280`), the discovery adapter already centralizes the relevant query validation and population guards (`corpus_adapters.py:245-289`), and merge already rebinds stored payloads to current indices (`map_memo.py:371-375`). No framework primitive is required.
- **Architecture alignment:** deterministic version lookup and pairing remain Python tools while LLM work remains in graph nodes, matching the three-layer rule and the FR's explicit `is_this_a_graph` disposition (`FR-1120:205-206`). The material graph edit is correctly routed through `scripts/author.sh` (`FR-1120:120, 180`).
- **Strategic classification:** **Contrib/example**. There are now two concrete consumers of the shared example-level memo, `meta_map` and `person_profile_census`, while FR-1116 deliberately deferred a framework `memo:` primitive until consumer evidence existed (`FR-1116:245-246`; `FR-1120:203`).

## Required revisions

### R-1: Commit the `updatedAt` evidence that carries the reuse contract

Replace the unsupported platform assertion with a committed evidence record or an expanded in-body research section. It must identify the exact `gh search prs --json` field and output shape, cite the authoritative source or reproducible probe for each change class claimed to advance `updatedAt`, and separately list known non-advancing changes. Narrow the claim if the evidence supports fewer events. The current text proves only that the CLI lists the field, then asserts title/body/label/push/state/comment/review invalidation without a cited witness (`FR-1120:77-80`). Because that marker decides whether extraction and classification are skipped, this is feasibility evidence, not optional documentation.

Fold the evidence path into `**Research:**` and add an acceptance criterion that the adapter requests `updatedAt` and rejects a missing, null, or empty `updatedAt` rather than storing an unusable version.

### R-2: Obtain and record the operator's open-PR freshness decision

Add this explicit human question and its answer under **Human decisions**:

> May repeated census runs knowingly reuse stale `base_sha`, `additions`, `deletions`, and `changed_files` for open PRs when the base branch moves without advancing `updatedAt`?

If the operator answers **yes**, retain the accepted limitation, state that "unchanged" means "`updatedAt` unchanged" rather than "extracted bundle unchanged," and keep the README warning required by AC-09. If the operator answers **no**, amend the versions contract so open PRs are always placed in `todo`, update the adapter fields and signature as needed, and add a provider-free witness showing a stable-`updatedAt` open PR is re-extracted and reclassified. The FR currently delegates this product/data-freshness choice to the judge (`FR-1120:184-191, 201`), but judge doctrine requires human decisions to be surfaced rather than absorbed (`judge-fr/doctrine.md:99-103`).

### R-3: Freeze `pair_executed` as an index join, not a positional zip

Amend Proposed Solution item 4 and AC-04 so `pair_executed`:

1. validates `todo` and the extracted bundle channel as one exact cover of integer indices `0..len(todo)-1`, rejecting booleans, missing indices, duplicates, and out-of-range indices;
2. validates successful findings plus `executed_findings_failures` as a second exact cover of the same index set, including duplicates across the success/failure channels;
3. parses and joins bundles and outcomes by their `_map_index`, never by list position;
4. emits nothing unless both covers validate completely.

The proposal currently says `contents[i]` and leaves "missing, duplicate or out-of-range index" without naming the channel (`FR-1120:148-157`). That is weaker than the current reducer boundary, which reconstructs bundle identity, verifies complete bundle indices, rejects duplicate findings, and rejects missing findings (`person_profile_census/tools.py:144-168, 409-425, 464-466`). FR-1076 already established the applicable precedent: dispatch-local successes and failures must map to stable keys, and missing, duplicate, boolean, or out-of-range indices publish nothing (`FR-1076:410-411`).

### R-4: Witness every promised computation-signature invalidator

Expand the graph-level acceptance test so changing each of `rubric`, `problem_labels`, `surface_labels`, and `azure_model` independently re-runs all five items. Add a focused graph/configuration witness that the exact four `signature_files` are passed, and prove that changing at least one signature file invalidates all five items. The Ideal Result promises invalidation for rubric, label vocabularies, model, prompt, and census code (`FR-1120:84-88`), and the proposed call lists those files and runtime inputs (`FR-1120:123-128`), but AC-06 currently witnesses only `azure_model` (`FR-1120:178`). Without these assertions, a missing graph binding can satisfy every existing test while silently reusing classifications under changed semantics.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Fold R-1 through R-4 into `feature-requests/FR-1120-census-map-memo.md`, including the operator decision and evidence citation. |
| D-2 | Add caller-supplied versions to `examples/shared/map_memo.py`; update only the split manifest and directly related shared documentation. |
| D-3 | Add the shared GitHub search helper and `gh_authored_prs_versions` to `examples/demos/corpus_census/adapters/corpus_adapters.py`; add `gh-authored-prs-versions.tool.yaml`. |
| D-4 | Through `scripts/author.sh`, migrate `examples/demos/person_profile_census/graph.yaml` and regenerate its governed demo output. |
| D-5 | Add `pair_executed` and the merged-input boundary to `examples/demos/person_profile_census/tools.py`; update `examples/demos/person_profile_census/README.md`. |
| D-6 | Add focused memo, adapter, pairing, reducer-equivalence, and provider-free graph witnesses, preserving the cited FR-1116 and FR-966 tests. |
| D-7 | Add the CAP/REQ registration, regenerated architecture registry, changelog fragment, FR implementation record, and one diary entry with a `Seed:`. |

Not authorized: changes under `yamlgraph/`; changes to `map_memo_merge` or the memo schema; changes to `gh_pr_extract`, census prompts, `gh-profiler.yaml`, `corpus_census`, or `repo_census`; pruning, deletion tracking, a store-read/query API, framework-level `memo:`, live LLM pilots, or any open-PR policy other than the operator-selected branch folded under R-2.

## Revised acceptance criteria

- [ ] AC-01: Split with `versions` over unique non-file string items returns every item in `todo` on an empty store, reads no item path, stores the supplied non-empty string versions after merge, and returns `todo == []` on a second split with identical versions.
- [ ] AC-02: Changing one supplied version puts exactly that key in `todo`. Missing or extra keys, non-dict `versions`, non-string or empty version values, duplicate/empty/non-string items, and non-string or empty `store` raise `MapMemoInputError` before a store is created. File mode remains unchanged and all existing `test_fr1116_map_memo.py` tests pass unmodified.
- [ ] AC-03: The committed research evidence satisfies R-1, and the FR records the operator's R-2 decision. The README states the resulting freshness contract without claiming stronger invalidation than the evidence supports.
- [ ] AC-04: With `_gh` stubbed, `gh_authored_prs_versions` requests `repository,number,updatedAt` and returns `{ref: updatedAt}` for the same fixture population as discover. It rejects missing, null, or empty `updatedAt`, overflow, an empty listing, a duplicate ref, and unsatisfiable visibility; shared failures retain discover's messages. `test_fr966_authored_pr_visibility.py` passes unmodified.
- [ ] AC-05: `pair_executed` performs the two exact index-cover validations in R-3, joins by index rather than list order, emits one record per todo index with parsed bundle plus finding or error, strips model-supplied `source_index`, and emits no partial result on malformed attribution.
- [ ] AC-06: For identical bundles and findings, `reduce_pr_ledger` given `merged` writes JSONL byte-identical to its existing `contents`/`findings`/`findings_failures` path, including the exact `row_failed` representation. Existing reducer tests pass unmodified, and malformed merged records retain the current batch-fatal missing/duplicate/out-of-range behavior.
- [ ] AC-07: A provider-free test runs the migrated graph over five PRs including one judge failure. Run 1 makes five extract and five classify calls. Run 2 with identical versions makes zero of each, writes byte-identical JSONL, and retains the judge failure as `row_failed`. Run 3 with one bumped version makes exactly one extract and one classify call for that PR and produces the same ledger as a clean full recomputation of the run-3 fixture.
- [ ] AC-08: Independently changing `rubric`, `problem_labels`, `surface_labels`, or `azure_model` re-runs all five items. The graph passes exactly the four frozen signature files, and changing a signature file invalidates all five items.
- [ ] AC-09: Omitting `memo_store` fails before any extract call and creates no memo store.
- [ ] AC-10: After FR-1119 is enforced, the graph is migrated through `scripts/author.sh`, lints without declarations for `_map_verdict` or `executed_findings_failures`, and regenerates `demo-output.log` with the exact command recorded in the authoring/implementation record.
- [ ] AC-11: The README documents the memo, required `memo_store`, controller warning, reset command, operator-selected open-PR policy, and updated Quickstart/corp invocations with the versions tool and memo store.
- [ ] AC-12: A CAP/REQ entry covers the behavior; every new test carries the REQ marker; `python scripts/req_coverage.py --strict` passes; the changelog fragment, FR implementation record, and diary entry are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 are folded into the FR before implementation begins. | GATE |
| C-2 | FR-1119 is independently judged, authorized, and enforced before the FR-1120 graph is authored; no manual `state:` workaround may substitute for it (`FR-1119:5-11, 76-82`). | GATE |
| C-3 | The graph and prompt-governed surfaces are changed only through `scripts/author.sh`, with `tmp/draft-authoring-report.md`, lint, and the deterministic smoke outcome inspected rather than inferred from exit status. | GATE |
| C-4 | Pairing or reducer validation must fail before memo merge or artifact writing on attribution defects; no positional fallback or silent partial result is permitted. | GATE |
| C-5 | All automated graph witnesses are provider-free and use stubbed GitHub/LLM boundaries; the recorded $0/no-live-pilot decision remains binding. | GATE |
| C-6 | Any need to change `yamlgraph/`, `map_memo_merge`, the store schema, prompts, or another census stops enforcement and returns to planning. | GATE |

Authority granted: after the four revisions are folded and FR-1119 satisfies C-2, implement only the caller-version memo extension, authored-PR versions adapter, index-safe person-profile pairing/reducer boundary, and the frozen documentation/test/traceability surfaces above.
