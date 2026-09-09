# Judgement: FR-1032 adapter-owned extract cache for the corpus census

**Verdict:** APPROVED WITH REVISIONS — adapter-owned caching is a feasible contrib/example change, but authority activates only after the FR narrows to the evidenced `gh_repo_extract` consumer and freezes the missing state, invalidation, validation, and capability contracts below.

**Reviewed against:** `feature-requests/FR-1032-census-adapter-owned-extract-cache.md`; `feature-requests/FR-1031-census-extract-cache-dir.md`; `feature-requests/FR-1031-census-extract-cache-dir.judgement.md`; `feature-requests/032-node-level-caching.md`; `feature-requests/FR-111-compiled-graph-cache.md`; `feature-requests/FR-101-ebook-pipeline-incremental-persist.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-899-org-repo-census-azure.md`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/corpus_census/adapters/corpus_adapters.py`; `examples/demos/corpus_census/adapters/diary_adapters.py`; `yamlgraph/tools/tool_slots.py`; `yamlgraph/tools/python_tool.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/executor_async.py`; `yamlgraph/models/state_builder.py`; `yamlgraph/cli/helpers.py`; `capabilities/CAP-249-tool-slot-binding.yaml`; `reference/patterns/corpus-map-reduce.md`; `docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The proposal resolves FR-1031's blocking ownership defect rather than silently widening the runtime. Slot resolution translates a bound manifest into an existing runtime, and the Python map tool receives state rather than a callable bound slot (`yamlgraph/tools/tool_slots.py:1-7,141-145`; `yamlgraph/tools/python_tool.py:229-239`). Keeping cache composition in the extraction implementation is therefore feasible and respects FR-892's "no new engine" boundary (`feature-requests/FR-1032-census-adapter-owned-extract-cache.md:53-65`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:64-85`).

The cache behavior is mostly concrete and fail-loud. The FR defines a versioned, extractor/source/item-scoped key, UTF-8 digest and byte semantics, atomic same-directory replacement, explicit refresh, diagnosed corrupt-entry misses, and hard failure for non-absence reads and exhausted writes (`feature-requests/FR-1032-census-adapter-owned-extract-cache.md:84-115`). AC-02 through AC-09 can produce direct RED tests for reuse, interruption, identity separation, corruption, I/O failure, and refresh without relying on wall-clock timing (`feature-requests/FR-1032-census-adapter-owned-extract-cache.md:127-143`).

The research record satisfies the prospective substance gate: it presents six genuine solution classes, cites precedent for each, preserves disagreement, and answers `is_this_a_graph` explicitly (`feature-requests/FR-1032-census-adapter-owned-extract-cache.md:151-174`; `.github/skills/judge-fr/doctrine.md:118-129`). The answer is correct: this proposal adds no model stage or graph topology.

The change is single-purpose. Removing the proposed ledger column preserves the existing reducer contract and avoids coupling an operational optimization to the semantic census output (`feature-requests/FR-1032-census-adapter-owned-extract-cache.md:117-121`). Strategically this is **Contrib/example**, not a framework primitive: one evidenced consumer changes code under `examples/demos/corpus_census`, while `yamlgraph/` execution and slot-binding behavior remain unchanged.

## Required revisions

### R-1: Replace the mismatched first-consumer evidence

Rewrite the first-consumer, Problem, and Value Statement claims around an actual invocation of the existing `gh_repo_extract` adapter. Delete the unsupported claim that this function re-fetches 620 GitHub files and the derived 1,860-call/30-minute measurement unless the FR cites committed evidence that maps those items to this adapter. The current function accepts `<org>/<name>`, fetches repository metadata, README, and contributors, and is fed by discovery capped at 100 repositories (`examples/demos/corpus_census/adapters/corpus_adapters.py:116-155`); it is not a GitHub-file extractor. The hand-rolled 620-file harvest in the cited diary is evidence for a related workload, not evidence that the present adapter served it (`docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md:1-20`).

State the first event as the next repeated FR-899 organization-repository census over the same source while iterating its rubric, or cite a committed run record for a completed repeated invocation. Do not add a GitHub-file adapter under this FR.

### R-2: Narrow caching to the evidenced extractor

Replace "each `*_extract` adapter" and the all-extractor guard with one authorized call site: `gh_repo_extract`. The stated defect is three remote calls made by that function (`feature-requests/FR-1032-census-adapter-owned-extract-cache.md:35-45`), while `pdf_extract`, `git_extract`, and `gh_pr_extract` have no consumer or event in this FR (`examples/demos/corpus_census/adapters/corpus_adapters.py:44-93,306-349`). `diary_extract` also lives in a separate module, disproving the claim that all census extractors are co-located (`examples/demos/corpus_census/adapters/diary_adapters.py:45-51`).

Keep one private cache helper in `corpus_adapters.py`, but test both the helper contract and the `gh_repo_extract` integration. Explicitly list `pdf_extract`, `git_extract`, `gh_pr_extract`, and `diary_extract` as not authorized. Additional adapters may opt in only under later evidence.

### R-3: Declare and strictly parse the cache controls

Amend `examples/demos/corpus_census/graph.yaml` state with `cache_dir: str` and `cache_refresh: str`; the current declared state contains neither (`examples/demos/corpus_census/graph.yaml:18-40`). Preserve absence as caching disabled. Because `--var` values are passed as strings (`yamlgraph/cli/helpers.py:54-88`), define `cache_refresh` as the exact case-insensitive enum `true | false`, default it to false when absent, and raise `ValueError` for every other supplied value. Do not use Python truthiness, under which `"false"` would refresh.

The map fan-out already copies outer state into every item send (`yamlgraph/compile/map_compiler.py:335-365`), so no compiler or slot-manifest change is authorized. The material `graph.yaml` state edit must use the graph-authoring route and retain its authoring report.

### R-4: Separate entry schema version from extractor-output version

Revise `_cached` to receive an explicit per-extractor version in addition to `extractor_id`. Include that version in the key and entry. `CACHE_SCHEMA` versions the JSON entry shape; the extractor version changes whenever `gh_repo_extract` changes the meaning or composition of its returned evidence, even if the JSON cache envelope is unchanged. A stable function name alone distinguishes two extractors but can silently serve output produced by an older implementation (`feature-requests/FR-1032-census-adapter-owned-extract-cache.md:84-94`).

Add a test proving that changing only the extractor version causes a miss and produces a separate entry. Keep mutable-source freshness explicitly operator-controlled by `cache_refresh`; remove the claim that this cache itself satisfies the corpus pattern's immutable-identity rule. That pattern requires immutable identities or recorded resolved snapshot data (`reference/patterns/corpus-map-reduce.md:57-82`), whereas this FR deliberately keys a mutable source and retains no cache provenance in the ledger.

### R-5: Make cache entries typed and validate every identity field

Define a Pydantic cache-entry model covering `schema`, `extractor_id`, `extractor_version`, `source`, `item`, `content`, `content_sha256`, `bytes`, and `fetched_at`. Before a hit, validate the complete model and exact equality of all identity fields to the requested key material, then validate UTF-8 byte count and digest. Treat malformed/type-invalid entries and every identity mismatch as separately diagnosed misses that re-fetch and atomically overwrite.

Expand the parametrized corruption criterion beyond malformed JSON/schema/digest/bytes to include wrong extractor ID, extractor version, source, item, non-string content, and invalid timestamp. Assert the diagnostic reason through `caplog` at a frozen log level. This satisfies the repository rule that structured data cross a typed boundary and prevents a validly hashed payload stored under the wrong filename from becoming a silent hit (`.github/copilot-instructions.md:193-195`).

### R-6: Freeze bounded replace behavior and temporary-file cleanup

Specify the retry constant and delay policy mechanically: at most three `os.replace` attempts; retry only `PermissionError`; use the same already-created temporary file; immediately raise any other `OSError`; and remove the temporary file on every terminal failure without masking the primary exception. A temp-file creation/write/flush/close failure is not a replace retry. Tests must assert attempt counts, exception propagation, destination integrity, and absence of orphan temp files.

### R-7: Give the example capability honest registry ownership

Remove the statement that CAP-249 already lists `examples/demos/corpus_census` in `modules`; it lists only `tools/tool_slots` and `compile/graph_loader` (`capabilities/CAP-249-tool-slot-binding.yaml:17-19`). Do not add adapter-cache semantics to the invocation-time slot-binding requirement, because this FR changes no binding behavior.

Create a dedicated capability entry for corpus extraction persistence containing REQ-YG-673 and modules for the graph, `corpus_adapters.py`, and the new test file. Keep CAP-249 unchanged. Update the FR's Requirement field and AC-12 accordingly.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Private typed cache helper and cache-entry model in `examples/demos/corpus_census/adapters/corpus_adapters.py` |
| D-2 | `gh_repo_extract` refactor routing its fetch through the helper; no other extractor call site |
| D-3 | `cache_dir` and strictly parsed `cache_refresh` state declarations in `examples/demos/corpus_census/graph.yaml`, authored through the sole graph-authoring route |
| D-4 | `tests/unit/test_census_extract_cache.py` with REQ-YG-673 markers |
| D-5 | Dedicated capability registry entry owning REQ-YG-673 and the exact example/test modules |
| D-6 | Changelog fragment, FR implementation record, authoring report, and diary distillation |

Not authorized: changes to `yamlgraph/` compiler, map, state-builder, CLI, tool-slot, checkpointer, or cache infrastructure; graph-owned wrapping; generic tool middleware; manifest-schema changes; ledger columns or reducer changes; cache TTL or eviction; a GitHub-file extractor; caching `pdf_extract`, `git_extract`, `gh_pr_extract`, or `diary_extract`; changes to repo-census or other graph/prompt artifacts; a shared framework cache primitive.

## Revised acceptance criteria

- [ ] AC-01: The FR names the existing FR-899 organization-repository census as the first consumer and removes the 620-file, 1,860-call, and 30-minute claims unless a committed run record directly ties them to `gh_repo_extract`.
- [ ] AC-02: RED tests prove that two `gh_repo_extract` calls with identical cache identity invoke its mocked GitHub fetch path twice today; GREEN invokes that path on the first call and zero times on the second.
- [ ] AC-03: With `cache_dir` absent, every call invokes `fetch`, creates no cache directory or file, and returns exactly the fetched content.
- [ ] AC-04: `graph.yaml` declares `cache_dir` and `cache_refresh`; `cache_refresh` absent or `"false"` permits hits, `"true"` forces a fetch and atomic rewrite, case is normalized, and any other supplied value raises `ValueError`.
- [ ] AC-05: The map-state witness proves `source`, `cache_dir`, and `cache_refresh` reach the bound extraction function through the existing parent-state `Send`; no compiler, CLI, state-builder, or manifest change is made.
- [ ] AC-06: A deterministic interruption after N successful writes leaves exactly N valid entries; a new invocation reads those N without fetching and fetches only the remaining M-N.
- [ ] AC-07: Cache identity includes cache-schema version, extractor ID, extractor-output version, source, and item; changing any one produces a miss and cannot serve the prior entry.
- [ ] AC-08: A Pydantic model validates every entry field. Malformed JSON, wrong field type, schema mismatch, extractor-ID mismatch, extractor-version mismatch, source mismatch, item mismatch, invalid timestamp, digest mismatch, and UTF-8 byte-count mismatch each emit their specific frozen diagnostic, re-fetch, and atomically overwrite.
- [ ] AC-09: `content_sha256` is SHA-256 of `content.encode("utf-8")`, and `bytes` is the length of those exact encoded bytes, including a non-ASCII witness.
- [ ] AC-10: A non-absence read `OSError` raises without fetching. Temp creation/write/flush/close errors raise. `os.replace` retries only `PermissionError`, at most three attempts, then raises the last error; every terminal write failure leaves the destination unchanged and no orphan temp file.
- [ ] AC-11: Atomic-write tests prove a reader observes either the complete old entry or complete new entry, never partial JSON.
- [ ] AC-12: A deterministic fetch fixture produces byte-identical ledger artifacts with caching disabled, on a miss, and on a hit; the semantic ledger schema remains unchanged.
- [ ] AC-13: An AST-based integration guard proves `gh_repo_extract` calls the cache helper with literal extractor ID and version; the same guard proves `pdf_extract`, `git_extract`, and `gh_pr_extract` do not call it, and a direct assertion leaves `diary_extract` outside scope.
- [ ] AC-14: The graph edit is produced through `scripts/author.sh`; `tmp/draft-authoring-report.md` records successful lint and smoke with cache disabled and with one miss followed by one hit.
- [ ] AC-15: A dedicated capability entry owns REQ-YG-673 and lists the graph, adapter, and test modules; every new test carries `@pytest.mark.req("REQ-YG-673")`; strict requirement coverage passes.
- [ ] AC-16: Changelog fragment, FR implementation status/decisions, and diary distillation with a `Seed:` are complete.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority exists until R-1 through R-7 and AC-01 through AC-16 are folded into FR-1032 and a human accepts this advisory draft. | GATE |
| C-2 | Cache only `gh_repo_extract`; a second extractor call site or new extractor stops enforcement and returns to planning. | GATE |
| C-3 | Add only graph state declarations through the graph-authoring route; do not change map propagation, CLI parsing, tool-slot binding, or another `yamlgraph/` runtime seam. | GATE |
| C-4 | Cache hits require exact typed identity, extractor-output version, UTF-8 byte count, and digest validation; malformed or mismatched entries are diagnosed misses, while non-absence I/O failures raise. | GATE |
| C-5 | Writes are per successful item and atomic in the destination directory; replace retry is bounded exactly as revised and terminal failure cleans its temp file without hiding the original error. | GATE |
| C-6 | Mutable-source freshness remains an explicit operator decision; do not claim the cache converts mutable GitHub names into immutable corpus identities or silently add TTL behavior. | GATE |
| C-7 | Keep the ledger byte contract unchanged and create dedicated capability ownership; do not widen CAP-249's slot-binding contract. | GATE |

Authority granted: after R-1 through R-7 are folded into FR-1032 and this advisory draft is human-approved, implement only the typed, opt-in, per-item cache for `gh_repo_extract` and the exact supporting graph-state, tests, capability, changelog, FR-record, and diary surfaces listed above.
