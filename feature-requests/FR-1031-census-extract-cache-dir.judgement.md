# Judgement: FR-1031 `cache_dir` on the census extract slot

**Verdict:** REJECTED — the resumable extract-cache problem is real, but the proposed shared wrapper cannot invoke the bound `extract` slot, the FR's own stop-line therefore leaves no implementable solution in scope, and the in-body research record does not satisfy the prospective research gate.

**Reviewed against:** `feature-requests/FR-1031-census-extract-cache-dir.md`; `feature-requests/032-node-level-caching.md`; `feature-requests/FR-111-compiled-graph-cache.md`; `feature-requests/FR-101-ebook-pipeline-incremental-persist.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.judgement.md`; `feature-requests/FR-892.research.md`; `feature-requests/FR-899-org-repo-census-azure.md`; `feature-requests/FR-895-census-synthesize-tail.md`; `reference/patterns/corpus-map-reduce.md`; `docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/corpus_census/tools.py`; `examples/demos/corpus_census/adapters/corpus_adapters.py`; `yamlgraph/tools/tool_slots.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/tools/python_tool.py`; `yamlgraph/node_factory/tool_nodes.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem and first consumer are concrete. The current GitHub repository extractor performs metadata, README, and contributor requests for every item (`examples/demos/corpus_census/adapters/corpus_adapters.py:135-150`), while the FR names the 620-item interrupted-harvest event and quantifies its repeated-call cost (`feature-requests/FR-1031-census-extract-cache-dir.md:7-10,34-44`). Avoiding a second fetch when only the rubric changes is a useful, directly observable outcome.

The proposal is single-purpose and appropriately keeps rubric-dependent judgement outside the extraction cache (`feature-requests/FR-1031-census-extract-cache-dir.md:50-55,94-105`). AC-02 through AC-04 identify strong behavioral witnesses: count adapter invocations, resume after a controlled interruption, and prove rubric changes re-run judgement without re-fetching. Those tests can fail for the missing behavior rather than for absent fixtures.

Keeping generic cache policy out of each corpus adapter is directionally aligned with the shared-graph architecture: the corpus pattern says a new corpus supplies discovery and extraction adapters rather than a new graph (`reference/patterns/corpus-map-reduce.md:54-60,380-382`), and FR-892 freezes one invocation-bound `extract` slot (`feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:29-36,64-83`).

Strategically, the proposal as written is **Contrib/example**, not a framework primitive: it names one concrete consumer and changes the shared census example, while claiming unnamed future consumers (`feature-requests/FR-1031-census-extract-cache-dir.md:7-10,22-24,54-55`). If the replacement design requires a generic tool-decoration or slot-composition mechanism in `yamlgraph/`, it must be reclassified and supported by at least three concrete use cases under the doctrine's framework-primitive threshold (`.github/skills/judge-fr/doctrine.md:51-57`).

## Required revisions

### R-1: Replace the research record with a substantive disposition

Re-file the plan with an in-body or separately committed research record containing four to six genuine solution classes, including the chosen solution class, a precedent/evidence line for each class, preserved disagreement, and an explicit `is_this_a_graph` answer. The present table lists five rejected or inapplicable approaches but does not evaluate the chosen wrapper as a solution class, preserve dissent about the operator constraint, or answer `is_this_a_graph` (`feature-requests/FR-1031-census-extract-cache-dir.md:107-115`). This fails the prospective research gate in `.github/skills/judge-fr/doctrine.md:118-129`.

### R-2: Resolve the human ownership decision before proposing an implementation

Record an explicit human answer to: **May cache composition be part of the bound extraction implementation/manifest, or must the shared graph own it?** If extraction binding may own composition, propose and bound that design. If the graph must own it, file a framework proposal for a callable tool-decoration/slot-composition seam and supply the three or more concrete use cases required for framework-primitive status. Do not retain `tools.py` `cached_extract` as the implementation: slot resolution translates declarations into the graph's tool registry (`yamlgraph/tools/tool_slots.py:141-145`; `yamlgraph/compile/graph_loader.py:71-77`), whereas an ordinary Python tool receives only the resolved state and calls its loaded function directly (`yamlgraph/tools/python_tool.py:229-239,299-319`). No bound-slot callable is present in that state.

The FR already states that compiler-level fallback is a larger, separate FR (`feature-requests/FR-1031-census-extract-cache-dir.md:84-90`). Because the wrapper is infeasible and that fallback is excluded, the current plan has no remaining implementation route.

### R-3: Freeze cache identity and invalidation semantics

Define the cache key as a versioned identity that prevents reuse across incompatible extractors and snapshots. At minimum, specify the cache schema version, bound extractor identity or manifest digest, item identity, source/snapshot identity, content digest algorithm, and exact byte encoding used for `bytes`. State how an operator intentionally refreshes mutable sources.

`sha256(item_ref)` alone is not content-addressed and aliases different bound extractors that receive the same item string (`feature-requests/FR-1031-census-extract-cache-dir.md:67-72`). The cited GitHub repository adapter uses mutable `<org>/<name>` identity and fetches current repository metadata, README, and contributors (`examples/demos/corpus_census/adapters/corpus_adapters.py:135-155`), while the governing corpus pattern requires immutable identities or recorded resolved snapshot data (`reference/patterns/corpus-map-reduce.md:71-82`).

### R-4: Define per-item durability and fail-loud corruption handling

Specify that every successful extraction is persisted before that map item is considered complete, using an atomic same-directory temporary write and replace. Define typed validation for the cache entry and enumerate failure classes: absence is a miss; malformed JSON, schema mismatch, byte-count mismatch, and digest mismatch are diagnosed and re-fetched; failure to read because of permissions and failure to replace the entry are surfaced according to a named fail-loud policy. Do not collapse every unreadable condition silently into `miss`.

This is necessary because AC-03 promises reuse after interruption at item N (`feature-requests/FR-1031-census-extract-cache-dir.md:98-99`), and the current extraction is a parallel map whose inner node is one independently compiled callable (`examples/demos/corpus_census/graph.yaml:75-85`; `yamlgraph/compile/map_compiler.py:228-332`). A batch write after the map returns would not satisfy the interruption contract.

### R-5: Reconcile disabled-cache and ledger semantics

Replace the binary ledger state with an explicit `disabled | hit | miss` status, or state that the cache column is absent when caching is disabled and test both schemas. The current plan says an unset cache preserves behavior exactly while also adding a mandatory `hit | miss` ledger column (`feature-requests/FR-1031-census-extract-cache-dir.md:22-24,73-74,94-105`). Those requirements are inconsistent, and labeling disabled extraction as a miss would make the audit record false.

Define the deterministic join from each discovered `item_ref` to its cache status and ledger row. The existing reducer consumes only `items` and `findings`, and its row schema and output header have no extraction metadata (`examples/demos/corpus_census/tools.py:53-65,303-345,357-375`).

### R-6: Make the replacement acceptance suite mechanically complete

Carry the revised criteria below into the replacement FR, naming exact test surfaces and expected assertions. Add the required capability/requirement decision, `@pytest.mark.req(...)` tags, graph-authoring route evidence for every material `graph.yaml` change, changelog fragment, FR implementation record, and diary distillation. The current criteria omit entry-schema validation, extractor/snapshot separation, atomic-write durability, concurrent duplicate handling, disabled-state truthfulness, and the required project wiring.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-0 | Planning artifacts only: disposition this FR as rejected and submit a replacement FR after the R-2 ownership decision |

Not authorized: changes to `examples/demos/corpus_census/graph.yaml`, `examples/demos/corpus_census/tools.py`, corpus adapters, `yamlgraph/` compiler/runtime code, cache files, tests, capability/requirement metadata, or documentation under FR-1031. No implementation authority is granted by this draft.

## Revised acceptance criteria

- [ ] AC-01: The replacement research record contains four to six genuine solution classes, identifies the chosen class, preserves disagreement, cites precedent per class, and answers `is_this_a_graph`.
- [ ] AC-02: A RED test at the selected composition seam proves that the bound extraction callable cannot currently be cached per item; GREEN demonstrates the exact authorized seam without adapter duplication.
- [ ] AC-03: With caching disabled, every item invokes the bound extractor, no cache directory or entry is created, and the ledger reports the frozen disabled-cache representation.
- [ ] AC-04: With caching enabled, two complete runs over the same frozen extractor/source/item identities produce one miss then one hit per item, and the second run invokes the bound extractor zero times.
- [ ] AC-05: A deterministic interruption after N successful item extractions leaves exactly N valid atomic entries; a new run reads those N entries and invokes the extractor only for the remaining items.
- [ ] AC-06: Changing only `rubric` re-runs judgement for every item and invokes extraction zero times; changing extractor identity, cache schema version, source snapshot identity, or item identity produces misses.
- [ ] AC-07: Entry validation checks the typed schema, item identity, extractor/snapshot identity, UTF-8 byte count, and content digest before declaring a hit.
- [ ] AC-08: Missing entries are misses; malformed JSON, schema mismatch, byte mismatch, and digest mismatch emit a deterministic diagnostic and are replaced atomically after successful extraction; permission and write failures follow the frozen fail-loud policy.
- [ ] AC-09: Concurrent processing cannot expose partial JSON, and duplicate item identities are either rejected before fan-out or serialized under a defined single-writer rule.
- [ ] AC-10: Every ledger row has exactly one truthful `disabled | hit | miss` status, status counts equal the frozen item count, and status is joined by collector-owned identity rather than list position alone.
- [ ] AC-11: Existing corpus adapters remain cache-unaware if graph ownership is retained; otherwise the replacement FR explicitly records the human-approved relaxation and prevents per-adapter cache implementations.
- [ ] AC-12: Material graph changes use the sole graph-authoring route and retain its lint/smoke report; tests carry requirement markers; capability/requirement metadata, changelog, FR implementation status, and diary distillation are complete.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-1031 grants no implementation authority; mark it Rejected or replace it with a newly filed plan after the ownership decision. | GATE |
| C-2 | Do not implement `tools.py::cached_extract` unless a prior authorized change supplies a typed bound-slot callable to that tool; current state-only Python-tool execution cannot do so. | GATE |
| C-3 | Do not silently widen this FR into a map/compiler cache feature, generic tool middleware, manifest-composition system, or new execution engine. | GATE |
| C-4 | Cache entries must be written per successful item and atomically; post-map batch persistence does not satisfy interrupted-run recovery. | GATE |
| C-5 | Cache hits must be scoped to frozen extractor, source/snapshot, schema, and item identities; `sha256(item_ref)` alone is insufficient. | GATE |
| C-6 | Cache corruption and I/O failures must be typed, diagnosed, and tested; no broad catch may turn operational failure into an unqualified miss. | GATE |
| C-7 | Any material graph or prompt change must use the graph-authoring route, and any enforcement-infrastructure change requires explicit human review. | GATE |

Authority granted: none; this rejected proposal may not enter enforcement.
