# Judgement: FR-1158 `cached_map` Node Type: Map With a Per-Item Persistent Memo

**Verdict:** REJECTED — Return to planning: the evidence supports an example/contrib memo, not a second framework map primitive, and the proposed identity and payload contracts permit incorrect reuse.

**Prior art:** FR-1116, FR-1120, FR-1073, FR-232 as cited in the FR. The judgement dismisses retrieval hits FR-958 and FR-959 (Claude CLI backends; they share only the nouns "node" and "cached").

**Reviewed against:** Committed artifacts at `5e0f50759b083d054abcaf5e29dd1c7553695eba`, limited to:

- `feature-requests/FR-1158-cached-map-node.md` (entire FR).
- `feature-requests/FR-1116-map-memo-file-corpus.md` (lines 1-220, 235-253 and cited alternatives).
- `feature-requests/FR-1120-census-map-memo.md` (lines 1-200, 250-270).
- `feature-requests/FR-1073-map-result-contract.md` (lines 1-190).
- `feature-requests/FR-232-race-node-type.md`.
- `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/map_contract.py`, `examples/shared/map_memo.py`.
- `yamlgraph/compile/node_compiler.py` (lines 1-230); `yamlgraph/models/state_builder.py` (lines 35-65, 230-285).
- `yamlgraph/models/guard_schema.py`, `capabilities/CAP-11-subgraph-map.yaml`, `pyproject.toml` (lines 1-190).
- `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, and repository instructions supplied from `.github/copilot-instructions.md` and `CLAUDE.md`.

This is a draft only. No author transcript, exploratory-agent report, uncommitted adapter changes, or uncited implementation files informed the verdict. The FR's claimed completed exploration is not evidence of its conclusions.

## What is sound

The strongest case for approval is real: example-local tools are excluded from the installed distribution (`pyproject.toml:173-175`), and the existing memo proves that persistence can avoid repeated work. Population-wide accounting and commit-before-enforce address an actual composition problem rather than merely shortening YAML. The existing account factory closes the token and commits the verdict before the join enforces it (`yamlgraph/compile/map_contract.py:177-223`), so inserting a store between them is feasible.

The separation of deterministic persistence from Send orchestration, explicit failure policy, fresh-process witness, and refusal to turn store corruption into a miss are worth preserving.

| Rubric criterion | Assessment |
|---|---|
| 1. Scope | Not minimal on present evidence. FR lines 112-120 and 189-201 introduce a parallel compiler and broad DSL registration surface; the smaller packaging alternative is dismissed only for retaining wiring (lines 238-239). |
| 2. Consistency | Not satisfied. Once-per-lookup identity excludes effective defaults and does not define item-dependent variable resolution (lines 142-156). Replayed payloads have no specified index-removal boundary (lines 126-128, 164-170). |
| 3. Measurability | Main happy paths are measurable (lines 205-232), but missing negative witnesses leave binding store, signature, and configuration decisions unenforced. See R-5. |
| 4. Feasibility | Send/account/store/join is workable with current dependencies. Reusing the worker factory also needs an explicit result boundary: today's wrapper emits only collect/accounting updates (`map_compiler.py:129-216`). |
| 5. Architecture alignment | Side-effect isolation and factory reuse align. A second core node type is not justified by the cited consumers; effective execution context is already supplied separately from authored worker config (`node_compiler.py:66-82,171-185`). |
| 6. Single responsibility | One cohesive concern: persistent per-item reuse. No SPLIT is warranted merely because schema, lint, docs, and tests accompany it. |
| 7. Strategic classification | **Contrib/example**, not framework primitive. There are two named existing consumers and a new demonstration, not three independently evidenced use cases (FR lines 7-12). One existing consumer requires an explicitly excluded identity mode. |
| 8. Testability | Call-count and threshold tests can be written. Correct tests for resolved identity, duplicate items, replay representation, and invalid stores cannot be derived unambiguously from the current contract. |

This is not measurement tooling; the measurement-specific raw-sample gate does not apply.

## Required revisions

These are return-to-plan requirements, not conditional implementation authority.

### R-1: Reconcile the strategic classification and rejected precedent

Replace the framework-primitive justification with a consumer/contract table distinguishing actual workloads from the new demo. Classify the currently evidenced proposal as contrib/example. Do not count the demo as independent demand. A later request for core graduation must supply at least three concrete use cases and show why existing abstractions do not fit, as required by judge doctrine lines 51-56.

Explicitly disposition the earlier rejection of framework-owned memo in `FR-1116-map-memo-file-corpus.md:240-249` and its continued rejection in `FR-1120-census-map-memo.md:254-264`. Merely citing those FRs as implementation history does not disposition their conclusions.

In particular, FR-1120 requires discovery-time caller versions to skip both extraction and classification (`FR-1120-census-map-memo.md:132-190`). FR-1158 excludes that mode (lines 19-21), so the census is not an unchanged consumer of this contract. Do not authorize caller-version support or a census migration implicitly to repair this count.

Retain an evidence-backed alternatives record covering the existing four architectural classes. Distinguish the repository's exposed `CacheConfig` from claims about LangGraph cache backends generally; that model establishes only a TTL field (`guard_schema.py:12-22`). Preserve the `is_this_a_graph` disposition.

### R-2: Define identity from effective worker inputs

Replace D4's authored-config-only signature with an effective-computation contract. Include inherited execution settings that affect the worker, including provider/model and generation settings, rather than relying on authors to duplicate ordinary framework defaults in `memo.inputs`. The current compiler passes defaults separately to worker factories (`map_compiler.py:290-324`); changing those defaults need not change any field in D4.

Resolve worker variables in the same item-bound context used for execution. Define a shared base digest for common configuration/files and a per-item digest for the resolved non-injected variables. A variable such as `text: "{state.item.text}"` must not resolve against an absent or stale parent `item` during lookup. The compiler currently injects the item into each worker's variables (`map_compiler.py:261-265`).

Keep external state/code dependencies explicit in `memo.inputs`/`memo.files`; specify that changing undeclared external dependencies is outside the invalidation guarantee. Add witnesses for inherited model changes and two items with item-derived variables.

### R-3: Specify a typed, position-independent payload boundary

Define typed lookup-plan and memo-row models, including where the resolved store, signature, item snapshot, and current dispatch are carried from lookup to workers and store. D6's row shape omits the signature, while account clears `_map_open` before store executes (`map_contract.py:198-203`); the store must use the exact lookup plan and verdict token, not recompute inputs from later state.

Specify that persisted success payloads exclude wrapper-owned `_map_index`, and that replay assigns the current population index last. Otherwise D2's `{"_map_index": i, **payload}` permits an old index in the payload to overwrite `i`. The predecessor explicitly strips and then reassigns this field (`examples/shared/map_memo.py:313,409`).

Define JSON-native success payloads as the supported persistent domain and raise explicitly for unsupported output values before any write. Describe extraction, scalar wrapping, Pydantic conversion, and `flatten_output` consistently for execution and replay. Do not silently stringify outputs or broaden this FR into a general object serializer.

### R-4: Resolve duplicate identity and side-effect semantics

D3 permits repeated equal items, but D7 has one row per key and D6 says only "last upsert wins" (FR lines 132-170). Two equal misses may execute to different results; a later run would replay one result at both positions, contradicting AC-01.

For the bounded first version, reject duplicate canonical item keys before any Send or store write, naming both indices. Document that memo hits skip worker side effects and are appropriate only when the author accepts reuse of the prior successful value. This does not authorize changing ordinary map duplicate semantics.

### R-5: Make binding edge contracts acceptance-testable

Extend the ACs to cover the failure branches already promised in D3-D10: invalid JSON inputs/outputs, missing declared files, incompatible or malformed stores, write failure, tolerated failures, all-hit routing, and the population cap. Specify default values and path resolution for every `memo` field, not just `store`.

Reuse FR-1116's read-only lookup and transaction semantics: missing/zero-byte stores miss without creation; only writes create parents; a failed write rolls back and raises; stale writers may replace a row but must never create a false hit for another version/signature (`examples/shared/map_memo.py:185-206,343-375`; `FR-1116-map-memo-file-corpus.md:235`). No eviction, locks beyond SQLite transactions, or per-branch durability is requested.

The demo smoke currently names no provider or spend limit (FR lines 87-88,227-229). Record the human decision explicitly: **May this smoke incur provider spend, and what is its limit?** Until answered, require a deterministic provider-free call-count witness, not an implicitly funded live run.

## Scope is frozen

No implementation scope is granted by this rejected draft.

| Deliverable | Surface |
|---|---|
| Draft verdict | `tmp/draft-judgement-copilot-FR-1158-cached-map-node.md` only |
| Return-to-plan work | A revised committed proposal and its evidence; not performed by this judge |
| Candidate capability, not authorized | Persistent reuse with explicit identity, population accounting, and commit-before-enforce |

Not authorized: core `cached_map` registration or compiler changes; changing ordinary `map`; adding caller versions to satisfy the consumer count; migrating either existing consumer; changing the FR-1116 file format; failure caching; cache backends/TTL/eviction; enforcement-hook changes; live provider spend without a human decision.

## Revised acceptance criteria

These define the minimum contract for reconsideration, not an instruction to implement the rejected core design.

- [ ] AC-01: The committed proposal classifies its evidenced use cases correctly and explicitly dispositions the framework-memo rejections in FR-1116 and FR-1120; a core proposal supplies the doctrine's three-use-case justification.
- [ ] AC-02: Two separate provider-free processes using the same store and successful population produce equal ordered results; the second executes zero workers and reports `{reused: N, executed: 0}`.
- [ ] AC-03: Editing one item or one declared item file executes only that item; reordering existing items executes none and assigns current indices, with no persisted wrapper index.
- [ ] AC-04: Changing effective worker config, inherited model/generation settings, prompt bytes, a declared signature file, a shared resolved variable, or `memo.inputs` invalidates affected rows; item-derived variables resolve against each current item.
- [ ] AC-05: Duplicate canonical keys, invalid/non-finite JSON inputs, and invalid file declarations raise before workers or writes. Unsupported success payloads raise explicitly and cannot partially populate the transaction.
- [ ] AC-06: Both failed and tolerated items remain uncached and execute next time. Three reused successes plus one untolerated failure meet `min_success: 0.75`; typed failures/errors and verdict arithmetic follow FR-1073.
- [ ] AC-07: On unmet completeness, successful executed rows are committed before `MapCompletenessError`; prior-dispatch rows cannot be written as current work.
- [ ] AC-08: Empty populations meet completeness without touching even an existing invalid store. Nonempty all-hit populations route lookup directly to account, then store/join, with no Send; outgoing edges leave the join.
- [ ] AC-09: Missing/zero-byte stores are read-only misses; incompatible schemas, malformed selected rows, and SQLite read/write failures raise `MapMemoStoreError`. A failed transaction leaves no partial rows, and a stale writer produces a later miss rather than false reuse.
- [ ] AC-10: Strict config validation covers required fields, unknown memo fields, thresholds/failure keys, and unsupported guards/loop limits. Population overflow follows existing map cap precedence before execution; valid configurations lint successfully.
- [ ] AC-11: Existing map tests remain unchanged and passing; any eventual implementation passes requirement traceability, import boundaries, relevant lint/schema/codegen checks, and the named clean-environment suite.
- [ ] AC-12: Any authorized demo follows the graph-authoring route with an honest authoring report and call-count evidence. Documentation states defaults, path resolution, JSON limits, declared dependencies, side-effect skipping, duplicate policy, and durability limits; capability/requirement registration and a feature changelog fragment accompany implementation.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| GATE-1 | No code authority is granted. Do not treat folding individual revisions as approval; the strategic objection requires a new independent judgement of the committed plan. | GATE |
| GATE-2 | Reconcile the contrib/example classification and prior rejected framework scope before seeking core authority; do not invent consumers or enlarge identity modes to pass the count. | GATE |
| GATE-3 | Freeze effective identity, typed payload/plan transport, duplicate semantics, and negative witnesses in the proposal before implementation. | GATE |
| GATE-4 | Record the human spend decision before any provider-backed smoke; deterministic witnesses require no provider authorization. | GATE |
| GATE-5 | Any later authorized implementation must follow RED/GREEN, requirement traceability, graph-authoring rules, and FR implementation/status recording. | GATE |

Authority granted: none; this draft rejects the present core-node proposal and requests return to planning.
