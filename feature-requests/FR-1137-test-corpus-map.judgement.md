# Judgement: FR-1137 Test Corpus Map — per-test description, target, and type

**Verdict:** APPROVED WITH REVISIONS — the test-level corpus map is a justified contrib/example, but authority activates only after R-1 through R-6 are folded into the committed FR; the current plan defers mandatory raw-record evidence, leaves the >500-item map topology undefined, permits incomplete runs to look successful, and promises provenance the graph cannot currently write.

**Reviewed against:** `feature-requests/FR-1137-test-corpus-map.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/hooks/README.md`; `reference/patterns/corpus-map-reduce.md`; `reference/map-nodes.md`; `feature-requests/FR-851-requirement-witness-audit.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `examples/demos/corpus_census/graph.yaml`; `scripts/req_coverage.py`; `yamlgraph/config.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/utils/validators.py`; `yamlgraph/cli/__init__.py`; `yamlgraph/cli/graph_run_helpers.py`; `yamlgraph/utils/token_tracker.py`; committed Python test files under `tests/unit/` and `tests/integration/` at `edc1f173f8e27395139fa921dc25db21ec275899` (derived census only: 536 files, 6,890 top-level test functions).

## What is sound

| Criterion | Finding |
|---|---|
| Scope | The operator and first decision are concrete (`feature-requests/FR-1137-test-corpus-map.md:8-13`), and the proposed output answers the three stated inventory questions without becoming a maintained repository-wide index (`feature-requests/FR-1137-test-corpus-map.md:68-82,229-255`). |
| Consistency | AST-owned identity plus model-owned meaning and deterministic Markdown rendering are coherent boundaries (`feature-requests/FR-1137-test-corpus-map.md:42-57,114-150`). The incomplete-row success semantics are not coherent and are corrected by R-3. |
| Measurability | The extraction, reconciliation, chunking, rendering, canary, and full-run criteria are mostly reducible to direct assertions (`feature-requests/FR-1137-test-corpus-map.md:178-216`). AC-08 and AC-09 are insufficient as written and are replaced below. |
| Feasibility | The repository supports LLM and Python map sub-nodes (`reference/map-nodes.md:15-19,71-108`) and bounded concurrency defaults to eight (`yamlgraph/utils/validators.py:255-286`). The map item limit is a hard error, not an implicit batching facility (`yamlgraph/compile/map_compiler.py:333-369`), so the topology must be made explicit under R-2. |
| Architecture alignment | The plan reuses `extract_req_markers` rather than creating a second REQ source (`scripts/req_coverage.py:96-145`), uses typed model output, reconciles model IDs in code, and renders aggregates deterministically. A dedicated graph is justified because the existing census owns a one-finding-per-item envelope (`feature-requests/FR-1137-test-corpus-map.md:25-29,222-225`) while this use case needs multiple test records per bounded file/chunk. |
| Single responsibility | Discovery, classification, reconciliation, and rendering are stages of one test-inventory concern, not separable product capabilities (`feature-requests/FR-1137-test-corpus-map.md:35-57,103-150`). No split is required. |
| Strategic classification | **Contrib/example.** There is one named operator use case and an existing map-reduce abstraction with a demonstrated envelope gap (`feature-requests/FR-1137-test-corpus-map.md:8-13,25-29`). This does not authorize a new framework primitive. |
| Testability | Direct failing tests can be derived for extraction, partition coverage, schema rejection, reconciliation, rendering, and canary behavior. The revised criteria add missing witnesses for immutable freeze, deterministic markers, ceilings, zero failed rows, and provenance. |

The research record is sufficient for this round: it names the matching graph pattern, distinguishes FR-851 and FR-892, and dispositions six genuine alternatives (`feature-requests/FR-1137-test-corpus-map.md:16-33,81-90,218-227`). The cost estimate is also directionally consistent with the committed corpus, although the stated 563-file count is not the selected scope's current 536-file count and must be snapshot-stamped rather than presented as timeless fact.

## Required revisions

### R-1: Supply the raw-record evidence before authority

Move the substance of AC-09 into a committed **Raw Input Read** section in the FR before enforcement. Record at least ten manually read test functions from the pinned corpus SHA. For each, include `nodeid`, a source citation, provisional `description`/`target`/`test_type`, and one concrete surprising detail that could not come from a generated inventory. At least three samples must demonstrate a directory-versus-target or directory-versus-type mismatch. Keep a separate post-run raw-response read criterion; reconciled JSON rows are not raw model responses.

This is a pre-authority gate, not work deferred until after implementation: judge doctrine requires evidenced samples before authority (`.github/skills/judge-fr/doctrine.md:112-117`), and Scripture says to read the rawest artifact before measurement (`.github/copilot-instructions.md:109,124,210`). FR-851 shows the acceptable pre-implementation form as a pinned raw-input table with concrete observations (`feature-requests/FR-851-requirement-witness-audit.md:50-80`).

### R-2: Freeze one executable partition topology and all spend bounds

Replace “batch items if the partition exceeds `max_items`” with one unambiguous topology: one map payload per file or whole-test-function chunk; one LLM call per payload; a declared numeric `max_map_items` high enough for the pinned dry-run partition count; and preflight failure before the first LLM call when the limit is exceeded. Do not hide multiple files inside a payload or launch nested graph runs. Freeze numeric ceilings for source files, source bytes, estimated tokens per payload, primary partitions/LLM calls, concurrency, and wall-clock timeout, and record estimated and actual call counts.

The current text promises roughly 600 calls but leaves the >cap behavior undefined (`feature-requests/FR-1137-test-corpus-map.md:84-91,118-129`). The runtime raises when the list exceeds `max_items` (`yamlgraph/compile/map_compiler.py:353-369`), while the cited pattern requires all ceilings before spend (`reference/patterns/corpus-map-reduce.md:91-92,230-253`).

Add an explicit operator decision:

- **Q4 — model and spend policy:** either pin a named cheap provider/model at temperature 0 for reproducible classification, or retain environment-selected defaults and explicitly accept provider-dependent quality and price. In both cases, preserve explicit provider/model overrides and record effective provider, model, and temperature. Correct the cost text to distinguish the current shell's `PROVIDER=inception` from the no-environment default of Anthropic (`yamlgraph/utils/llm_factory.py:96-108`; `yamlgraph/config.py:62-80`).

### R-3: Make every semantic defect reject the exhaustive run

Retain demoted rows for diagnostics, but an accepted `test-map.json`/`.md` pair must have `failed_rows == 0`. Missing records, schema failures, invalid descriptions, unknown IDs, duplicate IDs, count mismatches, map failures, and canary failures must all reject the run before canonical artifacts are written. On rejection, emit only a clearly separate diagnostic log/report; do not publish success-shaped `test-map.*` files.

The present plan permits null descriptions and `other` classifications to satisfy count equality (`feature-requests/FR-1137-test-corpus-map.md:95-99,130-146,188-207`). That contradicts the cited contract, where map errors and missing IDs make incompleteness fatal (`reference/patterns/corpus-map-reduce.md:143-161`) and every payload must produce a typed result (`reference/patterns/corpus-map-reduce.md:203-228`).

Keep canary expected answers outside every model payload. Treat each target/type enum value as a semantic family, and run the canary before rendering. A failed canary must leave canonical artifacts absent, as required by the cited invariant (`reference/patterns/corpus-map-reduce.md:216-224`).

### R-4: Make freeze and provenance truthful without adding framework scope

Freeze the exact committed inputs, not merely a SHA next to working-tree reads: either read test blobs from the recorded commit or reject a dirty/mismatched worktree and record each file's path, SHA-256, and byte count. Preserve partition IDs, source nodeids, spans, input size, and stable ordering. The accepted JSON provenance must include run ID, commit SHA, corpus hash, artifact hash, provider, model, temperature, source-file/test/partition counts, estimated calls, actual calls, and reconciliation totals.

Remove `token_usage` from the in-graph JSON promise. The existing callback learns totals during invocation and the CLI prints them only after the graph returns (`yamlgraph/utils/token_tracker.py:35-87`; `yamlgraph/cli/graph_run_helpers.py:171-176,245-269`), so the renderer cannot truthfully embed them without an unauthorized runtime or wrapper change. Run the proof command with `--token-usage` and capture those observed totals in `demo-output.log`; do not add a framework change merely to post-process provenance.

### R-5: Close the extraction and classification contracts

Expand the extraction fixture to assert canonical path-qualified nodeids, source line, sync and async tests, class-qualified methods, inherited module/class/function markers, and REQ inversion through the imported extractor. State whether `req` is excluded from `markers` because it is already represented by `reqs`.

Define `target` as the single **primary exercised surface** and add a deterministic prompt tie-break order for tests spanning multiple surfaces. Define the exact one-sentence validator in the FR as a single-line, non-empty string with one terminal `.`, `!`, or `?` and no earlier terminal punctuation followed by non-whitespace; invalid raw text remains in the diagnostic row and rejects the run under R-3. Add mixed-target and abbreviation/path fixtures so the validator and taxonomy are executable rather than interpretive.

### R-6: Correct the authoring and committed-evidence contracts

Replace AC-01's requirement to commit `tmp/draft-authoring-report.md` with the actual contract: it must exist, be non-empty, contain the five required headings, list the governed artifacts, and be inspected before commit, but it remains transient. The repository explicitly ignores `tmp/` and states that this report is absent in CI (`.github/skills/graph-authoring/doctrine.md:61-75`; `.github/hooks/README.md:115-118`).

Name the currently unspecified “allowlisted proof” from D2 as `examples/demos/test_map/proof.json`. It must be a compact committed proof, not the full map: frozen provenance, all invariant results, reconciliation totals, and references to the ten post-run raw-response observations. Keep full `test-map.json`, `test-map.md`, and raw responses under `tmp/test-map/`.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-1137-test-corpus-map.md`, including the pre-authority raw-input table, Q4 decision, numeric ceilings, and implementation record |
| D-2 | `examples/demos/test_map/graph.yaml` and `examples/demos/test_map/prompts/*.yaml`, authored only through `scripts/author.sh` |
| D-3 | Demo-local deterministic Python tools for freeze, extraction, partitioning, reconciliation, canary validation, and rendering |
| D-4 | Demo-local README, canary/extraction fixtures, and bounded smoke fixture |
| D-5 | Unit tests covering the revised acceptance criteria, each carrying the allocated REQ marker |
| D-6 | Runtime artifacts under `tmp/test-map/`: canonical JSON/Markdown and raw map responses only for an accepted run; diagnostic output only for a rejected run |
| D-7 | `examples/demos/test_map/demo-output.log` and compact `examples/demos/test_map/proof.json` from one real full-scope run |
| D-8 | One new CAP/REQ allocation, generated architecture wiring, one changelog fragment, and one diary entry with a **Seed:** |

Not authorized: changes to YAMLGraph map/runtime/CLI/token-tracking behavior; changes to `examples/demos/corpus_census`; generic multi-record census support; CI or hook changes; inclusion of `.github/hooks/tests`; committing the full generated test map or raw model-response corpus; scheduled regeneration; migration of other census graphs; witness-quality scoring; multi-label targets; or any additional provider abstraction.

## Revised acceptance criteria

- [ ] AC-01: The committed FR contains the R-1 raw-input table at a named SHA with at least ten source-cited observations, including at least three directory-versus-classification mismatches, and records the resolved Q4 model/spend decision plus all numeric ceilings from R-2.
- [ ] AC-02: `examples/demos/test_map/graph.yaml` and its prompts are authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` is present and substantive but uncommitted; graph lint and the narrow smoke are recorded honestly.
- [ ] AC-03: Freeze/extraction tests prove immutable-input handling, per-file path/SHA-256/bytes, path-qualified nodeid, line, sync/async and class test discovery, module/class/function marker inheritance, the declared `req`-marker policy, and equality with imported `req_coverage.extract_req_markers`.
- [ ] AC-04: Partition tests prove splits occur only between whole test functions, every payload carries the import block and collector-owned partition metadata, every nodeid belongs to exactly one payload, ordering is stable, and every configured source/byte/token/partition/call limit rejects before the first LLM call.
- [ ] AC-05: The map makes exactly one structured-output LLM call per file/chunk payload at the frozen concurrency and timeout. The schema requires `nodeid`, one-sentence `description`, enum-constrained `target`, and enum-constrained `test_type`; effective provider/model/temperature follow the recorded Q4 policy.
- [ ] AC-06: Reconciliation tests cover missing, unknown, duplicate, out-of-enum, malformed-description, wrong-partition, and map-error results. Every case produces diagnostic evidence and rejects acceptance; no failed row can appear in an accepted canonical map.
- [ ] AC-07: Classification tests cover every target and type, a multi-surface tie, a `tests/unit` subprocess/integration case, and the exact sentence-validation boundary, including abbreviations or dotted paths.
- [ ] AC-08: Markdown is rendered only from the accepted canonical JSON. Tests prove target-by-type counts equal JSON counts and every JSON nodeid appears exactly once in Markdown.
- [ ] AC-09: Withheld canary answers are never included in model input. A canary test covers every target family plus a unit-directory integration case; any mismatch rejects the run before `test-map.json` or `test-map.md` is written.
- [ ] AC-10: Accepted JSON provenance contains run ID, commit SHA, per-file hashes/bytes, corpus and artifact hashes, effective provider/model/temperature, source-file/test/partition counts, estimated and actual calls, reconciliation totals, and `failed_rows: 0`. Tests verify each field from deterministic inputs.
- [ ] AC-11: One real full-scope run at a pinned SHA succeeds with AST count == reconciled row count == unique nodeid count, every required invariant true, zero failed rows, and actual calls equal primary partitions. `demo-output.log` records the command, SHA, outcomes, and CLI `--token-usage` totals; `proof.json` records compact provenance and invariant results.
- [ ] AC-12: Before any aggregate table is quoted, at least ten raw model responses are read from `tmp/test-map/`; `proof.json` cites the corresponding nodeids and records one concrete observation per response, including at least three directory-versus-classification mismatches.
- [ ] AC-13: The full generated map and raw responses remain under `tmp/test-map/`; only `demo-output.log` and compact `proof.json` are committed as run evidence.
- [ ] AC-14: A new CAP and REQ are allocated at enforce time, every new test carries that REQ marker, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-15: The demo README documents scope, taxonomy, Q4 model policy, ceilings, rejection semantics, output locations, and the exact real-run command. A changelog fragment and diary entry with a **Seed:** are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not begin enforcement until R-1 through R-6 are folded into the committed FR and Q4 records the operator's model/spend decision. | GATE |
| C-2 | All governed graph and prompt writes must come through `scripts/author.sh`; the transient authoring report is evidence for the commit hook, not a committed deliverable. | GATE |
| C-3 | The collector must freeze and enforce all declared ceilings before the first LLM call; overflow fails rather than truncates or silently rebatches. | GATE |
| C-4 | No canonical artifact may be emitted unless every AST identity has exactly one valid semantic row, every count/hash reconciles, `failed_rows == 0`, and the withheld canary passes. | GATE |
| C-5 | Model-emitted IDs, counts, classifications, and prose remain claims; deterministic code owns identity, coverage, arithmetic, hashes, and rendering. | GATE |
| C-6 | Do not modify framework runtime, CLI, token tracking, `corpus_census`, CI, or hooks. If the demo cannot be completed without such a change, stop and file a separate FR. | GATE |
| C-7 | The full-scope proof must use real model calls and committed source at the recorded SHA; mocked output may cover unit tests but cannot satisfy AC-11 or AC-12. | GATE |
| C-8 | Do not commit the full map or raw responses; commit only the bounded proof and run log authorized by D-7. | GATE |

Authority granted: after the committed FR satisfies C-1, implement only the bounded `examples/demos/test_map` contrib/example and its directly required tests, proof, capability wiring, documentation, changelog fragment, and diary entry described above.

---

**Prior art:** `FR-1137-test-corpus-map.md` — the FR this judgement judges (self-match on nouns); prior art proper is dispositioned in the FR header. *(Addendum at promotion, not judge output.)*
